import sys
import io
import os
import zipfile
import asyncio
from PySide6.QtWebEngineCore import QWebEngineUrlScheme
from PySide6.QtCore import QFile, QIODevice
import qasync


# Register the scheme at module import time
scheme = QWebEngineUrlScheme(b'resource')
scheme.setFlags(QWebEngineUrlScheme.SecureScheme | 
               QWebEngineUrlScheme.LocalScheme |
               QWebEngineUrlScheme.LocalAccessAllowed)
QWebEngineUrlScheme.registerScheme(scheme)


import os
import json
from loguru import logger
from common import lfs
from common import misc
from common import network
import platform
import argparse
import cybercraft_gui
from oscal_support import OSCAL_support
from oscal_project_class import OSCAL_project

logger.remove()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# APPLICATION LOCATION
APP_LOCATION = lfs.get_app_location()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# LOGGING CONTROL
LOG_LEVEL = "INFO"
LOG_LOCATION = os.path.join(APP_LOCATION, "logs")
LOG_APP_FILE_FORMAT = "{time:YYYY-MM-DD--HH-mm-ss}_app.log"
LOG_SQL_FILE_FORMAT = "{time:YYYY-MM-DD--HH-mm-ss}_sql.log"
CONSOLE_FORMAT       = "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
LOG_APP_FORMAT       = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
LOG_APP_FORMAT_DEBUG = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>Line {line}</cyan> - <level>{message}</level>"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# APPLICATION DEFAULTS
APP_NAME = "CyberCraft"
APP_VERSION = "1.0.0--alpha"
APP_VERSION_DATE = "2025-05-15"
APP_DESCRIPTION = "A desktop application for viewing, validating and converting content expressed using the Open Security Controls Assessment Language (OSCAL)"
APP_FILE_ROOT = "cybercraft" # for files and folders (prefer no spaces)
APP_CONFIG_FILE = APP_FILE_ROOT + "_config.json"
OSCAL_SUPPORT_FILE = "support.oscal"
PORTABLE_MODE = True
# -- GUI DEFAULTS --
GUI_DEFAULT_WINDOW_WIDTH = 1280
GUI_DEFAULT_WINDOW_HEIGHT = 1024
GUI_DEFAULT_FULL_SCREEN = False
GUI_DEFAULT_THEME = "light"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def is_production():
    """Returns True if the application is running as a pyinstaller-created executable."""
    return getattr(sys, 'frozen', False)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class app_control:
    def __init__(self):
        self.status = True
        self.__production= is_production()
        self.debug = False
        self.portable_mode = PORTABLE_MODE
        self.appname = APP_NAME
        self.appversion = APP_VERSION
        self.approotname = APP_FILE_ROOT # for files and folders
        self.args = None
        self.cli_only = True
        self.project_file = "" 
        self.initial_file = "" 
        self.db = None
        self.internet_available = network.check_internet_connection()

        self.os = platform.system() # what OS are we running on? Expect ["Windows", "Linux", "Darwin" (Mac)]

        self.config = {}
        self.config["appname"] = APP_NAME
        self.config["appversion"] = APP_VERSION
        self.config["appversiondate"] = APP_VERSION_DATE
        # In portable mode, these are the folders, unless a loaded configuration overrides
        # When not in portable mode, these are re-assigned in startup based on the operating system
        self.config["location"] = {}
        self.config["location"]["application"] = {"data" : APP_LOCATION,                                                                 "label" : "Application Execution Location"}
        self.config["location"]["content"]     = {"data" : os.path.join(APP_LOCATION, "content"),                                        "label" : "OSCAL Content Default Location"}
        self.config["location"]["appdata"]     = {"data" : os.path.join(APP_LOCATION, "appdata"),                                        "label" : "Application Configuration Location"}
        self.config["location"]["logs"]        = {"data" : os.path.join(self.config["location"]["appdata"]["data"], "logs"),             "label" : "Log File Location"}
        self.config["location"]["cache"]       = {"data" : os.path.join(self.config["location"]["appdata"]["data"], "cache"),            "label" : "Temporary Cache Location"}
        self.config["location"]["support"]     = {"data" : os.path.join(APP_LOCATION, "support"),                                        "label" : "OSCAL Support Location"}
        self.config["location"]["supportfile"] = {"data" : os.path.join(self.config["location"]["support"]["data"], OSCAL_SUPPORT_FILE), "label" : "OSCAL Support Module"}
        self.config["location"]["config"]      = {"data" : os.path.join(self.config["location"]["appdata"]["data"], APP_CONFIG_FILE),    "label" : "Application Configuration File"}
        # logger.debug(f"Support file: {self.config["location"]["supportfile"]["data"]}")

        self.shared_locations = [] # Path to shared location
        self.config["user"] = {}
        self.config["user"]["id"]       = {"data" : misc.get_user_information(), "label" : "User's login ID"}
        # self.config["user"]["name"]     = {"data" : "", "label" : "User's Name"}
        # self.config["user"]["initials"] = {"data" : "", "label" : "User's Initials"}
        # self.config["user"]["email"]    = {"data" : "", "label" : "User's Email Address"}
        # self.config["user"]["org"]      = {"data" : "", "label" : "User's Oranization"}
        self.config["gui"] = {}
        self.config["gui"]["main"] = {}
        self.config["gui"]["main"]["width"] = GUI_DEFAULT_WINDOW_WIDTH
        self.config["gui"]["main"]["height"] = GUI_DEFAULT_WINDOW_HEIGHT
        self.config["gui"]["main"]["fullscreen"] = GUI_DEFAULT_FULL_SCREEN
        self.config["gui"]["theme"] = GUI_DEFAULT_THEME # "auto", "light", "dark" // TODO: "high-contrast"
        self.__backup_config_before_saving = False
        self.__save_config_on_exit = False
        self.support = None
        self.project = None
        
    # -------------------------------------------------------------------------
    @classmethod
    async def create(cls):
        self = cls()
        self.status = await self.startup()
        return self
    # -------------------------------------------------------------------------
    def __str__(self):
        label_width = 25
        data_width = 79-label_width

        str_out = ""
        str_out += "-------------------------------------------------------------------------------\n"
        str_out += f"-- {self.appname} (Version {self.appversion}) [Operating System: {self.os}]\n"
        if self.portable_mode:
            str_out += "-------------------------------------------------------------------------------\n"
            str_out += misc.iif(self.portable_mode, f"-- {'PORTABLE MODE':^73} --\n", "")
        str_out += "-------------------------------------------------------------------------------\n"
        str_out += f"{'LOCATION DETAILS':^{label_width}} | \n"
        for location in self.config["location"]:
            str_out += f"{misc.safeJSON(self.config["location"][location], ["label"])[:label_width] :<{label_width}} | {misc.safeJSON(self.config["location"][location], ["data"])}\n"
        str_out += "-------------------------------------------------------------------------------\n"
        str_out += f"{'USER DETAILS':^{label_width}} | \n"
        for user_detail in self.config["user"]:
            str_out += f"{self.config["user"][user_detail]["label"][:label_width] :<{label_width}} | {self.config["user"][user_detail]["data"]}\n"
        str_out += "-------------------------------------------------------------------------------\n"
        str_out += f"{'GUI DETAILS':^{label_width}} | \n"
        str_out += f"{'Application Theme'[:label_width] :<{label_width}} | {self.config["gui"]["theme"]}\n"

        return str_out
    # -------------------------------------------------------------------------
    def __del__(self):
        """
        Performs graceful cleanup activities.
        - Saves the config file
        """
        if self.__save_config_on_exit:
            self.__save_config()

    # =========================================================================
    async def startup(self):
        """
        Application startup tasks:
        - Handle command line arguments
        - Assign file and folder locations based on the OS
        - Ensure file and folder locations exist
        - Load the configuration file
        - Setup logging
        - Identify the "learned" OSCAL version(s)
        """
        status = False

        self.__startup_arguments() # Handle any passed command line arguments

        # If not in portable mode, assign folders based on the OS
        if not self.portable_mode: self.__assign_folders()

        # Once file and folder locaitons are assigned, ensure they exist
        status = await self.__setup_folders()

        # Once we know file and folder locations exist, we can load the configuration file
        if status:
            self.__load_config()
            self.__setup_loggers()

        # If the info argument (-i or --info) is passed, display the application information and exit
        if self.args.info:
            print(self.__str__())
            sys.exit(0)


        # If we got this far, we will want the config file to be saved on exit.
        # Even if this is the firt time running, and regardless of CLI or GUI mode.
        self.__save_config_on_exit = True

        self.support = await OSCAL_support.create(self.config["location"]["supportfile"]["data"])
        logger.debug(f"Support file: {self.config["location"]["supportfile"]["data"]}")


        # if the learn-new argument (-ln or --learn-new) is passed, learn the latest OSCAL version(s)
        if self.args.learn_oscal_latest:
            logger.info("Learning latest OSCAL version(s)")
            if await self.support.update("latest"):
                logger.info("latest OSCAL versions learned.")
                logger.info(f"Updated support module at {self.config["location"]["supportfile"]["data"]}")
            else:
                logger.error("Unable to learn all OSCAL versions.")
            sys.exit(0)

        # if the learn-all argument (-la or --learn-all) is passed, re-learn all OSCAL version(s)
        if self.args.learn_oscal_all:
            logger.info("Relearning all OSCAL version(s)")
            if await self.support.update("all"):
                logger.info("All OSCAL versions learned.")
                logger.info(f"Updated support module at {self.config["location"]["supportfile"]["data"]}")
            else:
                logger.error("Unable to learn all OSCAL versions.")
            sys.exit(0)

        # if the metaschema argument is passed, learn the specified OSCAL extension 
        if self.args.metaschema:
            status = False
            if self.args.metaschema != "":
                if lfs.chkfile(self.args.metaschema):
                    logger.info("Learning an OSCAL extension " + self.args.metaschema)
                    logger.warning("FUTURE CAPABILITY -- NOT YET IMPLEMENTED")
                else:
                    logger.error(f"Unable to find {self.args.metaschema}. Please check location and access rights.")
            else:
                logger.error("Must identify a metaschema file to learn.")

        # if a filename is passed, open the file
        # TODO: Detect if an native OSCAL file or a project file
        if self.args.filename is not None:
            logger.debug(f"Filename passed: {self.args.filename}")
            if lfs.chkfile(self.args.filename):
                self.initial_file = self.args.filename
                # Get the file extension
                _, extension = os.path.splitext(self.args.filename)
                
                # Convert to lowercase for case-insensitive comparison
                extension = extension.lower()
                
                # Check for specific extensions
                if extension in ['.oscal']:
                    self.project_file = self.args.filename
                    self.status = True
                elif extension in ['.json', '.xml', '.yaml', '.yml']:
                    self.initial_file = self.args.filename
                    logger.info(f"Valid OSCAL file detected with extension: {extension}")
                    self.status = True
                else:
                    logger.warning(f"Unsupported file extension: {extension}")
                    self.status = False
            else:
                logger.error(f"Unable to find {self.args.filename}. Please check location and access rights.")        
        # TEMPORARY EXIT POINT FOR DEBUGGING CLI APPLICATION TASKS  
        # sys.exit(0)

        return status
    
    # -------------------------------------------------------------------------
    def __startup_arguments(self):
       # Get Runtime Arguments and Parameters
        parser = argparse.ArgumentParser(
            prog=APP_NAME,
            description=APP_DESCRIPTION,
            epilog="CyberCraft is created by Ruf Risk (https://RufRisk.com) - (c) 2024 Ruf Risk, LLC")
        parser.add_argument("-v",  '--version',         dest="version",            help='Report the application vesion and exit.',                 action="version", version=f"{APP_NAME} {APP_VERSION} ({APP_VERSION_DATE})")
        parser.add_argument("-i",  '--info',            dest="info",               help='Reportsthe application configuration and exit.',          action="store_true")
        parser.add_argument("-ln", '--learn-new',       dest="learn_oscal_latest", help='Learn recently released OSCAL version(s) and exit.',      action="store_true")
        parser.add_argument("-la", '--learn-all',       dest="learn_oscal_all",    help='Re-learn all OSCAL versions and exit.',                   action="store_true")
        parser.add_argument("-lx", '--learn-extension', dest="metaschema",         help='Learn an OSCAL extension in metaschema format and exit.', type=str)
        parser.add_argument("-d",  '--debug',           dest="debug",              help='Run the applicaiton with debugging turned on.',           action="store_true")
        parser.add_argument("-p",  '--portable',        dest="portable",           help='Run the application in portable mode.',                   action="store_true")
        if not self.__production:
            parser.add_argument( '--production',        dest="production",         help='Set logging as if the application was in production.',    action="store_true")
        parser.add_argument("filename",       nargs='?',                           help='Load the OSCAL File or Project. May include path.',       default=None)
        self.args = parser.parse_args()

        if not self.__production:
            self.__production = self.args.production

        self.debug = self.args.debug
        self.portable_mode=self.args.portable
        if self.portable_mode:
            logger.debug("PORTABLE MODE: " + misc.iif(self.portable_mode, "YES", "NO"))

        # If an argument is passed that does not require the GUI, set the cli_only flag
        if self.args.info or self.args.learn_oscal_latest or self.args.learn_oscal_all or self.args.metaschema:
            self.cli_only = True
        else:
            self.cli_only = False

    # -------------------------------------------------------------------------
    # TODO: gracefully handle locations that "should" exist, but don't (ie %APPDATA% or ~)
    async def __setup_folders(self):
        """Ensure key folders exists"""
        status = False
        if lfs.chkdir(self.config["location"]["content"]["data"], make_if_not_present=True):
            if lfs.chkdir(self.config["location"]["appdata"]["data"], make_if_not_present=True):
                self.config["location"]["cache"]["data"]   = os.path.join(self.config["location"]["appdata"]["data"], "cache")
                if lfs.chkdir(self.config["location"]["cache"]["data"], make_if_not_present=True):
                    status = True
                else:
                    logger.error("Unable to find or create cache folder: " + self.config["location"]["cache"]["data"])
            else:
                logger.error("Unable to find or create appdata folder: " + self.config["location"]["appdata"]["data"])
        else:
            logger.error("Unable to find or create data folder: " + self.config["location"]["content"]["data"])

        logger.debug(f"Checking for support Folder: {self.config["location"]["support"]["data"]}")
        if lfs.chkdir(os.path.abspath(self.config["location"]["support"]["data"]), make_if_not_present=True):
            # self.support = oscal_support.OSCAL_support(self.config["location"]["supportfile"]["data"])
            logger.debug(f"Checkfing for support file: {self.config["location"]["supportfile"]["data"]}")
            if not lfs.chkfile(self.config["location"]["supportfile"]["data"]):
                logger.warning(f"{self.config["location"]["supportfile"]["data"]} not found.")
                resource_path = f":/support/support.zip"
                file = QFile(resource_path)
                if file.open(QIODevice.ReadOnly): 
                    logger.debug(f"Checking for support filein onboard datastore.")
                    binary_file = file.readAll().data()
                    zip_data = io.BytesIO(binary_file)

                    # Open the ZIP file
                    logger.debug(f"Found file. Uncompressing to {self.config["location"]["support"]["data"]}")
                    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
                        # Get the list of files in the ZIP
                        file_list = zip_ref.namelist()
                        
                        # Check if there's exactly one file
                        if len(file_list) != 1:
                            logger.warning(f"Expected exactly one file in the ZIP, but found {len(file_list)}")
                        
                        # Extract the single file
                        file_name = file_list[0]
                        extracted_path = os.path.join(self.config["location"]["support"]["data"], file_name)
                        
                        # Extract the file to the output folder
                        zip_ref.extract(file_name, self.config["location"]["support"]["data"])
                else:
                    logger.warning(f"{resource_path} not found. Will create support module.")


            logger.debug(f"Support file: {self.config["location"]["supportfile"]["data"]}")
            
        return status

    # -------------------------------------------------------------------------
    def __assign_folders(self):
        """
        Assigns folder locations based on what is standard for the detected operating system
        - Windows:
            - "content": "cybercraft" sub-folder in the user's "My Documents" folder
            - "appdata": "cybercraft" sub-folder in the user's %AppData% folder
        - OSX / Linux:
            - "content": "~/cybercraft" ("cybercraft" sub-folder in the user's $HOME (~) folder)
            - "appdata": "~/.cybercraft" (".cybercraft" sub-folder in the user's $HOME (~) folder)
        - Unrecognized:
            - "content": "content" sub-folder in the application's folder
            - "appdata": "appdata" sub-folder in the application's folder
        - Mobile devices (iOS, Android) to be addressed in the future.
         """
        match self.os:
            case "Windows":
                import ctypes.wintypes
                CSIDL_PERSONAL= 5       # My Documents
                SHGFP_TYPE_CURRENT= 0   # Want current, not default value
                buf= ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)

                self.config["location"]["content"]["data"] = os.path.join(buf.value, APP_FILE_ROOT)
                self.config["location"]["appdata"]["data"] = os.path.join(misc.handle_environment_variables("APPDATA"), APP_FILE_ROOT)
            case "Linux", "Darwin":
                self.config["location"]["content"]["data"] = os.path.join("~", APP_FILE_ROOT)
                self.config["location"]["appdata"]["data"] = os.path.join("~", f".{APP_FILE_ROOT}")
            case _:
                self.config["location"]["content"]["data"] = os.path.join(self.config["location"]["application"]["data"], "content")
                self.config["location"]["appdata"]["data"] = os.path.join(self.config["location"]["application"]["data"], "appdata")
        self.config["location"]["config"]["data"] = os.path.join(self.config["location"]["appdata"]["data"], APP_CONFIG_FILE)
        self.config["location"]["logs"]["data"] = os.path.join(self.config["location"]["appdata"]["data"], "logs")
        # logger.debug(f"Support file: {self.config["location"]["supportfile"]["data"]}")

    # -------------------------------------------------------------------------
    def __setup_loggers(self):
        """Configure logging for the application"""

        log_location = self.config["location"]["logs"]["data"]

        logger.remove()
        
        # Set format and level based on environment

        if self.__production or not self.debug:
            log_format = LOG_APP_FORMAT
            log_level = "INFO"
        else:
            log_format = LOG_APP_FORMAT_DEBUG
            log_level = "DEBUG"

        if self.cli_only or self.debug:
            # Log to console - only for debug or CLI
            logger.add(
                sys.stderr,
                format=CONSOLE_FORMAT,
                level=log_level,
                colorize=True
            )

        # Log to file - always
        logger.add(os.path.join(log_location, LOG_APP_FILE_FORMAT), format=log_format, level=log_level, rotation="5 MB", retention=4, enqueue=True)

        # logger.info(f"Log (Level: {log_level}) Locaiton: {log_location}")

    # =========================================================================
    def __load_config(self):
        """Loads the configuration file if found and uses it to over-ride defaults."""
        logger.debug(self.config["location"]["config"]["data"])

        if self.config["location"]["config"]["data"] == "": # no config file identified
            logger.debug("No configuration file identified.")
            temp = os.path.join(self.config["location"]["appdata"]["data"], APP_CONFIG_FILE)
            if lfs.chkfile(temp):
                self.config["location"]["config"]["data"] == temp

        
        if self.config["location"]["config"]["data"] != "":
            # logger.debug(f"Configuration file identified: {self.config["location"]["config"]["data"]}")
            config_json = lfs.getjsonfile(self.config["location"]["config"]["data"])
            if config_json:
                if config_json.get("appname", "") == self.appname:
                    logger.debug(f"configuration file loaded for {config_json["appname"]}")
                    logger.debug("App name matches")
                    if not config_json.get("appversion", "") == self.appversion:
                        self.__backup_config_before_saving = True
                        logger.debug("Config file from older application version detected.")
                    self.__apply_config(config_json)
                else:
                    logger.warning(f"Configuration file [{self.config["location"]["config"]["data"]}] does not appear correct for [{self.appname}].")
            else:
                logger.warning(f"{self.config["location"]["config"]["data"]} missing or empty. Using defaults. Will create on exit.")
        else:
            logger.warning(f"{self.config["location"]["config"]["data"]} not found. Using defaults. Will create on exit.")
    # -------------------------------------------------------------------------
    def __apply_config(self, json_config):
        if "location" in json_config:
            for location_key in json_config["location"]:
                self.config["location"][location_key] = json_config["location"][location_key]
        if "user" in json_config:
            for user_key in json_config["user"]:
                self.config["user"][user_key] = json_config["user"][user_key]
        if "gui" in json_config:
            for window_key in json_config["gui"]:
                self.config["gui"][window_key] = json_config["gui"][window_key]
                # logger.debug(f"Window Key: {window_key} = {self.config["gui"][window_key]}")
    # -------------------------------------------------------------------------
    def __config_json(self):
        json_out = {}
        json_out["appname"] = self.appname
        json_out["appversion"] = self.appversion

        json_out["saved"] = misc.datetime_string()
        json_out["location"] = self.config["location"]
        json_out["user"] = self.config["user"] 
        json_out["gui"] = self.config["gui"] 

        return json_out
    # -------------------------------------------------------------------------
    def __save_config(self):
        """Saves the application config file in JSON format."""
        if self.__backup_config_before_saving:
            lfs.backup_file(self.config["location"]["config"]["data"])
            self.__backup_config_before_saving = False
        temp = os.path.join(self.config["location"]["appdata"]["data"], APP_CONFIG_FILE)
        lfs.putfile(temp, json.dumps(self.__config_json(), indent=3))
        if lfs.chkfile(temp):
            self.config["location"]["config"]["data"] = temp
        else:
            logger.warning(f"Unable to save configuration [{temp}]")
    
async def main():
    app_instance = await app_control.create()
    try:
        if app_instance.status:
            exit_code = await cybercraft_gui.desktop_startup(app_instance)
            return exit_code
    except SystemExit:
        pass

    # added this to handle exceptions
    exit_code = await cybercraft_gui.desktop_startup(app_instance)
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

# if __name__ == '__main__':
#     exit_code  = 0

#     # Run the main function
#     sys.exit(asyncio.run(main()))
