import asyncio
import sys
import json
from html import escape
import html
# import urllib.request
from urllib.parse import urljoin
from loguru import logger
from oscal_support import OSCAL_support
from time import sleep

# import elementpath
# from elementpath.xpath3 import XPath3Parser
from xml.etree import ElementTree
# from xml.dom import minidom

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring

from common import *

global_counter = 0
global_unhandled_report = []
global_stop_here = False

"""Metaschema Parser for OSCAL
This module provides functionality to parse and process OSCAL metaschema XML files.

While there is some defensive coding, this module assumes metaschema files are valid.

It is not intended to validate metaschema structure or content.
It will ignore unexpected structures.
It will issue a WARNING message if it encounteres expected, but unhandled structures. 

"""
SUPPRESS_XPATH_NOT_FOUND_WARNINGS = True
RUNAWAY_LIMIT = 2000
DEBUG_OBJECT = "choice"

PRUNE_JSON = False  # If true, will remove None values and emnpty arrays from the Resolved JSON Metaschema output
OSCAL_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"
METASCHEMA_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/metaschema/1.0"
METASCHEMA_TOP_IGNNORE = ["schema-name", "schema-version", "short-name", "namespace", "json-base-uri", "remarks", "import"]
METASCHEMA_TOP_KEEP = ["define-assembly", "define-field", "define-flag", "constraint"]
METASCHEMA_ROOT_ELEMENT = "METASCHEMA"
CONSTRAINT_ROOT_ELEMENT = "metaschema-meta-constraints"
CONSTRAINT_TOP_IGNORE = []
CONSTRAINT_TOP_KEEP = ["context"]

GREEN   = "\033[32m"
BLUE    = "\033[34m"
YELLOW  = "\033[33m"
RED     = "\033[31m"
ORANGE  = "\033[38;5;208m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
PURPLE  = "\033[38;5;129m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TODO:
# - Add support for metaschema constraints
# - Fix metaschema CHOICE
# - Handle group-as on output
# - Handle choicie on output
# -------------------------------------------------------------------------
def clean_none_values_recursive(dictionary):
    """
    Recursively remove all key/value pairs where the value is None from dictionaries,
    including nested dictionaries.
    """
    result = {}
    for k, v in dictionary.items():
        if v is None:
            continue
        elif isinstance(v, dict):
            cleaned = clean_none_values_recursive(v)
            if cleaned:  # Only add non-empty dictionaries
                result[k] = cleaned
        elif isinstance(v, list):
            cleaned_list = []
            for item in v:
                if isinstance(item, dict):
                    cleaned_item = clean_none_values_recursive(item)
                    if cleaned_item:  # Only add non-empty dictionaries
                        cleaned_list.append(cleaned_item)
                elif item is not None:
                    cleaned_list.append(item)
            if cleaned_list:  # Only add non-empty lists
                result[k] = cleaned_list
        else:
            result[k] = v
    return result

# -------------------------------------------------------------------------

# =============================================================================
# CREATES A COLLAPSIBLE HTML TREE FROM OSCAL JSON DATA
# =============================================================================
def generate_html_tree(json_data):
    """Generate HTML with collapsible tree from OSCAL JSON data."""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSCAL Schema Tree</title>
    <style>
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
    </style>
</head>
<body>
    <h1>OSCAL Schema Tree</h1>
    <div class="tree-view">
