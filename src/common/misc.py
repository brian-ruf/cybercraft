# =============================================================================
#  --- Common Functions ---
# =============================================================================
# Common Functions
#
import os
import re
from datetime import datetime, timezone
import pytz
from tzlocal import get_localzone
import json
import getpass as gt
from loguru import logger
from typing import Union, Dict, Any 

# def convert_datetime_format(date_str, include_time=True):
#     """
#     Converts various ISO 8601 datetime strings to a formatted date string.
#     Handles variations including:
#     - Decimal or whole number seconds
#     - 'Z' timezone or GMT offset
    
#     Args:
#         date_str (str): ISO 8601 formatted datetime string
        
#     Returns:
#         str: Date formatted as 'Month DD, YYYY'
#     """
#     try:
#         # First try exact format with milliseconds
#         dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
#     except ValueError:
#         try:
#             # Try without milliseconds
#             dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
#         except ValueError:
#             try:
#                 # Try with timezone offset (e.g., +00:00)
#                 if '+' in date_str:
#                     # Split at + and remove the timezone part
#                     date_part = date_str.split('+')[0]
#                     if '.' in date_part:
#                         dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S.%f")
#                     else:
#                         dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
#                 elif '-' in date_str[19:]:  # Look for minus only after the date part
#                     # Split at - and remove the timezone part
#                     date_part = date_str.split('-', 3)[0:3]  # Keep first 3 parts
#                     date_part = '-'.join(date_part)
#                     if '.' in date_part:
#                         dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S.%f")
#                     else:
#                         dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
#                 else:
#                     raise ValueError(f"Unhandled date format: {date_str}")
#             except ValueError as e:
#                 raise ValueError(f"Unable to parse date string: {date_str}. Error: {str(e)}")
    
#     # Convert to the desired format
#     return dt.strftime("%B %d, %Y  %I:%M:%S %p") if include_time else dt.strftime("%B %d, %Y")

