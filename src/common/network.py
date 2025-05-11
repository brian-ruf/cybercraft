import requests
from loguru import logger
from . import misc
import socket
import aiohttp
import asyncio


def check_internet_connection():
    try:
        # Try to connect to a reliable host
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

async def async_api_get(url, headers=None):
    """Asynchronous version of api_get"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API request failed with status {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error during API request: {str(e)}")
        return None
    
async def async_download_file(url, filename):
    """Asynchronous version of download_file"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Download failed with status {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return None

def api_get(endpoint, http_headers={"Content-type": "application/json"}, timeout_seconds=10):
    """
        Calls a REST API and returns the response. 
        endpoint: The full URL to the REST endpoint
        http_headers: optional headers to include in the request 
            If not provided, this funciton requests a JSON response.
        
    """
    rest_ret = None
    try:
        rest_ret = requests.get(endpoint, headers=http_headers, timeout=timeout_seconds)

    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP Error: {type(err).__name__}: {str(err)}\n--for GET {endpoint}")
    except requests.exceptions.Timeout:
        logger.error(f"TIMEOUT Error: Waited {str(timeout_seconds)}\n--for GET {endpoint} .")
    except requests.exceptions.TooManyRedirects:
        logger.error(f"Too many redirects. {type(err).__name__}: {str(err)}\n--for GET {endpoint}")
    except requests.exceptions.RequestException as err:
        logger.error(f"Unrecognized request error {type(err).__name__}: {str(err)}\n--for GET {endpoint}")
    except (Exception, BaseException) as err:
        logger.error(f"Unrecognized error {type(err).__name__}: {str(err)}\n--for GET {endpoint}")

    if not rest_ret.status_code == 200:
        logger.error(f"HTTP Error: {str(rest_ret.status_code)} {rest_ret.text}\n--for GET {endpoint}")

    logger.debug(f"GET {endpoint} returned {rest_ret.status_code}")

    return rest_ret

def download_file(url, filename):
    """
    Downloads a file from a URL and saves it to the specified filename.
    """
    ret_value = ""
    try:
        response = requests.get(url)
        ret_value = misc.normalize_content(response.content)
        # with open(filename, "wb") as file:
        #     file.write(response.content)
    except requests.exceptions.RequestException as err:
        logger.error(f"Error downloading file: {str(err)}")
    except (Exception, BaseException) as err:
        logger.error(f"Unrecognized error downloading file: {str(err)}")
        
    return ret_value
