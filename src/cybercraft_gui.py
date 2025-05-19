import os
import sys
import uuid
import asyncio 
from loguru import logger
from pathlib import Path

# PySide6 Imports
from PySide6 import QtCore
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineSettings
from PySide6.QtWebEngineWidgets import *
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap, QAction, QActionGroup, QKeySequence, QIcon
from PySide6.QtWidgets import QApplication,QMainWindow, QLabel, QFileDialog
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Signal
# PySide6 Enhancements
import qdarktheme._os_appearance
import qdarktheme._template
import qdarktheme
import qasync # enables asyncio event loop in PySide6

# Application-Specific Imports
from browsertabwidget import BrowserTabWidget
from downloadwidget import DownloadWidget
from findtoolbar import FindToolBar
from webengineview import WebEngineView
from common import lfs

# ====================================================
# The backend object is used to communicate between the python code and the web page.
# It is used to send messages, data, and HTML fragments to the web page.
# It is also used to receive messages and data from the web page.
from backend import Backend, load_resource 

# ====================================================
# Each tab must have a display and handler function
from tabs import project, startup, support
TAB_STARTUP = {
    "startup": {
        "initial-display": startup.initialize,
        "handler": startup.handler,
        "tab_title": "CyberCraft"
    },
    "support": {
        "initial-display": support.initialize,
        "handler": support.handler,
        "tab_title": "Support"
    },
    "project": {
        "initial-display": project.initialize,
        "handler": project.handler,
        "tab_title": "Project"
    }
}
# ====================================================
OSCAL_PROJECT_EXTENSION = ".oscal"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
main_windows = []

def create_main_window(app_instance = None):
    """Creates a MainWindow using all of the available screen resolution 
    up to 1280x1024, or as set by the configuration file."""
    main_win = MainWindow(app_instance)
    main_windows.append(main_win)
    available_geometry = main_win.screen().availableGeometry()
    logger.debug("Detected Screen Dimensions: " + str(available_geometry.width()) + "x" + str(available_geometry.height()))
    if app_instance is not None:
        logger.debug("Main window with app_instance")
    else:
        logger.debug("Main window without app_instance")
    use_width = 1280
    use_height = 1024
    if available_geometry.width() < use_width:
        use_width = available_geometry.width()

    if available_geometry.height() < use_height:
        use_height = available_geometry.height()

    main_win.resize(use_width, use_height)
    main_win.show()
    return main_win