def convert_datetime_format(date_input, include_time=True, assume_localtime=True):
    """
    Converts various datetime inputs to a formatted date string.
    Handles both datetime objects and ISO 8601 datetime strings including:
    - Decimal or whole number seconds
    - 'Z' timezone or GMT offset
    - Empty or invalid input strings
    
    Args:
        date_input (Union[str, datetime]): Datetime object or ISO 8601 formatted datetime string
        include_time (bool): Whether to include time in the output string
        assume_localtime (bool): If True, assumes local time for timezone-naive inputs.
                               If False, assumes UTC. Defaults to True.
        
    Returns:
        str: Date formatted as 'Month DD, YYYY' or 'Month DD, YYYY HH:MM:SS AM/PM'
             Returns empty string if input is invalid
    """
    # Handle datetime object input
    if isinstance(date_input, datetime):
        try:
            # If datetime has no timezone, set according to assume_localtime
            if date_input.tzinfo is None:
                if assume_localtime:
                    try:
                        local_tz = get_localzone()
                        dt = date_input.replace(tzinfo=local_tz)
                    except Exception as e:
                        logger.debug(f"Error setting local timezone: {str(e)}. Falling back to UTC.")
                        dt = date_input.replace(tzinfo=pytz.UTC)
                else:
                    dt = date_input.replace(tzinfo=pytz.UTC)
            else:
                dt = date_input
            
            # Convert to local timezone for display
            try:
                local_tz = get_localzone()
                dt = dt.astimezone(local_tz)
            except Exception as e:
                logger.debug(f"Error converting to local timezone: {str(e)}")
                # Continue with original timezone if local conversion fails
                
            return dt.strftime("%B %d, %Y %I:%M:%S %p") if include_time else dt.strftime("%B %d, %Y")
        except Exception as e:
            logger.debug(f"Error formatting datetime object: {str(e)}")
            return ""
    
    # Handle string input
    if not isinstance(date_input, str):
        logger.debug(f"Invalid input type: {type(date_input)}. Expected str or datetime.")
        return ""
        
    if not date_input.strip():
        logger.debug("Empty date string provided")
        return ""
    
    try:
        # First try exact format with milliseconds
        try:
            dt = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt.replace(tzinfo=pytz.UTC)  # Z explicitly means UTC
        except ValueError:
            # Try without milliseconds
            try:
                dt = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%SZ")
                dt = dt.replace(tzinfo=pytz.UTC)  # Z explicitly means UTC
            except ValueError:
                # Try with timezone offset (e.g., +00:00)
                if '+' in date_input:
                    # Split at + and remove the timezone part
                    try:
                        date_part = date_input.split('+')[0]
                        if '.' in date_part:
                            dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S.%f")
                        else:
                            dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
                        offset = date_input.split('+')[1]
                        dt = dt.replace(tzinfo=pytz.FixedOffset(int(offset[:2]) * 60 + int(offset[3:])))
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse date with '+' offset: {date_input}. Error: {str(e)}")
                        return ""
                        
                elif '-' in date_input[19:]:  # Look for minus only after the date part
                    try:
                        # Split at - and remove the timezone part
                        date_part = date_input.split('-', 3)[0:3]  # Keep first 3 parts
                        date_part = '-'.join(date_part)
                        if '.' in date_part:
                            dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S.%f")
                        else:
                            dt = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
                        offset = date_input.split('-')[3]
                        dt = dt.replace(tzinfo=pytz.FixedOffset(-(int(offset[:2]) * 60 + int(offset[3:]))))
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse date with '-' offset: {date_input}. Error: {str(e)}")
                        return ""
                else:
                    # String format without explicit timezone
                    try:
                        if '.' in date_input:
                            dt = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S.%f")
                        else:
                            dt = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S")
                            
                        # Apply timezone based on assume_localtime
                        if assume_localtime:
                            try:
                                local_tz = get_localzone()
                                dt = dt.replace(tzinfo=local_tz)
                            except Exception as e:
                                logger.debug(f"Error setting local timezone: {str(e)}. Falling back to UTC.")
                                dt = dt.replace(tzinfo=pytz.UTC)
                        else:
                            dt = dt.replace(tzinfo=pytz.UTC)
                    except ValueError:
                        logger.debug(f"Unhandled date format: {date_input}")
                        return ""
        
        # Convert to local timezone for display if timezone information is present
        if dt.tzinfo is not None:
            try:
                local_tz = get_localzone()
                dt = dt.astimezone(local_tz)
            except Exception as e:
                logger.debug(f"Error converting to local timezone: {str(e)}")
                # Continue with current timezone if local conversion fails
        
        # Convert to the desired format
        return dt.strftime("%B %d, %Y %I:%M:%S %p") if include_time else dt.strftime("%B %d, %Y")
        
    except Exception as e:
        logger.debug(f"Unexpected error parsing date input '{date_input}': {str(e)}")
        return ""
    
# -----------------------------------------------------------------------------
def tell_user(message, log_as = ""):
    """
    Outputs a message to the console.
    """
    print(message)
    match log_as:
        case "info":
            logger.info(message)
        case "warning":
            logger.warning(message)
        case "error":
            logger.error(message)
        case "debug":
            logger.debug(message)
        case _:
            pass # no logging



def processing(out_char = "."):
    """
    Outputs a character to console.
    Intended to be called iterativley from a loop ton indicate progress.
    Default character is a period; however, a different character may be
       passed as an argument.
    This does not return anything.
    """
    print(out_char, end="")

# -----------------------------------------------------------------------------
def datetime_string(date_time = datetime.now(), format = "%Y-%m-%d--%H-%M-%S")-> str:
    """
    Converts a date and time to a formatted string.
    Optional Parameters:
    - date_time (datetime): A date and time to convert to a formatted string.
       default is the current date and time
    - format (str): The formatting string to use
        default is "%Y-%m-%d--%H-%M-%S" (YYYY-MM-DD--HH-MM-SS)

    Returns a formatted date time string.
    If an error occurs, returns an empty string.
    """
    ret_value = ""

    try:
        ret_value = date_time.strftime(format)
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} error handling date/time formatting: {str(error)}")
    return ret_value