"""
    
    # Process the root element
    html += process_element(json_data)
    
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
def process_element(element, level=0):
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
            html += process_element(flag, level + 1)
        
        # Process children
        children = element.get('children', [])
        for child in children:
            html += process_element(child, level + 1)
        
        html += '</div>'
    
    return html

# -------------------------------------------------------------------------

# -------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MetaschemaParser:
    def __init__(self, metaschema, support, import_inventory=[], oscal_version=""):
        logger.debug(f"Initializing MetaschemaParser")
        self.content = metaschema
        self.valid_xml = False
        self.top_level = False
        self.xml_namespace = ""
        self.oscal_version = oscal_version
        self.oscal_model = ""
        self.schema_name = ""
        self.tree = None
        self.nsmap = {"": METASCHEMA_DEFAULT_NAMESPACE}
        self.support = support
        self.imports = {} # list of imports {"metaschema_file_name.xml": MetaschemaParser_Object, ...}
        self.import_inventory = import_inventory
    @classmethod
    async def create(cls, metaschema, support, import_inventory=[], oscal_version=""):
        logger.debug(f"Creating MetaschemaParser")
        ret_value = None
        ret_value = cls(metaschema, support, import_inventory, oscal_version)
        return ret_value
    # -------------------------------------------------------------------------
    def __str__(self):
        """String representation of the MetaschemaParser."""
        ret_value = ""
        ret_value += f"Schema: {self.schema_name}\n"
        ret_value += f"Model: {self.oscal_model}\n"
        ret_value += f"Version: {self.oscal_version}\n"
        ret_value += f"XML Namespace: {self.nsmap}\n"
        ret_value += f"Valid XML: {misc.iif(self.valid_xml, "Yes", "No")}\n"
        return ret_value
    
    # -------------------------------------------------------------------------
    def str_node(self, node):
        """String representation of the MetaschemaParser."""
        ret_value = ""
        ret_value += f"{node["formal-name"]}: {node["use-name"]}"
        if node["name"] != node["use-name"]:
            ret_value += f" ({node["name"]})"
        if node["deprecated"] is True:
            ret_value += f" ** Deprecated**"
        if node["sunsetting"] is not None:
            ret_value += f" Sunsetting: {node["sunsetting"]}"
        ret_value += "\n"

        if node["min-occurs"] == "0":
            if node["max-occurs"] == "1":
                ret_value += f"[0 or 1]"
            elif node["max-occurs"] == "unbounded":
                ret_value += f"[0 or more]"
            elif node["max-occurs"] is not None:
                ret_value += f"[0 to {node["max-occurs"]}]"
        elif node["min-occurs"] == "1":
            if node["max-occurs"] == "1":
                ret_value += f"[exactly 1]"
            elif node["max-occurs"] == "unbounded":
                ret_value += f"[1 or more]"
            elif node["max-occurs"] is not None:
                ret_value += f"[{node["min-occurs"]} to {node["max-occurs"]}]"
        else:
            if node["min-occurs"] is not None and node["max-occurs"] is not None:
                ret_value += f"[{node["min-occurs"]} to {node["max-occurs"]}]"
            else:
                ret_value += f"[Cardinality not specified]"
        ret_value += f" {node["structure-type"]} "
        ret_value += f" [{node["datatype"]}]"
        ret_value += f"Path: {node["path"]}\n"

        if node["default"] is not None:
            ret_value += f"Default: {node["default"]}\n"
        if node["description"] is not None:
            ret_value += f"Description: {node["description"]}\n"
        if node["remarks"] is not None:
            ret_value += f"Remarks: {node["remarks"]}\n"
        if node["example"] is not None:
            ret_value += f"Example: {node["example"]}\n"
        if node["flags"] is not None:
            ret_value += f"Flags: {len(node["flags"])}\n"
        if node["source"] is not None:
            ret_value += f"Source: {', '.join(node["source"])}\n"
        if node["children"] is not None:
            ret_value += f"Children: {len(node["children"])}\n"
        if node["props"] is not None:
            ret_value += f"Props: {', '.join(node["props"])}\n"

        if node["group-as"] is not None:
            ret_value += f"Group As: "
            if node["group-as-in-json"] is not None:
                ret_value += f" JSON: {node["group-as-in-json"]}"  
            if node["group-as-in-xml"] is not None:
                ret_value += f" XML: {node["group-as-in-xml"]}"
            ret_value += "\n"

        # if node["json-array-name"]:
        #     ret_value += f"JSON Array Name: {node["json-array-name"]} "
        # if node["json-value-key"]:
        #     ret_value += f" JSON Value Key: {node["json-value-key"]}"
        # if node["json-value-key-flag"]:
        #     ret_value += f" JSON Value Key Flag: {node["json-value-key-flag"]}"
        # ret_value += "\n"

        if node["wrapped-in-xml"] is not None:
            if node["wrapped-in-xml"]:
                ret_value += f"In XML: WRAPPED\n"
            else:
                ret_value += f"In XML: UNWRAPPED\n"
            ret_value += "\n"
        if node["rules"] is not None:
            ret_value += f"Rules: {len(node["rules"])}\n"
        return ret_value
    # -------------------------------------------------------------------------
    async def top_pass(self):
        """Perform the first pass of parsing."""
        logger.debug("Performing top pass")

        try:
            self.tree = data.deserialize_xml(self.content, METASCHEMA_DEFAULT_NAMESPACE)
            self.valid_xml = True
            logger.debug(f"XML Valid! Content length: {len(self.content)}")
        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            self.valid_xml = False

        if self.valid_xml:
            self.oscal_model = self.xpath_atomic("/METASCHEMA/define-assembly/root-name/text()")
            if self.oscal_model:
                self.top_level = True
            else:
                self.oscal_model = self.xpath_atomic("/METASCHEMA/short-name/text()")
                if not self.oscal_model:
                    self.oscal_model = "unnamed-imported-metaschema"
            self.schema_name = self.xpath_atomic("/METASCHEMA/schema-name/text()")
            if self.oscal_version == "":
                self.oscal_version = f"v{self.xpath_atomic("/METASCHEMA/schema-version/text()")}"
                logger.info(f"DEBUG: Setting version to {self.oscal_version} for {self.oscal_model}")

            await self.setup_imports()
            # await self.handle_imports()
        else:        
            logger.error("Invalid XML content.")

        return self.valid_xml
    # -------------------------------------------------------------------------
    async def setup_imports(self):
        """Identify import elements and set them up as import objects."""
        logger.debug(f"Setting up imports for {self.oscal_model}")
        import_directives = data.xpath(self.tree, self.nsmap, '/./METASCHEMA/import/@href')
        logger.debug(f"Imports: {self.imports}")

        if import_directives is not None:
            if not isinstance(import_directives, list):
                logger.debug(f"Import directives is not None and not a list: {import_directives}")
                import_directives = [import_directives]

            for imp_file in import_directives:
                logger.debug(f"Import file: {imp_file}")
                if imp_file:
                    # logger.info(f"Processing import: {imp_file}")
                    if False: # imp_file in self.import_inventory:
                        logger.info(f"Import {imp_file} already processed.")
                    else:
                        logger.debug(f"Processing {imp_file}  ...")
                        self.import_inventory.append(imp_file)
                        model_name = imp_file
                        if model_name.startswith("oscal_"):
                            model_name = model_name[len("oscal_"):]
                        if model_name.endswith("_metaschema_RESOLVED.xml"):
                            model_name = model_name[:-len("_metaschema_RESOLVED.xml")]

                        logger.debug(f"Model name: {model_name}")
                        import_content = await self.support.asset(self.oscal_version, model_name, "metaschema")
                        if import_content:
                            logger.debug(f"Version: {self.oscal_version} Model: {model_name} Content length: {len(import_content)}")
                            import_obj = await MetaschemaParser.create(import_content, self.support, self.import_inventory, self.oscal_version)
                            status = await import_obj.top_pass()
                            logger.debug(f"Import status: {status}")
                            if status:
                                self.imports[model_name] = import_obj
                                # self.imports.append({imp_file: import_obj})
                                logger.debug(f"Imports[0] for {imp_file}: {misc.iif(import_obj.top_level, "TOP", "NOT TOP")}")
                            else:
                                logger.error(f"Invalid Import file: {imp_file}")
        # logger.info(f"IMPORTS FOR {self.oscal_model}: {self.imports}")
        # logger.info(f"IMPORTS FOR {self.oscal_model}: {self.import_inventory}")

    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    def xpath_atomic(self, xExpr, context=None):
        """
        Performs an xpath query either on the entire XML document
        or on a context within the document.
        Parameters:
        - xExpr (str): An xpath expression
        - context (obj)[optional]: Context object.
        If the context object is present, the xpath expression is run against
        that context. If absent, the xpath expression is run against the
        entire document.
        Returns:
        - an empty string if there is an error or if nothing is found.
        - The first result of the xpath expression as a string.
        """

        return data.xpath_atomic(self.tree, self.nsmap, xExpr, context)

    # -------------------------------------------------------------------------
    def xpath(self, xExpr, context=None):
        """
        Performs an xpath query either on the entire XML document 
        or on a context within the document.

        Parameters:
        - xExpr (str): An xpath expression
        - context (obj)[optional]: Context object.
        If the context object is present, the xpath expression is run against
        that context. If absent, the xpath expression is run against the 
        entire document.

        Returns: 
        - None if there is an error or if nothing is found.
        - an element object or a list of element objects if the xpath expression
        is successful.
        """
        

        return data.xpath(self.tree, self.nsmap, xExpr, context)

    # -------------------------------------------------------------------------
    def get_markup_content(self, xExpr, context=None):
        """
        Performs an xpath query where the response is expected to be either
        just a string, or a node with HTML formatting.
        Returns the content as a stirng either way.
        """
        

        return data.get_markup_content(self.tree, self.nsmap, xExpr, context)

    # -------------------------------------------------------------------------
    def build_metaschema_tree(self):
        """
        Build the metaschema tree.
        """
        logger.debug(f"Resolving the metaschema tree for {self.oscal_model}")
        metaschema_tree = {}

        try:
            context = self.xpath("/METASCHEMA")
            metaschema_tree = self.recurse_metaschema(self.oscal_model, "define-assembly", context=context)

        except Exception as e:
            logger.error(f"Error building metaschema tree: {e}")
            metaschema_tree = {}
            
        try:    
            if metaschema_tree:
                if PRUNE_JSON:
                    # Clean up the metaschema tree by removing None values and empty arrays
                    metaschema_tree = clean_none_values_recursive(metaschema_tree)

                prefix = f"OSCAL_{self.oscal_version}_{self.oscal_model}"

                # save to a JSON file
                output_file = f"{prefix}_FULLY_RESOLVED_metaschema.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metaschema_tree, f, indent=2)


                output_file = f"{prefix}_unhandled_report.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(global_unhandled_report, f, indent=2)

                # Generate the HTML
                html_output = generate_html_tree(metaschema_tree)
                
                # Write the HTML to a file
                output_file = f"{prefix}_schema_outline.html"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_output)
        except Exception as e:
            logger.error(f"Error saving metaschema tree: {e}")

        return metaschema_tree
    # -------------------------------------------------------------------------
    def initialize_metaschema_tree_node(self):
        """
        Initialize the metaschema tree.
        This function sets up the initial structure of the metaschema tree.
        It is called before building the tree to ensure a consistent starting point.
        """

        # Reset the metaschema tree
        metaschema_tree_node = {
            "path": None,
            "use-name": None,
            "name": None,
            "structure-type": None,
            "datatype": None,
            "min-occurs": None,
            "max-occurs": None,

            "default": None,
            "formal-name": None,

            "wrapped-in-xml" : None,
            "group-as": None,
            "group-as-in-json": None,
            "group-as-in-xml": None,
            "json-array-name": None,
            "json-value-key": None,
            "json-value-key-flag": None,
            "json-collapsible": None,
            "deprecated": None,
            "sunsetting": None,
            "sequence": 0,
            "source": [],
            "props": [],

            "description": [],
            "remarks": [],
            "example": [],

            "flags" : [],
            "children": [],
            "rules": [],
        }
        
        return metaschema_tree_node
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # TODO: Handle constraints <<<<====---- ****
    # TODO: Handle constraints <<<<====---- ****
    # TODO: Handle constraints <<<<====---- ****
        
    # TODO: Fix situations where the ref isn't over-riding the definition, 
    #       such as with cardinality on //resource/props 
    # TODO: Fix the recursion detection, such as for task/task or part/part.
    # TODO: Fix handling of CHOICE elements
    # -------------------------------------------------------------------------
 
    def recurse_metaschema(self, name, structure_type="define-assembly", parent="", ignore_local=False, already_searched=[], context=None, skip_children=False):
        """
        Recursively build the metaschema tree.
        This function processes the XML tree and extracts significant nodes
        based on the defined rules. It creates a dictionary representation of the
        metaschema structure, including attributes and child elements.
        Parameters:
        - oscal_model (str): The OSCAL model name.
        - structure_type (str): The type of structure to process (define-assembly, define-field, define-flag, assembly-field-flag).
        - ignore_local (bool): Flag to ignore local elements.
        Returns:
        - dict: A dictionary representation of the metaschema tree.


        NOTE: ignore_local should be true when performing this function on an imported
        metaschema. This is because the imported metaschema may have local elements
        that are not intended to be exposed to the importing metaschema file. 
        """
        global global_counter, global_unhandled_report, global_stop_here
        global_counter += 1
        logger.debug(f"{GREEN}[{global_counter}] Working in {self.oscal_model} on {structure_type}:{name} at [{parent}]{RESET}")

        # Create the metaschema tree (etablishes consistent sequence for keys that should always be present)
        metaschema_tree = self.initialize_metaschema_tree_node()
        metaschema_tree["sequence"] = global_counter

        # ===== REASONS TO STOP RECURSION BEFORE COMPLETION ==========================
        if global_counter > RUNAWAY_LIMIT:
            logger.error(f"Recursion limit reached. Exiting.")
            global_stop_here = True
            return metaschema_tree

        if global_stop_here:
            logger.info(f"DEBUG: Stopping Early.")
            return None

        # .............................................................................
        # Check if this module was already searched
        if self.oscal_model in already_searched:
            logger.debug(f"Already searched {self.oscal_model}. Search List: {already_searched}. For {structure_type} {name}")
            return None
        else:
            already_searched.append(self.oscal_model)

        if DEBUG_OBJECT == name:
            logger.info(f"DEBUG: Working on {structure_type}: {name} in {self.oscal_model} under {parent}")
        if structure_type in ["field", "flag", "assembly"]:
            logger.debug(f"Looking for the {structure_type} definition for {name}")
            metaschema_tree = self.recurse_metaschema(name, f"define-{structure_type}", parent=parent, already_searched=[], context=None) 

        # .............................................................................
        # Setup xpath query
        # xpath_query = f"{misc.iif(context, ".", "/METASCHEMA")}/{structure_type}"
        xpath_query = f"./{structure_type}"
        no_local = misc.iif(ignore_local, " and not(@scope='local')", "")
        xpath_query += f"[@{misc.iif(structure_type in ["field", "flag", "assembly"], "ref", "name")}='{name}'{no_local}]"
        if DEBUG_OBJECT == name:
            logger.info(f"DEBUG: Looking for {structure_type}: {name} in {self.oscal_model} with xpath: {xpath_query}")

        result = self.xpath(xpath_query, context)
    
        if result is None:
            if structure_type in ["define-assembly", "define-field", "define-flag"]:
                if context is not None:
                    metaschema_tree = self.recurse_metaschema(name, structure_type, parent=parent, ignore_local=False, already_searched=[], context=None)
                else:
                    # If nothing was found, look in the imported files
                    logger.debug(f"Did not find <{structure_type}: '{name}' ... > in {self.oscal_model}")
                    metaschema_tree = self.look_in_imports(name, structure_type, parent=parent, ignore_local=ignore_local, already_searched=already_searched)
            else:
                # assembly, field, and flag should always be found in the passed context.
                logger.error(f"Did not find <{structure_type}: '{name}' ... > in {data.xml_to_string(context)}")
        else:
            # .............................................................................
            if isinstance(result, list):
                # Duplicate definitions are not allowed in metaschema, so this would only happen if the metaschema was invliad.
                logger.warning(f"Found multiple {structure_type} objects named '{name}'. Using the first one found. [{xpath_query} ({context})]")
                definition_obj = result[0]
            else:
                # A single element was found as expected
                definition_obj = result
            logger.debug(f"Found: <{structure_type} name='{name}' ... >")

            metaschema_tree["name"]                = name # should always be present
            metaschema_tree["structure-type"]      = structure_type.replace("define-", "")
            metaschema_tree["use-name"]            = self.graceful_override(metaschema_tree["use-name"],            "./use-name/text()", definition_obj)
            if metaschema_tree["use-name"] is None or metaschema_tree["use-name"] == "":
                metaschema_tree["use-name"] = metaschema_tree["name"]
            if metaschema_tree["path"] is None or metaschema_tree["path"] == "":
                if structure_type in ["define-assembly", "assembly", "define-field", "field"]:
                   metaschema_tree["path"] = f"{parent}/{metaschema_tree["use-name"]}"
                elif structure_type in ["define-flag", "flag"]:
                    metaschema_tree["path"] = f"{parent}/@{metaschema_tree["use-name"]}"

            metaschema_tree["formal-name"]         = self.graceful_override(metaschema_tree["formal-name"],         "./formal-name/text()", definition_obj)
            # metaschema_tree["json-key"]            = self.graceful_override(metaschema_tree["json-key"],            "./json-key/text()", definition_obj)
            metaschema_tree["json-value-key"]      = self.graceful_override(metaschema_tree["json-value-key"],      "./json-value-key/text()", definition_obj)
            metaschema_tree["json-value-key-flag"] = self.graceful_override(metaschema_tree["json-value-key-flag"], "./json-value-key-flag/text()", definition_obj)

            metaschema_tree["description"] = self.graceful_accumulate(metaschema_tree["description"], "./description", definition_obj)
            metaschema_tree["remarks"]     = self.graceful_accumulate(metaschema_tree["remarks"]    , "./remarks", definition_obj)
            metaschema_tree["example"]     = self.graceful_accumulate(metaschema_tree["example"]    , "./example", definition_obj)


            # Handle metaschmea attributes, such as @datatype, @min-occurs, @max-occurs
            metaschema_tree = self.handle_attributes(metaschema_tree, definition_obj, structure_type, name, parent)
            if metaschema_tree is None or metaschema_tree == {}:
                logger.error(f"Lost data handling attributes for {structure_type} / {name}.")
                return {} 
            
            # Set default values where appropriate
            metaschema_tree = self.set_default_values(metaschema_tree, definition_obj, structure_type, name, parent)
            if metaschema_tree is None or metaschema_tree == {}:
                logger.error(f"Lost data setting defaults for {structure_type} / {name}.")
                return {} 
            
            # Handle group-as element, which is used to indicate how fields or assemblies should be grouped
            metaschema_tree = self.handle_group_as(metaschema_tree, definition_obj, structure_type, name, parent)
            if metaschema_tree is None or metaschema_tree == {}:
                logger.error(f"Lost data handling group-as for {structure_type} / {name}.")
                return {}

            # Identify which metaschema file this object is from
            if "source" in metaschema_tree:
                metaschema_tree["source"].append(self.oscal_model)
            else:
                metaschema_tree["source"] = [self.oscal_model]  

            metaschema_tree["flags"]    = self.handle_flags(metaschema_tree, definition_obj, structure_type, name, parent)
            logger.debug(f"Back from handle flags in {self.oscal_model} for {structure_type} / {name} in {parent}")

            if not misc.has_repeated_ending(metaschema_tree["path"], f"/{metaschema_tree["use-name"]}", frequency=2):
                metaschema_tree["children"] = self.handle_children(name, structure_type, metaschema_tree, definition_obj)
                logger.debug(f"Back from handle model")
            else:
                # It is one of several known circular references that needs to be handled.
                logger.info(f"Circular Reference protection: {name} is the same as the parent at {metaschema_tree["path"]}")
                metaschema_tree["structure-type"] = "recursive"
                metaschema_tree["description"] = "<b>Recursive: See parent</b>"
                metaschema_tree["children"] = []

        # .............................................................................

        if metaschema_tree is None or metaschema_tree == {}:
            logger.error(f"Did not find {structure_type} / {name} in {self.oscal_model} or any imports.")
        else:
            if DEBUG_OBJECT == name:
                logger.info(f"****: Found {structure_type} / {name} in {self.oscal_model} with path: {metaschema_tree["path"]}")
                logger.info(f"****: metaschema_tree: {self.str_node(metaschema_tree)}")

        return metaschema_tree

    # -------------------------------------------------------------------------
    def handle_group_as(self, metaschema_tree, definition_obj, structure_type, name, parent):
        """
        Handle the group-as element for the metaschema tree.
        This function processes the group-as element and its attributes,
        setting them in the metaschema tree.
        """
        logger.debug(f"Handling group-as for {structure_type} {name}")

        temp_group_as = self.xpath(f"./group-as", definition_obj)
        if temp_group_as is not None:
            if structure_type in ["define-assembly", "assembly", "define-field", "field"]:
                logger.debug(f"Found group-as for {structure_type} {name}")
                if temp_group_as.attrib:
                    logger.debug(f"Has attributes.")
                    metaschema_tree["group-as"] = temp_group_as.attrib.get("name", "")
                    if "in-xml" in temp_group_as.attrib:
                        logger.debug(f"Found in-xml attribute: {temp_group_as.attrib.get('in-xml')}")
                        if temp_group_as.attrib.get("in-xml") in ["GROUPED"]:
                            metaschema_tree["wrapped-in-xml"] = temp_group_as.attrib.get("name", "")
                            metaschema_tree["xpath"] = f"{parent}/{temp_group_as.attrib.get("name", "")}/{metaschema_tree["use-name"]}"
                        elif temp_group_as.attrib.get("in-xml") in ["UNGROUPED"]:
                            pass
                        else:
                            logger.warning(f"Unexpected in-xml value: {temp_group_as.attrib.get('in-xml')}")
                        metaschema_tree["group-as-in-xml"] = temp_group_as.attrib.get("in-xml")
                    if "in-json" in temp_group_as.attrib:
                        logger.debug(f"Found in-json attribute: {temp_group_as.attrib.get('in-json')}")
                        metaschema_tree["group-as-in-json"] = temp_group_as.attrib.get("in-json")
            else:
                logger.warning(f"Group-as found where it is not expected: {structure_type} {name}")

        return metaschema_tree
    # -------------------------------------------------------------------------
    def graceful_accumulate(self, current_value, xExpr, context=None):
        """
        Handle graceful accumulation for the metaschema tree where a field or assembly ref
        values need to be added to any existing defined-field or define-assembly values.
        """
        logger.debug(f"Handling graceful accumulation for {xExpr}")

        temp_value = self.get_markup_content(xExpr, context)
        if temp_value is not None and temp_value != "":
            if not isinstance(current_value, list):
                current_value = []
            current_value.insert(0, temp_value)

        return current_value
    # -------------------------------------------------------------------------
    def graceful_override(self, current_value, xExpr, context=None):
        """
        Handle graceful overrides for the metaschema tree where a field or assembly ref
        values need to replace any existing defined-field or define-assembly values.
        """
        ret_value = None
        logger.debug("Handling graceful overrides")
        temp_value = self.xpath_atomic(xExpr, context)
        if temp_value != "":
            ret_value = temp_value
        else:
            ret_value = current_value

        return ret_value
    # -------------------------------------------------------------------------
    def set_default_values(self, metaschema_tree, definition_obj, structure_type, name, parent):
        """
        Set default values for the metaschema tree.
        This function sets default values for various attributes in the metaschema tree
        based on the structure type and other conditions.
        """
        logger.debug("Setting default values")
        # Set default values for metaschema tree
        if metaschema_tree is not None:

            # If any of these have not been defined by this point, set them to default 
            # values per the metaschema specification.
            metaschema_tree.setdefault("datatype", "string")
            if metaschema_tree.get("datatype") is None:
                metaschema_tree["datatype"] = "string"
            if metaschema_tree.get("min-occurs") is None:
                metaschema_tree["min-occurs"] = "0"
            if metaschema_tree.get("max-occurs") is None:
                metaschema_tree["max-occurs"] = "1"
            if parent == "": # special case for the root element, which is identified because it has no parent.
                metaschema_tree["min-occurs"] = "1"
                metaschema_tree["max-occurs"] = "1"

            if metaschema_tree.get("is-collapsible") is None:
                metaschema_tree["is-collapsible"] = False
            if metaschema_tree.get("deprecated") is None:
                metaschema_tree["deprecated"] = False
            if metaschema_tree.get("default") is None:
                metaschema_tree["default"] = None # Explicitly makes present and sets to None

            if structure_type in ["define-field", "field", "define-assembly", "assembly"]:
                if metaschema_tree.get("wrapped-in-xml") is None:
                    metaschema_tree["wrapped-in-xml"] = True

        return metaschema_tree
    # -------------------------------------------------------------------------
    def look_in_imports(self, name, structure_type, parent="", ignore_local=False, already_searched=[]):
        """
        Look for a metaschema definition in the imported files.
        This function searches through the imported metaschema files to find
        a specific definition by name and structure type.
        """
        logger.debug(f"Looking for {structure_type} {name} in imports")
        metaschema_tree = None

        # Cycle through each of the imported metaschema files
        for item in self.imports:
            import_file = item
            parser_object = self.imports[import_file]
            metaschema_tree = parser_object.recurse_metaschema(name, structure_type, parent=parent, ignore_local=True, already_searched=already_searched, context=None)
            if metaschema_tree is not None and metaschema_tree != {}:
                break

        # Check if we got a meaningful result, not just an empty dict or None
        if metaschema_tree is not None and metaschema_tree.get("structure-type")!= "":
            logger.debug(f"FOUND in {import_file}: {structure_type}: {name}")
            if name == DEBUG_OBJECT:
                logger.info(f"DEBUG: FOUND in {import_file}: {structure_type}: {name}")
        # else:
        #     # Reset metaschema_tree to None so we continue searching
        #     metaschema_tree = None

        if metaschema_tree is None and not ignore_local: # ignore_local is only false at the top level
            logger.error(f"Did not find {structure_type}: {name} in {self.oscal_model} nor any imports. Parent: {parent}")

        return metaschema_tree
    # -------------------------------------------------------------------------
    def handle_flags(self, metaschema_tree, definition_obj, structure_type, name, parent):
        """Handle Flags defined or referenced in the Field or Assembly"""
        logger.debug(f"Handling flags for {structure_type} {name}")
        
        hold_flags = metaschema_tree.get("flags", [])

        temp_flags = self.xpath(f"./(define-flag | flag)", definition_obj)
        if temp_flags is not None:
            logger.debug(f"Found {len(temp_flags)} flags in {structure_type} {name}")
            if not structure_type in ["define-assembly", "assembly", "define-field", "field"]:
                logger.warning(f"Flags are only allowed in define-assembly, assembly, define-field, field. Not in {structure_type} {name}")

            if not isinstance(temp_flags, list): # more than one
                temp_flags = [temp_flags]

            for flag in temp_flags:
                flag_structure_type = flag.tag.split('}')[-1]  # Remove namespace
                flag_name = ""
                if "ref" in flag.attrib:
                    flag_name = flag.attrib['ref']
                elif "name" in flag.attrib: 
                    flag_name = flag.attrib['name']
                else:
                    logger.error (f"Flag: {flag_structure_type} contains neither @name nor @ref")

                if flag_name:
                    logger.debug(f"Building: {metaschema_tree["path"]}/@{flag_name}")
                    meta_object = self.recurse_metaschema(flag_name, flag_structure_type, parent=metaschema_tree["path"], already_searched=[], context=definition_obj)
                    if meta_object is not None and meta_object != {}:
                        hold_flags.append(meta_object)
        else:
            logger.debug(f"No flags found within {structure_type} {name}")
        
        return hold_flags
    # -------------------------------------------------------------------------
    def handle_attributes(self, metaschema_tree, definition_obj, structure_type, name, parent):
        """
        Handle attributes for the metaschema tree.
        This function processes the attributes of the given XML element and
        updates the metaschema tree accordingly.
        """
        logger.debug("Handling attributes")

        if definition_obj.attrib:
            for attr_name, attr_value in definition_obj.attrib.items():
                logger.debug(f"{structure_type} ({name}) Attribute: {attr_name} = {attr_value}")
                match attr_name:
                    case "name" | "ref" | "scope":
                        pass # Already captured: name, ref. Ignoring: scope
                    case "as-type": # for fields and flags
                        metaschema_tree["datatype"] = attr_value or metaschema_tree["datatype"]
                    case "required": # For flags
                        if attr_value == "yes":
                            metaschema_tree["min-occurs"] = "1"
                            metaschema_tree["max-occurs"] = "1"
                        elif attr_value == "no":
                            metaschema_tree["min-occurs"] = "0" 
                            metaschema_tree["max-occurs"] = "1" 
                    case "min-occurs": # For fields and assemblies
                        metaschema_tree["min-occurs"] = attr_value or metaschema_tree["min-occurs"]
                    case "max-occurs": # For fields and assemblies
                        metaschema_tree["max-occurs"] = attr_value or metaschema_tree["max-occurs"]
                    case "collapsible": # For fields
                        if attr_value == "yes":
                            metaschema_tree["is-collapsible"] = True
                        elif attr_value == "no": # default is "no"
                            metaschema_tree["is-collapsible"] = False
                        logger.debug(f"Collapsible: {metaschema_tree['is-collapsible']}")
                        unhandled = {"path": metaschema_tree["path"], "structure": metaschema_tree["structure-type"], attr_name: attr_value}
                        global_unhandled_report.append(unhandled)
                    case "deprecated":
                        if misc.compare_semver(attr_value, self.oscal_version) <= 0:
                            metaschema_tree["deprecated"] = True
                        else:
                            metaschema_tree["sunsetting"] = attr_value
                    case "default":
                        if structure_type in ["define-field", "define-flag"]:
                            metaschema_tree["default"] = attr_value
                        else:
                            logger.warning(f"Unexpected attribute: <define-{structure_type} name='{name}' {attr_name}='{attr_value}'")
                    case "in-xml":
                        if structure_type in ["define-field", "field", "define-assembly", "assembly"]:
                            if attr_value in ["WRAPPED", "WITH_WRAPPER"]:
                                metaschema_tree["wrapped-in-xml"] = True
                            else:
                                metaschema_tree["wrapped-in-xml"] = False
                        else:
                            logger.warning(f"Unexpected attribute: <define-{structure_type} name='{name}' {attr_name}='{attr_value}'")
                    case _:
                        logger.warning(f"Unexpected attribute: <{structure_type} ({name}) {attr_name}='{attr_value}'")

        return metaschema_tree
    
    # -------------------------------------------------------------------------
    def handle_children(self, name, structure_type, metaschema_tree, context, handle_choice=0):
        global global_unhandled_report, global_counter
        """Handle model specification for defined assemblies"""
        hold_children = metaschema_tree.get("children", [])
        choice_count = 0

        if structure_type == "define-assembly":
            xExpr = f"./model"
        elif structure_type == "choice":
            logger.info(f"Handling choice {handle_choice} for {metaschema_tree['path']}")
            xExpr = f"(./model/choice)[{handle_choice}]"
            logger.info(f"{xExpr} for {structure_type} {name} in {metaschema_tree["path"]}")
        else:
            xExpr = f""

        if xExpr != "":
            children = self.xpath(xExpr, context)
            if children is not None:
                for child in children:
                    child_structure_type = child.tag.split('}')[-1]  # Remove namespace
                    if child_structure_type in ["field", "assembly", "define-field", "define-assembly", "choice", "any"]:
                        if child_structure_type in ["define-field", "define-assembly"]:
                            child_name = child.attrib.get("name", "")
                        elif child_structure_type in ["field", "assembly"]:
                            child_name = child.attrib.get("ref", "")
                        elif child_structure_type in ["choice", "any"]:
                            logger.info(f"FOUND {child_structure_type} in {metaschema_tree["path"]}")
                            child_name = f"{child_structure_type.upper()}"

                        logger.info(f"[{global_counter}] {ORANGE}Building: {metaschema_tree["path"]}/{child_name} [{child.attrib}]")

                        if child_structure_type in ["define-field", "define-assembly", "field", "assembly"]:

                            meta_object = self.recurse_metaschema(child_name, child_structure_type, parent=metaschema_tree["path"], ignore_local=False, context=children, already_searched=[])
                            if meta_object is not None and meta_object != {}:
                                hold_children.append(meta_object)
                            else:
                                logger.error(f"Unexpected empty return at {metaschema_tree["path"]} for child: {child_structure_type} {child_name}")


                        elif child_structure_type == "choice":
                            choice_count += 1
                            logger.debug(f"Handling choice {choice_count} for {metaschema_tree["path"]}")
                            temp_object = {}
                            temp_object["name"] = f"CHOICE"
                            temp_object["structure-type"] = "choice"
                            temp_object["path"] = metaschema_tree["path"] 
                            temp_object["source"] = metaschema_tree["source"]
                            temp_object["children"] = self.handle_children(child_name, child_structure_type, temp_object, context=context, handle_choice=choice_count)

                            hold_children.append(temp_object)

                        elif child_structure_type == "any":
                            temp_object = {}
                            temp_object["name"] = f"ANY"
                            temp_object["structure-type"] = "any"
                            temp_object["path"] = metaschema_tree["path"] + f"/*"
                            temp_object["source"] = metaschema_tree["source"]
                            hold_children.append(temp_object)
                            global_unhandled_report.append({"path": metaschema_tree["path"], "structure": metaschema_tree["structure-type"], "child": child_structure_type})

                    else:
                        logger.error(f"Unexpected child structure type: {child_structure_type} in model for {structure_type} {name}")
            else:
                logger.warning(f"No children found in model for {structure_type} {name}")
        return hold_children

# ========================================================================

async def setup_support(support_file= "./support/support.oscal"):
    logger.debug(f"Setting up support file: {support_file}")
    
    support = await OSCAL_support.create(support_file)
    cycle = 0
    while not support.ready:
        logger.debug("Waiting for support object to be ready...")
        if support.db_state != "unknown":
            logger.debug(f"Support file status {support.db_state}")
            break
        cycle += 1
        if cycle > 20:
            logger.error(f"Support object took too long to be ready.({support.db_state})")
            break
        sleep(0.25)
    if not support.ready:
        logger.error("Support object is not ready.")
    else:
        logger.debug("Support file is ready.")

    return support
# -------------------------------------------------------------------------
async def main():
    base_url = "./support/support.oscal"
    status = False
    parsed_data = ""
    # base_url = "https://github.com/usnistgov/OSCAL/releases/download/v1.1.3/oscal_complete_metaschema_RESOLVED.xml"
    
    support = await setup_support(base_url)
    if support.ready:
        logger.debug("Support file is ready.")
        status = True
    else:
        logger.error("Support object is not ready.")

    if status:
        for version in support.versions.keys():
            logger.info(f"Version: {version}")

            models = await support.enumerate_models(version)
            for model in models:
                logger.info(f"Processing {version}: {model}")
                # Fetch the XML content
                model_metaschema = await support.asset(version, model, "metaschema")
                if model_metaschema:
                    # Parse the XML content
                    logger.debug(f"Parsing {model} metaschema.")    
                    parser = await MetaschemaParser.create(model_metaschema, support)
                    status = await parser.top_pass()

                    if status:
                        status = parser.build_metaschema_tree()
                    else:
                        logger.error(f"Failed to setup the {model}. metaschema")
                    
                    status = True

                # only parsing first model for now
                break
            # only parsing first version for now
            break

    if status:
        ret_value = 0
    else:
        ret_value = 1
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
        exit_code = asyncio.run(main())
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
