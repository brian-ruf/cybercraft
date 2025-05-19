# Local File System (LFS) Functions
# File and folder-level interactions
import os
import errno
import sys
import json
from . import misc
# import uuid
from loguru import logger
from pathlib import Path
from datetime import datetime



# =============================================================================
#  --- PyInstaller Interactions  ---
# =============================================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
# =============================================================================
#  --- LFS File Level Interactions ---
# =============================================================================

def putfile(file_name, content):
    """
    Saves content to a file.
    Returns True if successful. 
    Returns False otherwise.
    """
    logger.debug(f"Saving {file_name}")
    status = False
    try:
        with open(file_name, mode='w') as file:
            file.write(content)
            file.close()
        status = True
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} saving {file_name}: {str(error)}")

    return status

# -----------------------------------------------------------------------------
def chkfile(path) -> bool:
    """
    Checks for the existence of a file.
    Returns:
    True if found
    False if not found or an error occurs
    """
    status = False
    try:
        if os.path.isfile(path):
            logger.debug(f"Found {path}")
            status = True
    except OSError as exc:
        if exc.errno == errno.EACCES:
            logger.error(f"Permission denied checking {path}")
        else:
            logger.error(f"Unhandled OS error {str(exc)}")
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} while checking {path}: {str(error)}")

    return status

# -----------------------------------------------------------------------------
def getfile(file_name, normalize = True, mode="rb") -> str:
    """
    Opens a file and returns the contents. Handles errors gracefully.
    If no optional parameters are passed, this will open the file as binary
    and convert the content to string.
    - file_name (str): the file to open.
    - normalize (bool): 
       - If True, always convert the contents to string. 
       - if False, will return the binary contents.
    - mode: indicates the file mode to use when opening

    Returns:
    If the file is not found, or an error occurs, an empty string is returned.
    Otherwise, the file content is returned in accordance with the "normalize"
    boolean parameter above.
    """
    logger.debug(f"Getting {file_name}")
    status = False
    ret_value = ""
    if chkfile(file_name):
        try:
            file = open(file_name, mode)
            ret_value = file.read()
            if normalize:
                ret_value = misc.normalize_content(ret_value)
            status = True
            file.close()
        except OSError:
            logger.error(f"Could not open/read {file_name}")
        except Exception:
            logger.error(f"Unrecognized error while getting {file_name}")
    else:
        logger.debug(f"Unable to find {file_name}")
    
    if status:
        logger.debug(f"Success getting {file_name}")
    else:
        ret_value = ""

    return ret_value

# -----------------------------------------------------------------------------
def getjsonfile(file_name) -> dict:
    """
    Gets a JSON file from the local file system

    Returns a dict object
    
    Returns an empty dict object if the file does not exist or 
       an error occurs.
    """
    json_results = {}
    json_string = getfile(file_name)
    try:
        if json_string:
            json_results = json.loads(json_string)
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} error deserializing {file_name}: { str(error)}")
    return json_results

# -----------------------------------------------------------------------------
def backup_file(filename):
    """
    Creates a backup of the specified file by duplicating it in its current
       location and appending the date and time to the root file name.
       Example: 
          /appdata/config.json is copied to
          /appdata/config_2025-01-05--13-59-59.json
    """
    status = False
    if chkfile(filename):
        p = Path(filename)
        newname = f"{p.stem}_{misc.datetime_string()}{p.suffix}"
        logger.debug(f"Renaming [{filename}] to [{newname}]")
        p.rename(Path(p.parent, newname ))
        status = True
    else:
        logger.warning(f"File not found: {filename}")
    return status

# =============================================================================
#  --- LFS Folder Level Interactions ---
# =============================================================================

def get_app_location() -> str:
    """Returns the location of the application."""
    # This must be determined differently if running a pyinstaller executable
    #    as compared to running a Python script with the Python executable.
    # See discussion here:
    # https://stackoverflow.com/questions/404744/determining-application-path-in-a-python-exe-generated-by-pyinstaller
    application_path = ""
    # Detect if running within a PyInstaller created applcation
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable) # Need to use this for one-file EXE
        # application_path = sys._MEIPASS # Recommended, but does not work with one-file EXE
    else: # native Python script
        application_path = os.path.dirname(os.path.abspath(sys.argv[0]))

    # logger.debug(f"APP LOCATION {application_path}")
    return application_path

# -----------------------------------------------------------------------------
def chkdir(path, make_if_not_present = False) -> bool:
    """
    Checks for the existence of a folder.

    Returns:
    - True if the path already exists
    - True if the path didn't exist, but was created successfully
    - False otherwise
    """
    # logger.debug(f"Checking for {path}")
    status = False
    try:
        if  os.path.exists(path):
            status = True
            # logger.debug(f"Found {path}")
        else:
            # logger.debug(f"Not Found: {path}")
            if make_if_not_present:
                logger.debug(f"Making {path}")
                status = mkdir(path)
    except OSError as exc:
        if exc.errno == errno.EACCES:
            logger.error(f"Permission denied checking {path} ")
        else:
            logger.error(f"Unhandled OS error {str(exc)}")
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} while checking {path}: {str(error)}")

    # print ("Status: " + out.iif(status, "TRUE", "FALSE"))
    return status


# -----------------------------------------------------------------------------
def mkdir(path) -> bool:
    """
    Creates any folders needed to ensure the specified path exists.
    Returns:
    - True if the path already exists
    - True if the path didn't exist, but was created successfully
    - False otherwise
    """
    status = False
    if  chkdir(path):
        status = True
    else:
        logger.debug(f"Making {path}")    
        try:
            os.makedirs(path)
            status = True
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                # If the error is only because the folder already exists, we can ignore. 
                status = True
            else:
                if exc.errno == errno.EACCES:
                    logger.error(f"Permission denied for {path}")
                elif exc.errno == errno.ENOSPC:
                    logger.error(f"No space left for {path}")
                elif exc.errno == errno.EROFS:
                    logger.error(f"Read-only file system for {path}")
                else:
                    logger.error(f"Unhandled OS error {str(exc)}")
        except (Exception, BaseException) as error:
            logger.error(f"Error making folder {path} ({type(error).__name__}): {str(error)}")

    return status

# =============================================================================
#  --- MAIN: Only runs if the module is executed stand-alone. ---
# =============================================================================
if __name__ == '__main__':
    print("Local File System (LFS) Library. Not intended to be run as a stand-alone file.")