# -----------------------------------------------------------------------------
def oscal_date_time_with_timezone(date_time = datetime.now(), format = "%Y-%m-%dT%H:%M:%SZ")-> str:
    """
    Converts a date and time to UTC and ouptuts an OSCAL date-time-with-timezone string. 
    Optional Parameters:
    - date_time (datetime): A date and time to convert to a formatted string.
       default is the current date and time
    - format (str): The formatting string to use
        default is "%Y-%m-%d--%H-%M-%S" (YYYY-MM-DD--HH-MM-SS)

    Returns a formatted date time string.
    If an error occurs, returns an empty string.
    """
    ret_value = ""

    try:
        date_time = date_time.astimezone(timezone.utc)
        ret_value = date_time.strftime(format)
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} error handling date/time formatting: {str(error)}")
    return ret_value

# -----------------------------------------------------------------------------
def get_first_non_whitespace_char(data):
    """
    Returns the first character this is not a space or tab.
    Returns an empty string if there is no content or if an error occurs.
    """
    ret_val = ""
    try:
        for character in data:
            if character.strip() != "":
                ret_val = character
                break
    except (Exception, BaseException) as error:
        logger.error(f"{type(error).__name__} error finding first non-whitespace character: {str(error)}")
    
    return ret_val

# -----------------------------------------------------------------------------
def iif(condition, if_true, if_false):
    """
    Accepts and evaluates a condition
    Returns the first parameter if the condition is true
    Returns the second parameter if false
    """
    if condition:
        return if_true
    else:
        return if_false

# -----------------------------------------------------------------------------
# =============================================================================
# Normalize Content
# Converts any bytes content to string.
# Passes through all other content type untouched.
# =============================================================================
def normalize_content(content):

    if isinstance(content, str):
        pass # We want string. Do nothing.
        logger.debug("NORMALIZE: Already string - do nothing")
    elif isinstance(content, bytes):
        content = content.decode("utf-8")
        logger.debug(("NORMALIZE: Decoded"))
    else:
        logger.debug( ("NORMALIZE: Unhandled content encoding: " + type(content)))

    return content

# -----------------------------------------------------------------------------
# Always returns a string from a JSON key.
# If the value at the key is string, int, float, complex or boolean, returns the value as a string.
# if the key exists more than once, it returns the first instance.
# If the value is a JSON object, it returns the serialized JSON object string.
# If the key does not exist in the JSON object, returns an empty string.
def safeJSON(object, keys):
    status = False
    ret_value = ""

    for key in keys:
        if key in object:
            object = object[key]
            status = True

        if status:
            obj_type = type(object)
            if obj_type is str:
                ret_value = object
            elif (obj_type is int or obj_type is float or obj_type is complex or obj_type is bool):
                ret_value = str(object)
            else:
                ret_value = json.dumps(object)

    return ret_value


# -----------------------------------------------------------------------------
# Always returns a string from a JSON key.
# If the value at the key is string, int, float, complex or boolean, returns the value as a string.
# if the key exists more than once, it returns the first instance.
# If the value is a JSON object, it returns the serialized JSON object string.
# If the key does not exist in the JSON object, returns an empty string.
def JSON_safe_atomic(object, key):
    ret_value = ""

    if key in object:
        object = object[key]
        obj_type = type(object)
        if obj_type is str:
            ret_value = object
        elif (obj_type is int or obj_type is float or obj_type is complex or obj_type is bool):
            ret_value = str(object)
        else:
            ret_value = json.dumps(object)

    return ret_value






# -----------------------------------------------------------------------------
# If the environment variable identified in the argument exits, return the value as a string.
# If the environment variable identified in the argument does not exit, return an empty string.
def handle_environment_variables(env_name, verbose = False, error_only = True):
    ret_value = ""
    if env_name in os.environ:
        ret_value = os.environ[env_name]
        if verbose: 
            logger.debug(env_name + " environtment variable set to: " + ret_value)
    else:
        if verbose or error_only:
            logger.debug(env_name + " environment variable not set.")
    return ret_value

# -----------------------------------------------------------------------------
# Obtains the user id from the operating system
def get_user_information():
    ret_val = ""
    # TODO make sure this works for Linux and Mac
    try:
        ret_val = gt.getuser()
    except (Exception, BaseException) as error:
        logger.error("Error getting user information. (" + type(error).__name__ + ") ", str(error))
        
    return ret_val

