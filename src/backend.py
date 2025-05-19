# support_gui.py
# import sys
# import os
from loguru import logger
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot, Signal, QFile, QIODevice, QUrl
from PySide6.QtWebEngineCore import (
    QWebEngineUrlSchemeHandler, 
    QWebEngineUrlRequestJob,
    QWebEngineSettings
    # QWebEngineUrlScheme,
    # QWebEngineProfile, 
    # QWebEnginePage
)
from PySide6 import QtCore
import qasync
import asyncio
import json
import urllib.parse
import base64
from ps6_customwebpage import CustomWebPage
from common import misc
from jinja2 import Template, BaseLoader, TemplateNotFound, Environment

import resources_rc

def load_template(template_name, session_id="", title="----", theme="light", debug=False):
    template = load_resource(f":/templates/{template_name}")
    styling_strings = [
        "<style id='layout-styles'>",
        load_resource(":/styles/layout.css"),
        "</style>",
        "<style id='theme-styles'>",
        load_resource(f":/styles/{theme}.css"),
        "</style>",
        "<style id='custom-styles'></style>",
    ]
    styling = "\n".join(styling_strings)
    
    # Update paths in template to use resource:// scheme
    # Look for both src=":/img/ and src='/img/ patterns
    template = template.replace('src=":/img/', 'src="resource:/img/')
    
    code_strings = [
        f"var session_id = '{session_id}';",
        f"var debug = {str(debug).lower()};",
        load_resource(":/js/qwebchannel.js"),
        load_resource(":/js/ps6_bridge.js"),
        load_resource(":/js/dom_management.js")
    ]
    bridge_code = "\n".join(code_strings)
    
    output = Template(template).render(title=title, bridge_code=bridge_code, styling=styling)
    return output

def load_resource(resource_path, expect_binary=False):
    """Load a resource file from the Qt resource system.
    If expect_binary is True, the file is read as binary data.
    If expect_binary is False, the file is read as text."""
    file = QFile(resource_path)
   
    if expect_binary:
        if not file.open(QIODevice.ReadOnly):
            raise Exception(f"Could not open template: {resource_path}")
        content = file.readAll().data() # .decode('utf-8')
    else:
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            logger.error(f"Could not open template: {resource_path}")
        content = file.readAll().data().decode('utf-8')
    file.close()
    
    # Create and return the Jinja template
    return content

