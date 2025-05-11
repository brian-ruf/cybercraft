from loguru import logger
from jinja2 import Template, BaseLoader, TemplateNotFound, Environment
import asyncio

from oscal_project_class import *


TAB_TITLE = "Project"
TEMPLATE = "primary.html"
PAGE_TITLE = "<h1>New Project</h1>"
MAIN_HTML_FRAGMENT = "project.html"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
async def initialize(backend):
    """
    This function sets up the initial content in the tab.
    """
    status = False
    if backend is not None:

        backend.render_page(TEMPLATE)
        logger.debug("Rendered page")
        app_instance = backend.app_instance
        support = app_instance.support
        # action = backend.action

        backend.page_section_control(header=True, 
                                    footer=False, 
                                    status=False, 
                                    aside=False, 
                                    asideOpen=False, 
                                    statusOpen=False)

        # Setup the support tab and page
        backend.set_tab_title(TAB_TITLE)
        header_content = PAGE_TITLE + " " + backend.action
        backend.send_html_fragment("header", PAGE_TITLE, "")
        styling = backend.load_resource(":/styles/project.css")
        backend.send_page_styling(styling)

        if backend.action == "new":
            backend.project = await OSCAL_project.create(backend.project_file)
        else:
            backend.project = await OSCAL_project.load(backend.project_file)
        if backend.project is not None:
            main_content(backend)
            status = True
        else:
            logger.error("Failed to load project file.")
            backend.status_update("Failed to load project file.", "error")
            status = False

        # 2. Edit title
        # 3. Add component definitions
        # 4. Make entire OSCAL model block clickable
        # 5. change "Controls" to "Catalogs and Baselines"

    else:
        logger.error("Invalid backend object: Unable to setup tab.")
    return status

# =========================================================
def main_content(backend, main_content="", styling=""):
    # app_instance = backend.app_instance # Get the app instance
    template_fragment = backend.fetch_html_fragment(MAIN_HTML_FRAGMENT)
    
    # Create environment and add filter
    env = Environment(loader=BaseLoader())
    # env.filters['convert_date'] = function_name # Add filters here
    
    # Create template with environment
    template = env.from_string(template_fragment)
    html_content = template.render()

    backend.send_html_fragment("main", html_content, styling)
    backend.queue_message({"type": "startAnimation"})
# =========================================================
async def handler(backend, command):
    """Receives messages forwarded from the backend and processes them."""
    status = False
    logger.debug(f"Command to {__name__}: {command}")

    try:
        if command["type"] == "click":
            match (command["tagName"]):
                case "button":
                    match (command["id"]):
                        case "button-id":
                            logger.info(f"{command["id"]} button clicked")
                            backend.spinner(on=True)  # Show processing indicator
                            try:
                                # Call process_update directly
                                await process_update(backend, "command")
                                status = True
                            except Exception as e:
                                logger.error(f"Error processing {command["id"]}: {str(e)}")
                                backend.status_update(f"Error: {str(e)}", "error")
                            finally:
                                backend.spinner(on=False)
                        case "open":
                            logger.info("Open button clicked")
                            await process_update(backend, "open")

                        case _:
                            logger.debug(f"Ignoring button {command['id']}")
                            status = True
                case _:
                    logger.debug(f"Ignoring click event for {command['tagName']}")
                    status = True
        else:
            logger.debug(f"Ignoring command type: {command['type']}")
            status = True
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        backend.status_update(f"Error: {str(e)}", "error")
        
    return status
# =========================================================
async def process_update(backend, command):
    """Handles any backend processes asynchronously while keeping UI responsive"""

    try:
        match command:
            case "command":
                logger.debug("Get Started command")
                # backend.render_page("concept_page.html")
            case _:
                logger.debug(f"Unknown command: {command}")

    except Exception as e:
        logger.error(f"Error during update process: {e}")
        backend.status_update(f"Error during update: {str(e)}", "error")

