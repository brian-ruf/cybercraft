import asyncio
from loguru import logger
from jinja2 import Template, BaseLoader, TemplateNotFound, Environment

def initialize(backend):
    status = False

    if backend is not None:
        backend.render_page()
        logger.debug("Rendered page")
        app_instance = backend.app_instance
        backend.set_tab_title("Startup")
        
        backend.page_section_control(header=False, 
                                    footer=False, 
                                    status=False, 
                                    aside=False, 
                                    asideOpen=False, 
                                    statusOpen=False)

        styling = """
        html, body {
            overflow: hidden !important;
            background-color: #073b4c;
            color: #f8f9fa;
        }

        .container, .content-wrapper, .main {
            background-color: #073b4c;
            overflow: hidden !important;
            color: #f8f9fa;
        }

        #main {
            display: flex;
            padding: 0;
            overflow: hidden !important;
        }

        #main .content {
            width: 100%;
            height: 100%;
            max-width: none;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            overflow: hidden !important;
        }

        .content {
            position: relative;
            background-color: #073b4c;
            color: #f8f9fa;
            display: flex;
            flex-direction: column;  /* Stack children vertically */
            justify-content: center;
            align-items: center;
            height: 100%;
            width: 100%;
            text-align: center;  /* Center text content */
        }

        .content > * {
            margin: 10px 0;  /* Add vertical spacing between elements */
        }

        .splash_logo_container {
            perspective: 500px;
            width: 200px;
            height: 200px;
            background-color: #073b4c;
            overflow: hidden;
        }

        .splash_logo {
            width: 100%;
            height: 100%;
            position: relative;
            animation: spin 4s linear infinite;
            transform-style: preserve-3d;
            overflow: hidden;
        }

        @keyframes spin {
            from { transform: rotateY(0deg); }
            to { transform: rotateY(360deg); }
        }

        .splash_logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            overflow: hidden;
        }


        /* Style the button */
        #get-started {
            padding: 12px 24px;
            font-size: 1.1em;
            border: 2px solid #f8f9fa;
            background-color: transparent;
            color: #f8f9fa;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s ease;
        }

        #get-started:hover {
            background-color: #f8f9fa;
            color: #073b4c;
        }
        """
        backend.send_page_styling(styling)

        search_box = """
        DuckDuckGo Search Box

        <form action="https://duckduckgo.com/" method="get" class="search-form">
            <input type="text" name="q" placeholder="Search DuckDuckGo..." required>
            <button type="submit">Search</button>
        </form>
        """
        search_box = ""

        buttons = """
        <div id="buttons" style="text-align: center; width: 100%; margin: 20px 0;">
            <p>Create a New OSCAL project or open existing project.<br />
            Create or import OSCAL files from within an OSCAL project.</p>
            <button class="button-secondary" id="new">New Project</button>&nbsp;&nbsp;<button class="button-secondary" id="open">Open Project</button>
        </div>
        """

        html_content = f"""
        <div class="content">
            <div class="splash_logo_container">
            <div class="splash_logo">
                <img src="resource:/img/CC_Logo.svg" alt="Spinning Logo">
            </div>
            </div>
            <h1>CyberCraft</h1>
            <h3>OSCAL Made Easy!</h3>
            <p>Version {app_instance.appversion}</p>
            <button id="get-started">Get Started</button>
            <br /><br />
            {buttons}
            <br /><br /><br /><br />
            {search_box if (app_instance.debug and app_instance.internet_available) else ""}
        </div>
        """

        backend.send_html_fragment("main", html_content, "")
        status = True
    else:
        logger.error("Invalid app_instance or tab_objects: Unable to create OSCAL Support GUI tab.")
    return status

# =========================================================

def main_content(backend, main_content="", styling=""):
    # app_instance = backend.app_instance # Get the app instance
    template_fragment = backend.fetch_html_fragment("concept.html")
    
    # Create environment and add filter
    env = Environment(loader=BaseLoader())
    # env.filters['convert_date'] = function_name # Add filters here
    
    # Create template with environment
    # template = env.from_string(template_fragment)
    # html_content = template.render()
    # backend.send_html_fragment("main", html_content, styling)
    backend.send_html_fragment("main", template_fragment, styling)
    backend.queue_message({"type": "startAnimation"})
# =========================================================
async def handler(backend, command):
    status = False
    logger.debug(f"Command to {__name__}: {command}")

    try:
        if command["type"] == "click":
            match (command["tagName"]):
                case "button":
                    match (command["id"]):
                        case "get-started":
                            logger.info("Get Started button clicked")
                            backend.spinner(on=True)  # Show processing indicator
                            try:
                                # Call process_update directly
                                await process_update(backend, "get-started")
                                status = True
                            except Exception as e:
                                logger.error(f"Error processing get-started: {str(e)}")
                                backend.status_update(f"Error: {str(e)}", "error")
                            finally:
                                backend.spinner(on=False)
                        case "open":
                            logger.info("Open button clicked")
                            await process_update(backend, "open")
                        case "new":
                            logger.info("New button clicked")
                            await process_update(backend, "new")
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
            case "get-started":
                logger.debug("Get Started command")
                backend.render_page("concept_page.html")
                status = True
            case "open":
                logger.debug("Open command")
                backend.main_gui._open_project()
                status = True
            case "new":
                logger.debug("New command")
                backend.main_gui._new_project()
                status = True
            case _:
                logger.debug(f"Unknown command: {command}")

    except Exception as e:
        logger.error(f"Error during update process: {e}")
        backend.status_update(f"Error during update: {str(e)}", "error")