def create_main_window_with_browser():
    logger.debug("create_main_with_browser")
    """Creates a MainWindow with a BrowserTabWidget."""
    main_win = create_main_window()
    return main_win.add_browser_tab()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MainWindow(QMainWindow):
    """Provides the parent window with initial widigits."""
    def __init__(self, app_instance = None):
        logger.debug("MainWindow Class Init")
        super().__init__()

        # Setup main Window
        self.setWindowTitle('CyberCraft - The OSCAL Desktop GUI')
        self.app_instance = app_instance
        # self.support_bridge = None
        
        pixmap = QPixmap()
        app_icon = load_resource(':/img/favicon.ico', expect_binary=True) 
        pixmap.loadFromData( app_icon )
        appIcon = QIcon(pixmap)
        self.setWindowIcon(appIcon)

        self._change_theme(self.app_instance.config["gui"]["theme"])

        self._tab_widget = BrowserTabWidget(create_main_window_with_browser)
        self._tab_widget.enabled_changed.connect(self._enabled_changed)
        self._tab_widget.download_requested.connect(self._download_requested)
        self.setCentralWidget(self._tab_widget)
        self.connect(self._tab_widget, QtCore.SIGNAL("url_changed(QUrl)"),
                     self.url_changed)

        # TODO Properties Window
        self._find_tool_bar = None
        self._actions = {}
        self._create_menu()

        self._zoom_label = QLabel()
        self.statusBar().addPermanentWidget(self._zoom_label)
        self._update_zoom_label()

        self._tabs = []
        self._current_web_view = None
        self._current_backend = None
        self._current_channel = None
        
    # ---------------------------------------------------
    def closeEvent(self, event):  # Fixed method name to camelCase
        logger.debug("Close Event")
        # Stop the listener thread
        if hasattr(self, 'listener'):
            logger.debug("Stopping listener thread")
            self.listener.running = False  # Signal the thread to stop
            self.listener.stop()
            if not self.listener.wait(1000):  # Wait up to 1 second
                logger.warning("Listener thread did not stop gracefully")
                self.listener.terminate()  # Force quit if necessary
                self.listener.wait()  # Wait for termination
        
        main_windows.remove(self)
        event.accept()

    # ---------------------------------------------------
    def _open_project(self):
        logger.debug("Open!")
        # file_filter = f"OSCAL Files (*.xml *.json *.yaml *{OSCAL_PROJECT_EXTENSION});; All Files (*.*)"
        file_filter = f"OSCAL Files (*{OSCAL_PROJECT_EXTENSION})"
        file = QFileDialog.getOpenFileName(
            parent=self,
            caption="Open OSCAL Project",
            # directory=os.getcwd(),
            dir=self.app_instance.config["location"]["content"]["data"],
            filter=file_filter
        )

        if file[0] != "":
            # Detect the file extension
            file_extension = os.path.splitext(file[0])[1].lower()
            file_name = os.path.basename(file[0])
            file_name_no_ext = os.path.splitext(file_name)[0]
            file_path = os.path.dirname(file[0])
            if file_extension == OSCAL_PROJECT_EXTENSION:
                logger.debug("Project File")
            elif file_extension in [".xml", ".json", ".yaml"]:
                logger.debug("OSCAL File")
            
            self.show_new_tab("project", project_file=file[0], action="open")

    # ---------------------------------------------------
    def _new_project(self):
        """Opens a Save File dialog for creating a new OSCAL project file."""
        logger.debug("Creating new project")
        
        # Set up the file filter to only allow the OSCAL Project extension
        file_filter = f"OSCAL Project Files (*{OSCAL_PROJECT_EXTENSION});; All Files (*.*)"
        
        # Create a QFileDialog instance
        dialog = QFileDialog(self, "Create New OSCAL Project", self.app_instance.config["location"]["content"]["data"], file_filter)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        
        # Customize the button text
        dialog.setLabelText(QFileDialog.Accept, "New")
        dialog.setLabelText(QFileDialog.Reject, "Cancel")
        
        # Show the dialog and get the selected file
        if dialog.exec() == QFileDialog.Accepted:
            file_path = dialog.selectedFiles()[0]
            
            # Ensure the file has the OSCAL project extension
            if not file_path.lower().endswith(OSCAL_PROJECT_EXTENSION):
                file_path += OSCAL_PROJECT_EXTENSION
                
            # Open the project tab
            logger.debug(f"New project file created: {file_path}")
            self.show_new_tab("project", project_file=file_path, action="new")
                
    # ---------------------------------------------------
    def _save_project():
        logger.debug("Save Project")

    # ---------------------------------------------------
    def menuactionExit(self):
        logger.debug("Exit!")
        sys.exit()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # --- VIEW PAGE SOURCE
    def _view_page_source(self):
        """Opens a window and displays the HTML source of the current tab."""
        current_tab = self._tab_widget.currentWidget()
        if current_tab:
            current_tab.page().toHtml(lambda html: self._show_source_window(html))

    # ---------------------------------------------------
    def _show_source_window(self, html):
        from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("Page Source")
        dialog.resize(800, 600)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(html)
        text_edit.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.show()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # --- CREATE MENU
    def _create_menu(self):
        logger.debug("create menu")

        self.menuBar().setProperty("class", "button")

        # --- FILE MENU ---
        file_menu = self.menuBar().addMenu("  &File  ")
        file_menu.setStyleSheet(":hover {background-color: #000000}")
        file_menu.setProperty("class", "button")

        new_icon = QIcon.fromTheme("document-new")
        new_action = QAction(new_icon, "&New Project",
                              self, shortcut="Ctrl+N", triggered=self._new_project)
        new_action.setProperty("class", "button")
        file_menu.addAction(new_action)

        open_icon = QIcon.fromTheme("document-open")
        open_action = QAction(open_icon, "&Open Project",
                              self, shortcut="Ctrl+O", triggered=self._open_project)
        open_action.setProperty("class", "button")
        file_menu.addAction(open_action)

        # TODO: Handle Recent Files

        close_icon = QIcon.fromTheme("close")
        close_action = QAction(close_icon, "&Close Project",
                              self, shortcut="Ctrl+W", triggered=self._close_current_project)
        close_action.setProperty("class", "button")
        close_action.setEnabled(False)
        file_menu.addAction(close_action)

        exit_icon = QIcon.fromTheme("application-exit")
        exit_action = QAction(exit_icon, "E&xit",
                              self, shortcut="Ctrl+X", triggered=self.menuactionExit)
        file_menu.addAction(exit_action)

        # --- PROJECT MENU ---
        project_menu = self.menuBar().addMenu("  &Project  ")
        project_menu.setStyleSheet(":hover {background-color: #000000}")
        project_menu.setProperty("class", "button")

        import_icon = QIcon.fromTheme("document-import")
        import_action = QAction(import_icon, "&Import OSCAL File",
                              self, shortcut="Ctrl+I", triggered=self._import_file)
        import_action.setProperty("class", "button")
        import_action.setEnabled(False)
        project_menu.addAction(import_action)


        new_icon = QIcon.fromTheme("document-new")
        new_action = QAction(new_icon, "&New OSCAL File",
                              self, shortcut="Ctrl+N", triggered=self._new_content)
        new_action.setProperty("class", "button")
        new_action.setEnabled(False)
        new_action.setVisible(False)
        project_menu.addAction(new_action)

        # ---  MENU ---
        reload_action = QAction(text="Reload", parent=self,
                                shortcut=QKeySequence(QKeySequence.Refresh),
                                triggered=self._tab_widget.reload)
        self._actions[QWebEnginePage.Reload] = reload_action

        # --- EDIT MENU ---
        edit_menu = self.menuBar().addMenu(" &Edit ")

        find_action = QAction("Find", self,
                              shortcut=QKeySequence(QKeySequence.Find),
                              triggered=self._show_find)
        edit_menu.addAction(find_action)

        edit_menu.addSeparator()
        undo_action = QAction("Undo", self,
                              shortcut=QKeySequence(QKeySequence.Undo),
                              triggered=self._tab_widget.undo)
        self._actions[QWebEnginePage.Undo] = undo_action
        undo_action.setEnabled(False)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self,
                              shortcut=QKeySequence(QKeySequence.Redo),
                              triggered=self._tab_widget.redo)
        self._actions[QWebEnginePage.Redo] = redo_action
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self,
                             shortcut=QKeySequence(QKeySequence.Cut),
                             triggered=self._tab_widget.cut)
        self._actions[QWebEnginePage.Cut] = cut_action
        cut_action.setEnabled(False)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self,
                              shortcut=QKeySequence(QKeySequence.Copy),
                              triggered=self._tab_widget.copy)
        self._actions[QWebEnginePage.Copy] = copy_action
        copy_action.setEnabled(False)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self,
                               shortcut=QKeySequence(QKeySequence.Paste),
                               triggered=self._tab_widget.paste)
        self._actions[QWebEnginePage.Paste] = paste_action
        paste_action.setEnabled(False)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        select_all_action = QAction("Select All", self,
                                    shortcut=QKeySequence(QKeySequence.SelectAll),
                                    triggered=self._tab_widget.select_all)
        self._actions[QWebEnginePage.SelectAll] = select_all_action
        select_all_action.setEnabled(False)
        edit_menu.addAction(select_all_action)

        # --- TOOLS MENU ---
        tools_menu = self.menuBar().addMenu(" &Tools ")

        validate_action = QAction("Validate", self,
                                  triggered=lambda: self.placeholder("Validate"))
        validate_action.setEnabled(False)
        tools_menu.addAction(validate_action)
        

        update_action = QAction("OSCAL Versions", self,
                                  triggered=lambda: self.show_new_tab("support"))
        tools_menu.addAction(update_action)

        settings_action = QAction("Settings", self,
                                  triggered=lambda: self.placeholder("Settings"))
        settings_action.setVisible(False)
        tools_menu.addAction(settings_action)

        # --- WINDOW MENU ---
        window_menu = self.menuBar().addMenu("&Window")

        window_menu.addSeparator()

        zoom_in_action = QAction(QIcon.fromTheme("zoom-in"),
                                 "Zoom In", self,
                                 shortcut=QKeySequence(QKeySequence.ZoomIn),
                                 triggered=self._zoom_in)
        window_menu.addAction(zoom_in_action)
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out"),
                                  "Zoom Out", self,
                                  shortcut=QKeySequence(QKeySequence.ZoomOut),
                                  triggered=self._zoom_out)
        window_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction(QIcon.fromTheme("zoom-original"),
                                    "Reset Zoom", self,
                                    shortcut="Ctrl+0",
                                    triggered=self._reset_zoom)
        window_menu.addAction(reset_zoom_action)

        # Create the Theme submenu
        theme_menu = window_menu.addMenu("Theme")

        # Create actions for each theme option
        # auto_theme_action = QAction("Auto", self)
        light_theme_action = QAction("Light", self)
        dark_theme_action = QAction("Dark", self)

        # Set shortcut for one of the actions (optional - you can choose which one should have it)
        # auto_theme_action.setShortcut("Ctrl+Shift+d")  # Keeping your existing shortcut

        # Make the actions checkable and add them to a group so only one can be selected
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        # for action in [auto_theme_action, light_theme_action, dark_theme_action]:
        for action in [light_theme_action, dark_theme_action]:
            action.setCheckable(True)
            theme_group.addAction(action)
            theme_menu.addAction(action)

        # Set default checked state (you can modify this based on your needs)
        if self.app_instance.config["gui"]["theme"] == "light":
            light_theme_action.setChecked(True)
        elif self.app_instance.config["gui"]["theme"] == "dark":
            dark_theme_action.setChecked(True)  
        else:
            # auto_theme_action.setChecked(True)
            pass

        # Connect actions to the theme change function
        # auto_theme_action.triggered.connect(lambda: self._change_theme("auto"))
        light_theme_action.triggered.connect(lambda: self._change_theme("light"))
        dark_theme_action.triggered.connect(lambda: self._change_theme("dark"))

        view_source_action = QAction("View Page Source", self,
                                shortcut="Ctrl+U",
                                triggered=self._view_page_source)
        window_menu.addAction(view_source_action)
        window_menu.addSeparator()

        # --- HELP MENU ---
        help_menu = self.menuBar().addMenu(" &Help ")
        help_action = QAction("Help", self,
                               shortcut=QKeySequence(QKeySequence.HelpContents),
                               triggered=self._help)
        help_menu.addAction(help_action)
        aboutCC_action = QAction("About Cybercraft", self,
                               triggered=self._aboutCC)
        help_menu.addAction(aboutCC_action)
        aboutQt_action = QAction("About Qt", self,
                               triggered=QApplication.instance().aboutQt) #  qApp.aboutQt)
        help_menu.addAction(aboutQt_action)


    # ---------------------------------------------------
    def _close_current_project(self):
        logger.debug("Close Current Project")
        pass
    # ---------------------------------------------------
    def _import_file(self):
        logger.debug("Import OSCAL File")
        pass

    # --------------------------------------------------------
    def _new_content(self):
        logger.debug("New OSCAL Content")
        pass
    # ---------------------------------------------------
    def show_new_tab(self, tab_module, project_file=None, action=""):
        """Creates a new tab, sets up the tab's back end, and runs the initial display function."""

        initial_display = TAB_STARTUP[tab_module].get("initial-display")

        tab_object = {
            "session_id": str(uuid.uuid4()),
            "main_gui": self,
            "initial_display": initial_display,
            "handler": TAB_STARTUP[tab_module].get("handler"),
            "tab_title": TAB_STARTUP[tab_module].get("tab_title"),
            "app_instance": self.app_instance,
            "tab_widget": self._tab_widget,
            "web_view": None,
            "backend": None,
            "channel": None,
            "project_file": project_file,
            "project": None,
            "action": action
        }

        logger.debug(f"Opening {tab_object.get('tab_title')} tab and running: {tab_object.get('initial_display').__name__} [Session ID: {tab_object.get('session_id')}]")

        # Get a new web view through the proper tab creation mechanism
        web_view = self._tab_widget.add_browser_tab()
        tab_object["web_view"] = web_view

        # Set up the web channel
        channel = QWebChannel()
        tab_object["channel"] = channel

        # Setup a dedicated Backend object for this tab
        backend = Backend(tab_object)
        tab_object["backend"] = backend

        # Create a dedicated web channel for this tab, and register the backend object
        channel.registerObject("backend", backend)
        logger.debug("Created web channel and registered backend object")

        # Important: Set the web channel before loading the HTML content
        # The web channel handles communication between the front-end HTML/JavaScript and the backend Python module
        page = web_view.page()
        page.setWebChannel(channel)
        logger.debug("Set web channel on page")

        self._tabs.append(tab_object)
        logger.debug("Added tab to list")

        # Schedule the asynchronous initial display function
        if asyncio.iscoroutinefunction(initial_display):
            asyncio.create_task(initial_display(backend))
        else:
            initial_display(backend)

        return web_view


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def _change_theme(self, theme):
        logger.debug(f"Change theme to {theme}")
        status = False
        stylesheet = load_resource(':/styles/ps6_styling.qss', expect_binary=False)

        if theme == "auto":
            qdarktheme.setup_theme(additional_qss=stylesheet)
            status = True
        elif theme == "light":
            qdarktheme.setup_theme("light", additional_qss=stylesheet)
            status = True
        elif theme == "dark":
            qdarktheme.setup_theme("dark", additional_qss=stylesheet)
            status = True

        if status:
            logger.debug(f"Theme set to {theme}")
            self.app_instance.config["gui"]["theme"] = theme

    # ---------------------------------------------------
    def placeholder(self, msg='--'):
        logger.debug("Placeholder: " + str(msg))
    
    # ---------------------------------------------------
    def _aboutCC(self):
        logger.debug("About CC Menu!")
        html = load_resource(':/templates/about.html')
        self._tab_widget.add_browser_tab().setHtml(html)
        pass

    # ---------------------------------------------------
    def _help(self):
        logger.debug("Help Menu!")
        pass
    
    # ---------------------------------------------------
    def add_browser_tab(self):
        """Override add_browser_tab to set up JS console logging"""
        web_view = self._tab_widget.add_browser_tab()

        # web_view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)
        # web_view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.CustomScrollbars, True)
        # web_view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        return web_view
    
    # ---------------------------------------------------
    def _close_current_tab(self):
        logger.debug("Close Browser Tab")
        if self._tab_widget.count() > 1:
            self._tab_widget.close_current_tab()
        else:
            self.close()

    # ---------------------------------------------------
    def load(self):
        logger.debug("Load")
        # url_string = self._addres_line_edit.text().strip()
        # if url_string:
        #     self.load_url_string(url_string)

    # ---------------------------------------------------
    def load_url_string(self, url_s):
        logger.debug("load url string: " + url_s)
        url = QUrl.fromUserInput(url_s)
        if (url.isValid()):
            self.load_url(url)

    # ---------------------------------------------------
    def load_url(self, url):
        logger.debug("Load URL: ")
        self._tab_widget.load(url)

    # ---------------------------------------------------
    def load_url_in_new_tab(self, url):
        logger.debug("Load URL in new table: " )
        self.add_browser_tab().load(url)

    # ---------------------------------------------------
    def url_changed(self, url):
        logger.debug("Tab changed: ")
        
        # self._addres_line_edit.setText(url.toString())

    # ---------------------------------------------------
    def _enabled_changed(self, web_action, enabled):
        logger.debug(f"Enabled Change: {web_action} -> {enabled}")
        action = self._actions.get(web_action)
        if action:
            action.setEnabled(enabled)
        else:
            logger.warning(f"Unhandled web action: {web_action}")

    # ---------------------------------------------------
    def _zoom_in(self):
        logger.debug("Zoom In")
        new_zoom = self._tab_widget.zoom_factor() * 1.5
        if (new_zoom <= WebEngineView.maximum_zoom_factor()):
            self._tab_widget.set_zoom_factor(new_zoom)
            self._update_zoom_label()

    # ---------------------------------------------------
    def _zoom_out(self):
        new_zoom = self._tab_widget.zoom_factor() / 1.5
        logger.debug("Zome Factor")
        if (new_zoom >= WebEngineView.minimum_zoom_factor()):
            self._tab_widget.set_zoom_factor(new_zoom)
            self._update_zoom_label()

    # ---------------------------------------------------
    def _reset_zoom(self):
        logger.debug("Reset Zoom")
        self._tab_widget.set_zoom_factor(1)
        self._update_zoom_label()

    # ---------------------------------------------------
    def _update_zoom_label(self):
        logger.debug("Update Zoom Label")
        percent = int(self._tab_widget.zoom_factor() * 100)
        self._zoom_label.setText(f"{percent}%")

    # ---------------------------------------------------
    def _download_requested(self, item):
        logger.debug("Download Requested: " + item)
        # Remove old downloads before opening a new one
        for old_download in self.statusBar().children():
            if (type(old_download).__name__ == 'DownloadWidget' and
                old_download.state() != QWebEngineDownloadRequest.DownloadInProgress):
                self.statusBar().removeWidget(old_download)
                del old_download


        item.accept()
        download_widget = DownloadWidget(item)
        download_widget.remove_requested.connect(self._remove_download_requested,
                                                 Qt.QueuedConnection)
        self.statusBar().addWidget(download_widget)

    # ---------------------------------------------------
    def _remove_download_requested(self):
        logger.debug("Remove Download Requested")
        download_widget = self.sender()
        self.statusBar().removeWidget(download_widget)
        del download_widget
    
    # ---------------------------------------------------
    def _show_find(self):
        logger.debug("Show Find")

        if self._find_tool_bar is None:
            self._find_tool_bar = FindToolBar()
            self._find_tool_bar.find.connect(self._tab_widget.find)
            self.addToolBar(Qt.BottomToolBarArea, self._find_tool_bar)
        else:
            self._find_tool_bar.show()
        self._find_tool_bar.focus_find()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
async def desktop_startup(app_instance):
    logger.debug("Starting GUI")
    app = QApplication(sys.argv)

    # Create and set the event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    QApplication.setFont(font)

    main_win = create_main_window(app_instance)
    
    if not app_instance.initial_file:
        logger.debug("No file or URL passed. Opening default.")
        main_win.show_new_tab("startup")
    # else:
    #     for url in filenames:
    #         main_win.load_url_in_new_tab(QUrl.fromUserInput(url))
    
    # Run the event loop until the application exits
    try:
        with loop:
            loop.run_forever()
            return 0  # Success exit code
    except Exception as e:
        logger.error(f"Error in event loop: {e}")
        return 1  # Error exit code

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == '__main__':
    print("Cybercraft GUI Module. Not intended to be run as a stand-alone file.")
