import sys
import json
import glob
from html import escape
import html
from loguru import logger
from time import sleep
from common import *

DATA_LOCATION = "./"

# TODO:
# - Handle group-as on output
# - Handle choicie on output
# - Handle unwrapped on output


# =============================================================================
# CREATES A COLLAPSIBLE HTML TREE FROM A FULLY RESOLVED JSON METASCHEMA OBJECT
# =============================================================================
def generate_tree_view(metaschema_tree, format):
    """Generate HTML with collapsible tree from OSCAL JSON data."""
    
    style = """
        .tree-view {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .tree-item {
            margin-left: 20px;
        }
        .collapsible {
            cursor: pointer;
            user-select: none;
            padding: 5px;
            margin: 2px 0;
            background-color: #f1f1f1;
            border-radius: 4px;
            display: block; /* Changed from inline-block to block */
            width: calc(100% - 10px); /* Account for padding */
        }
        .collapsible:hover {
            background-color: #ddd;
        }
        .content {
            display: none;
            margin-left: 20px;
        }
        .element-name {
            font-weight: bold;
            color: #2c5282;
            text-decoration: none;
        }
        .element-name:hover {
            text-decoration: underline;
        }
        .element-details {
            color: #4a5568;
            font-size: 0.9em;
        }
        .active {
            display: block;
        }
        .type-assembly { color: #3182ce; }
        .type-field { color: #805ad5; }
        .type-flag { color: #dd6b20; }
        .expander {
            display: inline-block;
            width: 15px;
            text-align: center;
            font-weight: bold;
            cursor: pointer;
        }
        .spacer {
            display: inline-block;
            width: 15px;
        }
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metaschema_tree["oscal_version"]} {{metaschema_tree["oscal_model"]}} ({format.upper()})</title>
    <style>
{style}
    </style>
</head>
<body>
    <h1>{metaschema_tree["schema_name"]} {format.upper()}</h1>
    <h3>OSCAL Version: {metaschema_tree["oscal_version"]}</h3>
    
    <div class="tree-view">
"""
    
    # Process the root element
    match format:
        case "xml":
            logger.info("Processing XML format")
            html += process_xml_element(metaschema_tree["nodes"], level=0)
        case "json" | "yaml":
            pass
            # html += process_json_element(metaschema_tree["nodes"], format, level=0)
    
    html += """
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            var expanders = document.getElementsByClassName("expander");
            for (var i = 0; i < expanders.length; i++) {
                expanders[i].addEventListener("click", function(e) {
                    e.stopPropagation(); // Prevent event bubbling
                    var content = this.parentElement.nextElementSibling;
                    
                    if (content.style.display === "block") {
                        // Collapsing
                        content.style.display = "none";
                        this.textContent = "+";
                    } else {
                        // Expanding
                        content.style.display = "block";
                        this.textContent = "-";
                    }
                });
            }
            
            // Stop propagation for element name clicks
            var elementNames = document.getElementsByClassName("element-name");
            for (var i = 0; i < elementNames.length; i++) {
                elementNames[i].addEventListener("click", function(e) {
                    e.stopPropagation();
                    // You can add your click handler for the path here
                    console.log("Clicked on path:", this.getAttribute("data-path"));
                });
            }
            
            // Add click handler for the collapsible divs (optional)
            var collapsibles = document.getElementsByClassName("collapsible");
            for (var i = 0; i < collapsibles.length; i++) {
                collapsibles[i].addEventListener("click", function(e) {
                    if (e.target.classList.contains('element-name')) return;
                    
                    // Find the expander in this collapsible and trigger its click
                    var expander = this.querySelector('.expander');
                    if (expander) {
                        expander.click();
                    }
                });
            }
        });
    </script>
</body>
</html>
"""
    return html