# -----------------------------------------------------------------------------
def indent(level, length=3) -> str:
    return (" " * length * level)


# -----------------------------------------------------------------------------
def prepare_html_for_json(html_content: str, escape_unicode: bool = True) -> str:
    """
    Prepares HTML content for safe transmission in a JSON field.
    
    Args:
        html_content (str): The HTML content to be prepared
        escape_unicode (bool): Whether to escape unicode characters. Defaults to True.
                             Set to False if your JSON encoder can handle unicode.
    
    Returns:
        str: The prepared HTML string safe for JSON transmission
    
    Examples:
        >>> html = '<div class="test">Hello & welcome</div>'
        >>> prepare_html_for_json(html)
        '<div class=\\"test\\">Hello & welcome</div>'
        
        >>> html_with_unicode = '<div>Hello 🌍</div>'
        >>> prepare_html_for_json(html_with_unicode)
        '<div>Hello \\ud83c\\udf0d</div>'
    """
    if not isinstance(html_content, str):
        raise TypeError("HTML content must be a string")
    
    # First, escape any existing backslashes
    content = html_content.replace('\\', '\\\\')
    
    # Escape quotes
    content = content.replace('"', '\\"')
    
    # Replace problematic whitespace characters
    content = content.replace('\n', '\\n')
    content = content.replace('\r', '\\r')
    content = content.replace('\t', '\\t')
    
    # Handle unicode if requested
    if escape_unicode:
        # Convert to json and back to handle unicode escaping
        # but preserve the already escaped characters
        content = json.dumps(content)[1:-1]  # Remove the surrounding quotes
    
    return content

def create_html_update_message(target_id: str, html_content: str, 
                             additional_data: Dict[str, Any] = None) -> str:
    """
    Creates a complete JSON message for HTML content update.
    
    Args:
        target_id (str): The ID of the target DOM element
        html_content (str): The HTML content to be inserted
        additional_data (dict): Optional additional data to include in the message
    
    Returns:
        str: JSON string ready for transmission
    
    Examples:
        >>> msg = create_html_update_message(
        ...     "status-div", 
        ...     '<p class="status">Processing...</p>'
        ... )
        >>> print(msg)
        {"type": "html", "targetId": "status-div", "content": "<p class=\\"status\\">Processing...</p>"}
    """
    if not target_id:
        raise ValueError("target_id cannot be empty")
    
    # Prepare the base message
    message = {
        "type": "html",
        "targetId": target_id,
        "content": prepare_html_for_json(html_content)
    }
    
    # Add any additional data
    if additional_data:
        if not isinstance(additional_data, dict):
            raise TypeError("additional_data must be a dictionary")
        message.update(additional_data)
    
    # Convert to JSON string
    try:
        return json.dumps(message)
    except Exception as e:
        raise ValueError(f"Failed to create JSON message: {str(e)}")

def is_valid_html_content(html_content: str) -> bool:
    """
    Performs basic validation of HTML content.
    This is a simple check for common issues, not a full HTML validator.
    
    Args:
        html_content (str): The HTML content to validate
    
    Returns:
        bool: True if the content appears valid, False otherwise
    
    Examples:
        >>> is_valid_html_content('<div>Valid</div>')
        True
        >>> is_valid_html_content('<div>Invalid</span>')
        False
    """
    if not html_content.strip():
        return False
        
    # Check for balanced tags
    stack = []
    tag_pattern = re.compile(r'</?([a-zA-Z][a-zA-Z0-9]*)[^>]*/?>')
    
    for tag_match in tag_pattern.finditer(html_content):
        tag = tag_match.group(1)
        full_tag = tag_match.group(0)
        
        # Skip self-closing tags
        if full_tag.endswith('/>'):
            continue
            
        # Handle opening/closing tags
        if not full_tag.startswith('</'):
            stack.append(tag)
        else:
            if not stack:
                return False
            if stack[-1] != tag:
                return False
            stack.pop()
    
    return len(stack) == 0



# =============================================================================
#  --- MAIN: Only runs if the module is executed stand-alone. ---
# =============================================================================
if __name__ == '__main__':
    print("Miscellaneous Function Library. Not intended to be run as a stand-alone file.")


