from loguru import logger
from . import misc
from . import lfs
import requests
import socket
import os
import shutil
import urllib.request


GH_ROOT_API = "https://api.github.com"
GH_ROOT_RAW = "https://raw.githubusercontent.com"
GH_ROOT = "https://github.com"

jsonhead= {"Content-type": "application/json"}
GH_API_RELEASE_FIELD_NAME = "tag_name" # key in the returned GitHub JSON containing the OSCAL version in the form of a release tag
OSCAL_releases_json = "" # The JSON content returned from GitHub REST API call requesting the OSCAL releases published by NIST


GITHUB_API_TOKEN = "" # misc.handle_environment_variables('GITHUB_API_TOKEN')
if GITHUB_API_TOKEN != "":
    logger.debug("Found GitHub API Access token. Will use to authenticate API calls. (Rate limit 5,000/hr)")
    github_headers= {"Content-type": "application/json", "X-GitHub-Api-Version": "2022-11-28", "Authorization": "Bearer " + GITHUB_API_TOKEN}
else:
    logger.debug("No GitHub API Access token found. API calls will be anonymous (Rate limit 60/hr).")
    github_headers= {"Content-type": "application/json", "X-GitHub-Api-Version": "2022-11-28"}

GITHUB_API_ROOT = "https://api.github.com/"
GITHUB_RAW_ROOT = "https://raw.githubusercontent.com/"


DATA_SOURCE = misc.handle_environment_variables('DATA_SOURCE')
FILE_PATTERNS = [".xml", ".json", ".yaml"]
EXCLUDE_LIST = ["src/", "package.json", "-alpha", "-beta"]
CACHE_LOCATION = "./cache"



def get_file(url, refresh=False):
    if refresh:
        # download file
        pass
    else:
        # if in cache serve
        pass

def fetch_file(url, api_key=""):
    pass

def check_cache(url):
    pass




class smart_dl():
    def __init__(self):
        self.file_uri = ""
        pass


def GH_download_files(owner_repo, release, save_path, FILE_PATTERNS=["*"]):
    file_count = 0
    match_count = 0
    download_count = 0
    download_problems = 0
    download_skipped = 0
    file_ignored = 0

    url = GITHUB_API_ROOT + "repos/" + owner_repo + "/" + "git/trees/"+ release + "?recursive=true"
    logger.debug( "Fetching " + owner_repo + " " + release )
    status, ret = api_get(url, github_headers) # requests.get(url, headers=github_headers)
    if ret != "":
        files_ret = ret.json()
        if "tree" in files_ret:
            misc.processing("#")
            match_file_found = False
            for file in files_ret["tree"]:
                file_count +=1
                misc.processing("_")
                if file["path"][0] != ".":
                    # determine if the file matches any of the defined patterns
                    OK_to_fetch = False
                    for item in FILE_PATTERNS:
                        if file["path"].endswith(item):
                            OK_to_fetch = True
                            match_count += 1
                            break
                    if OK_to_fetch:
                        for item in EXCLUDE_LIST:
                            if item in file["path"]:
                                OK_to_fetch = False
                                break
                    if OK_to_fetch:
                        misc.processing("+")
                        temp_path = os.path.dirname(save_path + "/" + file["path"])
                        lfs.mkdir(temp_path)
                        if not match_file_found:
                            match_file_found = True
                        url = GITHUB_RAW_ROOT + owner_repo + "/" + release + "/" + file["path"]
                        save_to = save_path + "/" + file["path"] # .replace("/", "_")
                        download_status = download_file_and_save(url, save_to)
                        if download_status == -1:
                            download_problems +=1
                        elif download_status ==0:
                            download_skipped += 1
                        elif download_status ==1:
                            download_count += 1
                    else:
                        # misc.processing(".")
                        file_ignored += 1

        else:
            logger.debug("No files found for " + url, "ERROR")
    else:
        logger.debug("Unable to get list of files.", "WARNING")

    msg = str(file_count) + " Files Found --  " 
    msg = msg + str(file_ignored) + " Ignored -- " 
    msg = msg + str(download_count) + " Downloaded -- " 
    msg = msg + str(download_skipped) + " Skipped (already present)"
    if download_problems > 0:
        msg = msg +   " !! " + str(download_problems) + " Downloads Failed" 
    logger.info(msg)

    # return file_list           