# -------------------------------------------------------------------------
def process_json_element(element, format, level=0):
    """Process a single element in the OSCAL schema."""
    if not isinstance(element, dict):
        return ""
    
    html = ""
    
    # Get element properties
    use_name = element.get('use-name', element.get('name', 'unknown'))
    structure_type = element.get('structure-type', 'unknown')
    datatype = element.get('datatype', '')
    min_occurs = element.get('min-occurs', '')
    max_occurs = element.get('max-occurs', '')
    path = element.get('path', '')
    
    # Format occurrence information
    occurrence = ""
    if min_occurs == "0" and (max_occurs == "1" or max_occurs == "unbounded"):
        occurrence = "[0 or 1]" if max_occurs == "1" else "[0 or more]"
    elif min_occurs == "1" and max_occurs == "1":
        occurrence = "[exactly 1]"
    elif min_occurs == "1" and max_occurs == "unbounded":
        occurrence = "[1 or more]"
    else:
        occurrence = f"[{min_occurs}..{max_occurs}]"
    
    # Check if element has children or flags to determine if we need expansion control
    has_expandable = (element.get('flags', []) or element.get('children', []))
    
    # Create the element header with details
    html += '<div class="collapsible">'
    if has_expandable:
        # Set the initial expander symbol based on level
        expander_symbol = "-" if level == 0 else "+"
        html += f'<span class="expander">{expander_symbol}</span> '
    else:
        html += '<span class="spacer">&nbsp;</span> '
    html += f'<a href="#" class="element-name" data-path="{escape(path)}">{escape(use_name)}</a> '
    html += f'<span class="element-details type-{structure_type}">({structure_type})</span> '
    html += f'<span class="element-details">{escape(str(datatype))} {occurrence}</span>'
    html += '</div>'
    
    # Create content div for children and flags together
    if has_expandable:
        # Set initial display style based on level
        display_style = "block" if level == 0 else "none"
        html += f'<div class="content tree-item" style="display: {display_style};">'
        
        # Process flags (attributes)
        flags = element.get('flags', [])
        for flag in flags:
            html += process_json_element(flag, format, level + 1)
        
        # Process children
        children = element.get('children', [])
        for child in children:
            html += process_json_element(child, format, level + 1)
        
        html += '</div>'
    
    return html

# -------------------------------------------------------------------------
def process_xml_element(element, level=0):
    """Process a single element in the OSCAL schema."""
    if not isinstance(element, dict):
        return ""
    
    html = ""
    
    # Get element properties
    use_name = element.get('use-name', element.get('name', 'unknown'))
    structure_type = element.get('structure-type', 'unknown')
    datatype = element.get('datatype', '')
    min_occurs = element.get('min-occurs', '')
    max_occurs = element.get('max-occurs', '')
    path = element.get('path', '')
    logger.info(f"Processing element: {path}")
    
    # Format occurrence information
    occurrence = ""
    if min_occurs == "0" and (max_occurs == "1" or max_occurs == "unbounded"):
        occurrence = "[0 or 1]" if max_occurs == "1" else "[0 or more]"
    elif min_occurs == "1" and max_occurs == "1":
        occurrence = "[exactly 1]"
    elif min_occurs == "1" and max_occurs == "unbounded":
        occurrence = "[1 or more]"
    else:
        occurrence = f"[{min_occurs}..{max_occurs}]"
    
    # Check if element has children or flags to determine if we need expansion control
    has_expandable = (element.get('flags', []) or element.get('children', []))
    
    # Create the element header with details
    html += '<div class="collapsible">'
    if has_expandable:
        # Set the initial expander symbol based on level
        expander_symbol = "-" if level == 0 else "+"
        html += f'<span class="expander">{expander_symbol}</span> '
    else:
        html += '<span class="spacer">&nbsp;</span> '
    html += f'<a href="#" class="element-name" data-path="{escape(path)}">{escape(use_name)}</a> '
    html += f'<span class="element-details type-{structure_type}">({structure_type})</span> '
    html += f'<span class="element-details">{escape(str(datatype))} {occurrence}</span>'
    html += '</div>'
    
    # Create content div for children and flags together
    if has_expandable:
        # Set initial display style based on level
        display_style = "block" if level == 0 else "none"
        html += f'<div class="content tree-item" style="display: {display_style};">'
        
        # Process flags (attributes)
        flags = element.get('flags', [])
        for flag in flags:
            html += process_xml_element(flag, level + 1)
        
        # Process children
        children = element.get('children', [])
        for child in children:
            html += process_xml_element(child, level + 1)
        
        html += '</div>'
    
    return html

# -------------------------------------------------------------------------

def main():
    ret_value = False

    file_pattern = f"{DATA_LOCATION}/OSCAL*metaschema.json"
    # For each file that matches the pattern
    for file_path in glob.glob(file_pattern):
        logger.info(f"Processing file: {file_path}")
        
        # Load the metaschema JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            metaschema_tree = json.load(f)

        prefix = f"OSCAL_{metaschema_tree["oscal_version"]}_{metaschema_tree["oscal_model"]}"


        for format in ["xml"]: # , "json", "yaml"]:
            html_output = generate_tree_view(metaschema_tree, format=format)
            output_file = f"{DATA_LOCATION}/{prefix}_outline_{format}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_output)

    return ret_value

if __name__ == "__main__":
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True
    )

    logger.add(
        "output.log",
        level="DEBUG",  # Log everything to file
        colorize=False,
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True
    )


    try:
        exit_code = main()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)