class Backend(QObject):
    messageFromPython = Signal(str)
    bridgeReady = Signal()

    def __init__(self, tab_object):
        super().__init__()
        logger.debug("Backend initializing")
        self.session_id   = tab_object.get("session_id")
        self.main_gui     = tab_object.get("main_gui")
        self.handler      = tab_object.get("handler")
        # tab_object.get("tab_title")
        self.app_instance = tab_object.get("app_instance")
        self._tab_widget  = tab_object.get("tab_widget")
        self.web_view     = tab_object.get("web_view")
        # tab_object.get("backend")
        # tab_object.get("channel")
        self.project_file = tab_object.get("project_file")
        self.project      = tab_object.get("project")
        self.action       = tab_object.get("action")

        self._pending_messages = []
        self._bridge_ready = False
        self._js_ready = False
        self.current_task = None
        self.loop = asyncio.get_event_loop()
        
        # Set up the custom page for console messages
        class WebPage(CustomWebPage):
            def javaScriptConsoleMessage(self_, level, message, line, source):
                level_map = {0: "INFO", 1: "WARNING", 2: "ERROR"}
                log_level = level_map.get(level, "INFO")
                logger.debug(f"[{log_level}] line {line}: {message}")

        self.web_view.setPage(WebPage(self.web_view.page().profile(), self.web_view))
        
        # Configure web profile and resource handler setup
        profile = self.web_view.page().profile()
        configure_web_profile(profile)
        self.resource_handler = ResourceHandlerSingleton.get_instance()
        if not hasattr(profile, '_resource_handler_installed'):
            profile.installUrlSchemeHandler(b'resource', self.resource_handler)
            profile._resource_handler_installed = True

    def load_template(self, template_name, session_id, title="----", theme="light", debug=False):
        return load_template(template_name, session_id, title, theme, debug)
    
    def load_resource(self, resource_path, expect_binary=False):
        return load_resource(resource_path, expect_binary)

    def render_page(self, template_name = "primary.html"):
        page_title = "New"
        html_content = load_template(template_name, self.session_id, page_title, self.app_instance.config["gui"]["theme"])
        base_url = QUrl('resource:/')
        
        # Connect page load signal before setting HTML
        self.web_view.page().loadFinished.connect(self._on_page_load_finished)
        self.web_view.page().setHtml(html_content, base_url)

    def _on_page_load_finished(self, success):
        if success:
            logger.debug("Page loaded successfully")
            self._check_js_ready()
        else:
            logger.error("Page failed to load")

    def _check_js_ready(self):
        """Periodically check if JavaScript has signaled it's ready"""
        if not self._js_ready:
            QtCore.QTimer.singleShot(100, self._check_js_ready)

    @Slot()
    def notify_js_ready(self):
        """Slot called by JavaScript when it's fully initialized"""
        logger.debug("JavaScript notified ready")
        self._js_ready = True
        self._bridge_ready = True
        self.bridgeReady.emit()
        self._process_pending_messages()

    def _process_pending_messages(self):
        """Process any messages that were queued while waiting for bridge"""
        logger.debug(f"Processing {len(self._pending_messages)} pending messages")
        while self._pending_messages:
            message = self._pending_messages.pop(0)
            self.messageFromPython.emit(json.dumps(message))

    def queue_message(self, message):
        """Queue a message to be sent when the bridge is ready"""
        if self._bridge_ready:
            logger.debug(f"Bridge ready, sending message immediately")
            self.messageFromPython.emit(json.dumps(message))
        else:
            logger.debug(f"Bridge not ready, queueing message")
            self._pending_messages.append(message)
    
    def set_tab_title(self, title):
        index = self._tab_widget.indexOf(self.web_view)
        self._tab_widget.setTabText(index, title)
        logger.debug("Changing tab title")

    def fetch_html_fragment(self, template_name):
        return load_resource(f":/templates/{template_name}")

    def send_html_fragment(self, element_id, html_fragment="", styling=""):
        """Send an HTML fragment to the page
           The styling can only apply inline styles (properties like color, 
           background-color, etc.). It cannot apply:
            - CSS selectors (.content, .logo, etc.)
            - Media queries or keyframe animations (@keyframes spin)
            - Complex CSS rules with nested properties
        """
        message = {
            "type": "content",
            "targetId": element_id,
            "html": None,
            "styling": None
        }
        if html_fragment != "":
            message["html"]    = base64.b64encode(html_fragment.encode()).decode()
        if styling != "":    
            message["styling"] = base64.b64encode(      styling.encode()).decode()

        self.queue_message(message)

    def send_page_styling(self, styling):
        """Send page styling to the page"""
        message = {
            "type": "styling",
            "styling": base64.b64encode(styling.encode()).decode()
        }
        self.queue_message(message)

    def status_update(self, status_message, level="info"):
        """Send a status update to the page"""
        message = {
            "type": "status",
            "level": level,
            "content": status_message
        }
        self.queue_message(message)

    def snackbar(self, message, duration=0, level="info"):
        """Send a snackbar message to the page"""
        message = {
            "type": "snackbar",
            "duration": duration,
            "level": level,
            "content": message
        }
        self.queue_message(message)

    def spinner(self, on=False):
        """Turn the processing spinner on and off"""
        message = {
            "type": "spinning-start" if on else "spinning-stop"
        }
        self.queue_message(message)

    # ---------------------------------------------------------
    @Slot(str)
    def receive_from_js(self, message):
        """Slot to receive messages from JavaScript"""
        logger.debug(f"Backend received from JS: {message}")

        if self.handler is not None:
            try:
                logger.debug("Forwarding message")
                # Instead of creating a task directly, we'll use qasync to schedule it
                asyncio.ensure_future(self._handle_message(message))
            except Exception as e:
                logger.error(f"Error handling message: {str(e)}")
        else:
            logger.error("No handler available")

    # ---------------------------------------------------------
    def page_section_control(self, header=None, footer=None, status=None, aside=None, asideOpen=None, statusOpen=None):
        """Control the visibility of page sections"""
        message = {"type": "sections"}
        if header is not None:
            message["header"] = header
        if footer is not None:
            message["footer"] = footer
        if status is not None:
            message["status"] = status
        if aside is not None:
            message["aside"] = aside
        if asideOpen is not None:
            message["asideOpen"] = asideOpen
        if statusOpen is not None:
            message["statusOpen"] = statusOpen
        self.queue_message(message)
    # ---------------------------------------------------------
    async def _handle_message(self, message):
        """Async helper method to handle messages"""
        try:
            logger.debug("Handling message")
            if self.current_task and not self.current_task.done():
                logger.debug("Cancelling existing task")
                self.current_task.cancel()
                try:
                    await self.current_task
                except asyncio.CancelledError:
                    pass
            
            # Call the handler directly since we're already in a coroutine
            await self.handler(self, json.loads(message))
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
     
    # ---------------------------------------------------------
    def cancel_current_task(self):
        """Cancel the current task if it exists"""
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            return True
        return False


    @Slot(str)
    def process_data(self, data):
        """Slot that processes data and returns a result"""
        logger.debug(f"Backend processing data: {data}")
        result = f"Processed by Python: {data.upper()}"
        logger.debug(f"Backend returning: {result}")
        self.messageFromPython.emit("RECEIVED")
        return result

    dataUpdated = Signal(dict)
    statusChanged = Signal(str)
    
    @Slot(str, int, str)
    def handle_console_message(self, level, message, source_id):
        """Handle console messages from JavaScript"""
        level_map = {
            0: "INFO",
            1: "WARNING",
            2: "ERROR"
        }
        log_level = level_map.get(level, "INFO")
        logger.debug(f"Page Console ({source_id}): [{log_level}] {message}")

    def make_element(self, element_id, element_type, element_class=None, element_attributes={}, content="", img_src=None):
        """Create a new HTML element and return its ID"""
        html = ""
        if element_type == "button": 
            html += f"<button id='{element_id}'"
        elif element_type == "img":
            html += f"<img id='{element_id}'"
        else:
            html += f"<span id='{element_id}'"

        if element_class:
            html += f" class='{element_class}'"

        if element_attributes:
            for key, value in element_attributes:
                html += f" {key}='{value}'"
        
        if img_src:
            icon = ""

        html += f">{content}</" + element_type + ">"

        return html