def GH_get_files(owner_repo, FILE_PATTERNS, data_location):
    global GITHUB_API_ROOT, GITHUB_RAW_ROOT
    url = GITHUB_API_ROOT + "repos/" + owner_repo 
    logger.info("Getting list of releases from " + url)
    base_path = data_location + "/" + owner_repo.replace("/", "_")
    lfs.mkdirs(base_path)

    # Cycles through each published release and downloads any files matching the file pattern
    status, ret = api_get(url + "/releases", github_headers) 
    if ret != "":
        json_ret = ret.json()

        # For each published release, pull the files down 
        for entry in json_ret:
            logger.info("PROCESSING RELEASE: " + entry[GitHub_Release_Field_Name])
            release_path = base_path +  "/" + entry[GitHub_Release_Field_Name]
            lfs.mkdir(release_path)
            download_files(owner_repo, entry[GitHub_Release_Field_Name], release_path, FILE_PATTERNS)
    else:
        logger.warning("Retrieving list of releases returned (" + str(ret.status_code) + ") " + ret.text)

    status, ret = api_get(url, github_headers) # requests.get(url, headers=github_headers)
    if ret != "":
        json_ret = ret.json()
        if "default_branch" in json_ret:
            release_path = base_path +  "/" + json_ret["default_branch"]
            lfs.mkdirs(release_path)
            download_files(owner_repo, json_ret["default_branch"], release_path, FILE_PATTERNS)
        else:
            logger.warning("Could not determine default branch.")
 


# =============================================================================
#  --- API Call Functions ---
# =============================================================================

# Calls an API using the provided URL, traps errors and signals status
# If no header information is passed, this funciton requests a JSON response.
def api_get(url, api_call_headers={"Content-type": "application/json"}):
    status = False
    ret = ""
    try:
        ret = requests.get(url, headers=api_call_headers)
        if ret.status_code == 200:
            status = True
        else:
            logger.error("REST API error with GET " + url, "(" + str(ret.status_code) + ") " + ret.text)
    except requests.exceptions.HTTPError as err:
        logger.error("GET returned an HTTP error.", str(err))
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        logger.error("TIMEOUT: The server took too long to respond.")
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        logger.error("Bad URL or too many redirects.")
    except requests.exceptions.RequestException as err:
        # catastrophic error.
        logger.error("Unable to fetch from " + url, str(err))
    except (Exception, BaseException) as error:
        logger.error("Problem fetching from " + url, "(" + type(error).__name__ + ") " + str(error))


    return status, ret

# Downloads a file from a specified URL 
# Returns status and the file contents
def fetch_file(url):
    status = False
    ret_value = ""
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '}

    try:
        req = urllib.request.Request(url=url, headers=header)
        with urllib.request.urlopen(req) as response:
            ret_value = response.read()
        status = True
    except requests.exceptions.HTTPError as err:
        logger.error("The server returned an HTTP error.", str(err))
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        logger.error("TIMEOUT: The server took too long to respond.")
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        logger.error("Bad URL or too many redirects.")
    except requests.exceptions.RequestException as err:
        # catastrophic error.
        logger.error("Unable to fetch release information from the NIST OSCAL Repository.", str(err))
    except (Exception, BaseException) as error:
        logger.error("Problem downloading " + url, "(" + type(error).__name__ + ") " + str(error))

    if status:
        status = len(ret_value) > 0
        logger.error("TYPE FROM GITHUB: " + str(type(ret_value)))
        ret_value = misc.normalize_content(ret_value)
        
    return status, ret_value



def download_file_and_save(url, dest_file, overwrite = False) -> int:
    """
    Downloads a file from a specified URL and saves it at a specified file location
    Returns:
      -1 if failed
      0 if skipped (already exists and overwrite set to False)
      1 if downloaded
    """
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) '}
    req = urllib.request.Request(url=url, headers=header)
    ret_value = -1
    timeout = 10 # seconds
    socket.setdefaulttimeout(timeout)

    if os.path.exists(dest_file) and not overwrite:
        logger.debug(dest_file + " exists. Skipping.")
        ret_value = 0
        pass
    else:
        # Create an http response object
        with urllib.request.urlopen(req) as response:
            # Create a file object
            with open(dest_file, "wb") as f:
                # Save file as binary
                shutil.copyfileobj(response, f)
                logger.debug(dest_file + " downloaded.")
                ret_value = 1

    return ret_value




# =============================================================================
if __name__ == '__main__':

    print("Not intended to be run as a stand-alone script. ")
    print("This is a library of network functions.")
