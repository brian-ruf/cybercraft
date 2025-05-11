import asyncio
from loguru import logger
from jinja2 import Template, BaseLoader, TemplateNotFound, Environment
from common.network import check_internet_connection
from common.misc import convert_datetime_format

def initialize(backend):
    """
    This function will start the OSCAL support module and load the support database.
    It will also create the GUI tab for the OSCAL support module.
    """
    status = False
    if backend is not None:
        backend.render_page()
        logger.debug("Rendered page")

        app_instance = backend.app_instance
        support = app_instance.support

        # Setup the support tab and page
        backend.set_tab_title("Support")
        backend.page_section_control(header=True, 
                                    footer=False, 
                                    status=True, 
                                    aside=False, 
                                    asideOpen=False, 
                                    statusOpen=True)
        backend.send_html_fragment("header", "<h1>OSCAL Support</h1>", "")

        # if support.versions:
        #     logger.debug(f"versions {support.versions}")
            
        if app_instance.internet_available:
            logger.debug(f"Internet available")
        if app_instance.config["location"]["supportfile"]["data"]:
            logger.debug(f"Support file available")

        main_content(backend)

        status = True
    else:
        logger.error("Invalid backend object: Unable to create OSCAL Support GUI tab.")
    return status

# =========================================================

def main_content(backend, styling=""):
    app_instance = backend.app_instance
    support = app_instance.support

    styling = ""
    template_fragment = backend.fetch_html_fragment("support.html")
    
    # Create environment and add filter
    env = Environment(loader=BaseLoader())
    env.filters['convert_date'] = convert_datetime_format
    
    # Create template with environment
    template = env.from_string(template_fragment)
    html_content = template.render(
        versions=support.versions, 
        internet=app_instance.internet_available,
        support_file=app_instance.config["location"]["supportfile"]["data"]
        )

    backend.send_html_fragment("main", html_content, styling)

# =========================================================

async def handler(backend, command):
    status = False
    logger.debug(f"Command to {__name__}: {command}")

    match command["type"]:
        case "click":
            match (command["tagName"]):
                case "button":
                    match (command["id"]):
                        case "refresh-all":
                            logger.info("Refresh All or Initialize button clicked")
                            backend.spinner(on=True)
                            # Create task but don't await it
                            backend.current_task = asyncio.create_task(process_update(backend, "get-started"))
                            status = True
                        case "check-for-new":
                            logger.info("Check for New button clicked")
                            backend.spinner(on=True)
                            backend.current_task = asyncio.create_task(process_update(backend, "latest"))
                            status = True
                        case "check-internet":
                            logger.info("Check Internet button clicked")
                            status = True
                        case _:
                            if isinstance(command["id"], str) and command.get("id", "").startswith("refresh-"):
                                logger.info(f"Refresh button clicked for version {command['id']}")
                                backend.spinner(on=True)
                                version = command["id"].replace("refresh-", "")
                                backend.current_task = asyncio.create_task(process_update(backend, version))
                                status = True
                            else:
                                logger.debug(f"Ignoring button click (id='{command.get('id', '[none]')}'")
                                status = True
                case _:
                    logger.debug(f"Ignoring click event for {command['tagName']}")
                    status = True
        case _:
            logger.debug(f"Ignoring command type: {command['type']}")
            status = True

    return status

# =========================================================
async def process_update(backend, update_type):
    """Handles the update process asynchronously while keeping UI responsive"""
    try:
        support = backend.app_instance.support
        # Start the update process
        await support.update(update_type, backend)
        # Refresh the main content after update completes
        main_content(backend)
        backend.spinner(on=False)
        backend.snackbar("Update complete", 10, "success")
    except Exception as e:
        logger.error(f"Error during update process: {e}")
        backend.status_update(f"Error during update: {str(e)}", "error")