def update_page_area(div_id, html_fragment):
    """Update the content of a div element on the page"""
    # js = f"document.getElementById('{div_id}').innerHTML = `{html_fragment}`;"
    # logger.debug(f"Updating page: {js}")
    # view.page().runJavaScript(js)
    message = misc.create_html_update_message(
        target_id="status-container",
        html_content='<div class="alert">Status: <b>Ready</b></div>'
        )
    
class QtResourceLoader(BaseLoader):
    def get_source(self, environment, template):
        # Template path should be in format :/templates/base.html
        path = f":/templates/{template}"
        qfile = QFile(path)
        
        if not qfile.exists():
            raise TemplateNotFound(template)
            
        if not qfile.open(QIODevice.ReadOnly | QIODevice.Text):
            raise TemplateNotFound(template)
            
        try:
            source = qfile.readAll().data().decode('utf-8')
            return source, path, lambda: True
        finally:
            qfile.close()

class ResourceHandlerSingleton:
    _instance = None
    _handler = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ResourceHandler()
        return cls._instance

class ResourceHandler(QWebEngineUrlSchemeHandler):
    def __init__(self):
        super().__init__()
        
    def requestStarted(self, request):
        try:
            url = request.requestUrl()
            # Get the path part of the URL (removing the scheme)
            path = url.path()
            # Convert to Qt resource path format
            resource_path = f":{path}"
            
            logger.debug(f"Resource requested: {url.toString()} -> {resource_path}")
            
            file = QFile(resource_path)
            if not file.open(QIODevice.ReadOnly):
                logger.error(f"Failed to open resource: {resource_path}")
                request.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
                return
                
            mime_type = self._get_mime_type(path)
            logger.debug(f"Serving {resource_path} as {mime_type}")
            
            buffer = QtCore.QBuffer(parent=request)
            buffer.setData(file.readAll())
            buffer.open(QtCore.QIODevice.ReadOnly)
            request.reply(mime_type.encode(), buffer)
            
        except Exception as e:
            logger.error(f"Error handling resource request: {str(e)}")
            request.fail(QWebEngineUrlRequestJob.Error.RequestFailed)

    def _get_mime_type(self, path):
        if path.endswith('.mp4'):
            return 'video/mp4'
        elif path.endswith('.svg'):
            return 'image/svg+xml'
        elif path.endswith('.png'):
            return 'image/png'
        elif path.endswith('.ico'):
            return 'image/x-icon'
        return 'application/octet-stream'

def configure_web_profile(profile):
    """Configure the web profile to enable media playback and local content"""
    
    # Enable media playback
    settings = profile.settings()
    
    # Enable playback without user gesture
    settings.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
    
    # Enable autoplay
    settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
    
    # Enable local storage
    settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
    
    # Enable WebGL
    settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
    
    # Allow local content access
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
    settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
    
    # Enable media features
    # settings.setAttribute(QWebEngineSettings.ShowScrollBars, False)
    settings.setAttribute(QWebEngineSettings.AllowWindowActivationFromJavaScript, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    
    return profile

def encode_json(data):
    return json.dumps(data)

# Set up Jinja environment with the custom loader
env = Environment(loader=QtResourceLoader())
