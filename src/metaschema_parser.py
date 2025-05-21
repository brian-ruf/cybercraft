import asyncio
import sys
import json
import urllib.request
from urllib.parse import urljoin
from loguru import logger
from oscal_support import OSCAL_support
from time import sleep

import elementpath
from elementpath.xpath3 import XPath3Parser
from xml.etree import ElementTree
from xml.dom import minidom
from common import *
import copy

"""Metaschema Parser for OSCAL
This module provides functionality to parse and process OSCAL metaschema XML files.

While there is some defensive coding, this module assumes metaschema files are valid.

It is not intended to validate metaschema structure or content.
It will ignore unexpected structures.
It will issue a WARNING message if it encounteres expected, but unhandled structures. 

"""
OSCAL_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"
METASCHEMA_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/metaschema/1.0"
METASCHEMA_TOP_IGNNORE = ["schema-name", "schema-version", "short-name", "namespace", "json-base-uri", "remarks", "import"]
METASCHEMA_TOP_KEEP = ["define-assembly", "define-field", "define-flag", "constraint"]
METASCHEMA_ROOT_ELEMENT = "METASCHEMA"
CONSTRAINT_ROOT_ELEMENT = "metaschema-meta-constraints"
CONSTRAINT_TOP_IGNORE = []
CONSTRAINT_TOP_KEEP = ["context"]

GREEN = "\033[32m"
RESET = "\033[0m"
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# -------------------------------------------------------------------------
from packaging.version import parse as parse_version

def compare_semver(version1, version2):
    """
    Compare two semantic versions and return:
    -1 if version1 < version2
     0 if version1 == version2
     1 if version1 > version2
    """
    v1 = parse_version(version1)
    v2 = parse_version(version2)
    
    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    else:
        return 0
# -------------------------------------------------------------------------
def xpath(tree, nsmap, xExpr, context=None):
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
    - A single element if exactly one is found
    - A list of elements if multiple are found
    """
    result = None
    try:
        if context is None:
            logger.debug(f"XPath: {xExpr}")            
            result = elementpath.select(tree, xExpr, namespaces=nsmap)
        else:
            logger.debug(f"XPath (Context: { context.tag }): {xExpr}")            
            result = elementpath.select(context, xExpr, namespaces=nsmap)
        
        # Return None for empty results
        if not result:
            return None
        
        # Return the single element if there's only one result
        if len(result) == 1:
            result= result[0]
        
    except SyntaxError as e:
        logger.error(f"XPath syntax error: {e} in {xExpr}")
    except IndexError as e:
        logger.debug(f"XPath result not found for: {xExpr}")
    except Exception as e:
        logger.error(f"XPath error: {e}")
    
    return result
# -------------------------------------------------------------------------
def xpath_atomic(tree, nsmap, xExpr, context=None):
    """
    Performs an xpath query either on the entire XML document
    or on a context within the document.
    Parameters:
    - tree (ElementTree): The XML tree to process.
    - xExpr (str): An xpath expression
    - context (obj)[optional]: Context object.
    If the context object is present, the xpath expression is run against
    that context. If absent, the xpath expression is run against the
    entire document.
    Returns:
    - an empty string if there is an error or if nothing is found.
    - The first result of the xpath expression as a string.
    """
    ret_value=""

    try:
        if context is None:
            logger.debug(f"XPath Atomic: {xExpr}")
            ret_value = elementpath.select(tree, xExpr, namespaces=nsmap)[0]
        else:
            logger.debug(f"XPath Atomic (Context: { context.tag }): {xExpr}")
            ret_value = elementpath.select(context, xExpr, namespaces=nsmap)[0]

    except SyntaxError as e:
        logger.error(f"XPath syntax error: {e} in {xExpr}")
    except IndexError as e:
        logger.warning(f"XPath result not found for: {xExpr}")
    except Exception as e:
        logger.error(f"Other XPath error: {e}")

    return str(ret_value)

# -------------------------------------------------------------------------
def extract_significant_nodes(tree, nsmap):
    """
    Extracts significant nodes from the XML tree.
    This function is a placeholder and should be implemented based on specific requirements.
    """
    logger.debug("Extracting significant nodes")

    content = ""
    # Example: Extract all 'define-assembly' elements
    child_elements = xpath(tree, nsmap, '/METASCHEMA/*')
    
    # Process each child element under METASCHEMA
    for assembly in child_elements:
        assembly_tag = assembly.tag.split('}')[-1]  # Remove namespace
        # logger.debug(f"Processing child:: {assembly_tag}")
        if assembly_tag not in METASCHEMA_TOP_IGNNORE:
            logger.debug(f"Adding child: {assembly_tag}")
            
            # Convert the entire element to a string
            element_str = xml_to_string(assembly)

            # logger.debug(element_str)
            content += f"{element_str}\n"
        else:
            logger.debug(f"Skipping child: {assembly_tag}")

    logger.debug(f"Extracted content: {len(content)} {str(type(content))}")
    return content
# -------------------------------------------------------------------------
"""
async def recurse_imports(tree, nsmap, support, oscal_version, content=""):
    ""Recursively assemble metaschema import statements.""
    logger.debug("Recursing imports")
    imports = xpath(tree, nsmap, '/./METASCHEMA/import/@href')
    logger.debug(f"Imports: {imports}")

    for imp_file in imports:
        if imp_file:
            logger.info(f"Processing import: {imp_file}")
            model_name = imp_file
            if model_name.startswith("oscal_"):
                model_name = model_name[len("oscal_"):]
            if model_name.endswith("_metaschema_RESOLVED.xml"):
                model_name = model_name[:-len("_metaschema_RESOLVED.xml")]

            logger.debug(f"Model name: {model_name}")
            import_content = await support.asset(oscal_version, model_name, "metaschema")
            if import_content:

                try:
                    temp_tree = deserialize_xml(import_content)
                    content += extract_significant_nodes(temp_tree, nsmap)
                    content += await recurse_imports(temp_tree, nsmap, support, oscal_version, content)
                except ElementTree.ParseError as e:
                    logger.error(f"Invalid inport {imp_file}")
                    logger.error(f"Error {e}")

    logger.debug(f"Recursed content: {len(content)} {str(type(content))}")
    return content
"""
# -------------------------------------------------------------------------
def xml_to_string(element):
    """Convert an XML element or list of elements to a string."""
    element_str = ""
    
    try:
        # Handle case where element is a list (common with xpath results)
        if isinstance(element, list):
            if len(element) > 0:
                # Take the first element if it's a list
                clean_assembly = copy.deepcopy(element[0])
                remove_namespace(clean_assembly)
                element_str = ElementTree.tostring(clean_assembly, encoding='unicode')
            else:
                # Return empty string for empty list
                return ""
        else:
            # Handle single element case
            clean_assembly = copy.deepcopy(element)
            remove_namespace(clean_assembly)
            element_str = ElementTree.tostring(clean_assembly, encoding='unicode')
    except Exception as e:
        logger.error(f"Error converting XML to string: {e}")

    return element_str

# -------------------------------------------------------------------------
def remove_namespace(element):
    """Remove namespace from an element and all its children"""
    # Remove namespace from this element
    if '}' in element.tag:
        element.tag = element.tag.split('}', 1)[1]
    
    # Process attributes
    for attr_name in list(element.attrib.keys()):
        if '}' in attr_name:
            new_name = attr_name.split('}', 1)[1]
            element.attrib[new_name] = element.attrib.pop(attr_name)
    
    # Process children
    for child in element:
        remove_namespace(child)

# -------------------------------------------------------------------------
def deserialize_xml(xml_string):
    """Deserialize an XML string into a Python dictionary."""
    ret_value = None
    try:
        # When creating the ElementTree parser
        ElementTree.register_namespace("", METASCHEMA_DEFAULT_NAMESPACE)        
        # Parse the XML string
        root = ElementTree.fromstring(xml_string)
        
        ret_value = root
    except ElementTree.ParseError as e:
        logger.error(f"Error parsing XML: {e}")

    return ret_value
# -------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MetaschemaParser:
    def __init__(self, metaschema, support, import_inventory=[]):
        logger.debug(f"Initializing MetaschemaParser")
        self.content = metaschema
        self.valid_xml = False
        self.top_level = False
        self.xml_namespace = ""
        self.oscal_version = ""
        self.oscal_model = ""
        self.schema_name = ""
        self.tree = None
        self.nsmap = {"": METASCHEMA_DEFAULT_NAMESPACE}
        self.support = support
        self.imports = [] # list of imports [{"metaschema_file_name.xml": MetaschemaParser_Object}, {}]
        self.import_inventory = import_inventory
    @classmethod
    async def create(cls, metaschema, support, import_inventory=[]):
        logger.debug(f"Creating MetaschemaParser")
        ret_value = None
        ret_value = cls(metaschema, support)
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
    async def top_pass(self):
        """Perform the first pass of parsing."""
        logger.debug("Performing top pass")

        try:
            self.tree = deserialize_xml(self.content)
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
            self.oscal_version = f"v{self.xpath_atomic("/METASCHEMA/schema-version/text()")}"

            await self.setup_imports()
            # await self.handle_imports()
        else:        
            logger.error("Invalid XML content.")

        return self.valid_xml
    # -------------------------------------------------------------------------
    async def setup_imports(self):
        """Identify import elements and set them up as import objects."""
        logger.debug("Setting up imports")
        import_directives = xpath(self.tree, self.nsmap, '/./METASCHEMA/import/@href')
        logger.debug(f"Imports: {self.imports}")

        if import_directives is not None:
            if not isinstance(import_directives, list):
                import_directives = [import_directives]

            for imp_file in import_directives:
                if imp_file:
                    logger.info(f"Processing import: {imp_file}")
                    if imp_file in self.import_inventory:
                        logger.debug(f"Import {imp_file} already processed.")
                    else:
                        logger.debug(f"Import {imp_file} not processed. Continuing ...")
                        self.import_inventory.append(imp_file)
                        model_name = imp_file
                        if model_name.startswith("oscal_"):
                            model_name = model_name[len("oscal_"):]
                        if model_name.endswith("_metaschema_RESOLVED.xml"):
                            model_name = model_name[:-len("_metaschema_RESOLVED.xml")]

                        logger.debug(f"Model name: {model_name}")
                        import_content = await self.support.asset(self.oscal_version, model_name, "metaschema")
                        if import_content:
                            import_obj = await MetaschemaParser.create(import_content, self.support, self.import_inventory)
                            status = await import_obj.top_pass()
                            if status:
                                self.imports.append({imp_file: import_obj})
                                logger.debug(f"Imports[0] for {imp_file}: {misc.iif(import_obj.top_level, "TOP", "NOT TOP")}")
                            else:
                                logger.error(f"Invalid Import file: {imp_file}")
        # logger.debug(f"IMPORTS FOR {self.oscal_model}: {self.imports}")
        # logger.debug(f"IMPORTS FOR {self.oscal_model}: {self.import_inventory}")

    # -------------------------------------------------------------------------
    """
    async def handle_imports(self):
        ""Handle import elements in the XML.""

        temp_content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        temp_content += "<METASCHEMA xmlns=\"http://csrc.nist.gov/ns/oscal/metaschema/1.0\">\n"
        temp_content += extract_significant_nodes(self.tree, self.nsmap)
        
        temp_content += await recurse_imports(self.tree, self.nsmap, self.support, self.oscal_version)
        temp_content += "</METASCHEMA>"

        # logger.debug(f"Content (BEFORE): {len(self.content)} {str(type(self.content))}")
        self.content = temp_content
        logger.debug(f"Content (AFTER): {len(self.content)} {str(type(self.content))}")

        try:
            self.tree = deserialize_xml(self.content) #  ElementTree.fromstring(self.content)
            self.valid_xml = True

        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            self.valid_xml = False        
    """

    # -------------------------------------------------------------------------
    def find(self, name, type, allow_local=True):
        """Look for a define-field, define-flag, or define-asssembly by name."""
        logger.debug(f"Finding {type} with name: {name}")
        ret_value = None
        if type == "define-field":
            ret_value = self.xpath(f"/./METASCHEMA/define-field[@name='{name}']")
        elif type == "define-flag":
            ret_value = self.xpath(f"/./METASCHEMA/define-flag[@name='{name}']")
        elif type == "define-assembly":
            ret_value = self.xpath(f"/./METASCHEMA/define-assembly[@name='{name}']")
        else:
            logger.error(f"Unknown type: {type}")

        if not ret_value:
            ret_value = self.find_in_imports(name, type)

        return ret_value


    # -------------------------------------------------------------------------
    def parse_assembly(self, assembly):
        """Parse a define-assembly element."""
        logger.debug("Parsing assembly")
        assembly_dict = {}
        assembly_dict["name"] = self.xpath_atomic("./@name", assembly)
        assembly_dict["type"] = self.xpath_atomic("./@type", assembly)
        assembly_dict["namespace"] = self.xpath_atomic("./@namespace", assembly)
        assembly_dict["json-base-uri"] = self.xpath_atomic("./@json-base-uri", assembly)
        assembly_dict["remarks"] = self.xpath_atomic("./remarks/text()", assembly)

        # Process child elements


    # -------------------------------------------------------------------------
    async def parse(self, oscal_version, oscal_models=[], parse_type=None):
        """Parse the metaschema."""
        status = False

        if parse_type is None:
            parse_type = "all"

        logger.debug(f"Parsing metaschema for version: {oscal_version}, models: {oscal_models}, type: {parse_type}")
        
        # Check if the version is supported
        if oscal_version in self.support.versions:
            # models = await self.support.enumerate_models(oscal_version)
            # if oscal_models == []:
            #     oscal_models = models
            # for oscal_model in oscal_models:
            #     if oscal_model in models:
            #         logger.info(f"Processing {oscal_version}: {oscal_model}")
            #         # Fetch the XML content
            #         model_metaschema = await self.support.asset(oscal_version, oscal_model, "metaschema")
            #         if model_metaschema:
            #             # Parse the XML content
            #             logger.debug(f"Parsing {oscal_model} metaschema.")
            #             parsed_data = self.parse_xml_to_dict(model_metaschema)
                        
            #             # Save the parsed data to a file
            #             output_file = f"{oscal_model}_FULLY_RESOLVED_metaschema.xml"
            #             with open(output_file, 'w', encoding='utf-8') as f:
            #                 json.dump(parsed_data, f, indent=2)
                        
            #             logger.info(f"Successfully created {output_file}")
            #             status = True
            #     else:
            #         logger.warning(f"OSCAL {oscal_version} does not incldue a '{oscal_model}' model.")
            pass
        else:
            logger.error(f"Unsupported OSCAL version: {oscal_version}")
        
        return status


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

        return xpath_atomic(self.tree, self.nsmap, xExpr, context)

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
        

        return xpath(self.tree, self.nsmap, xExpr, context)

    # -------------------------------------------------------------------------
    def build_metaschema_tree(self):
        """
        Build the metaschema tree.
        """
        logger.debug(f"Building metaschema tree for {self.oscal_model}")
        metaschema_tree = {}

        try:
            metaschema_tree = self.recurse_metaschema(self.oscal_model, "define-assembly")
            if metaschema_tree:
                # save to a JSON file
                output_file = f"{self.oscal_model}_FULLY_RESOLVED_metaschema.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(metaschema_tree, f, indent=2)
        except Exception as e:
            logger.error(f"Error building metaschema tree: {e}")
            metaschema_tree = {}

        return metaschema_tree
    # -------------------------------------------------------------------------
 
    def recurse_metaschema(self, name, structure_type="define-assembly", parent="", ignore_local=False, already_searched=[], context=None):
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
        logger.debug(f"{GREEN}==================== Recursing metaschema tree ====================={RESET}")
        metaschema_tree = {}

        # Check if this module was already searched
        if self.oscal_model in already_searched:
            logger.debug(f"Already searched {self.oscal_model}. Search List: {already_searched}. For {structure_type} {name}")
            return None


        if structure_type in ["field", "flag", "assembly"]:
            logger.debug(f"Recursing metaschema tree for {structure_type} {name}")
            metaschema_tree = self.recurse_metaschema(name, f"define-{structure_type}", parent) 

        # Setup xpath query
        xpath_query = f"{misc.iif(context, ".", "/METASCHEMA")}/{structure_type}"
        no_local = misc.iif(ignore_local, " and not(@scope='local')", "")
        xpath_query += f"[@{misc.iif(structure_type in ["field", "flag"], "ref", "name")}='{name}'{no_local}]"

        result = self.xpath(xpath_query, context)

    
        if result is None:
            # If nothing was found, look in the imported files
            logger.debug(f"Did not find <{structure_type} name='{name}' ... > in {self.oscal_model}")

            # cycle through each of the imported metaschema files
            # logger.debug(f"Looking in imports: {self.imports}")
            for item in self.imports:
                import_file = list(item.keys())[0]
                # Get the parser object associated with this key
                parser_object = item[import_file]
                
                logger.debug(f"Looking in {import_file}")
            
                # This will recursively search down the stack of imports. 
                # If all metaschema files are valid, the definition SHOULD be found.
                # There are some circular imports, so we need a way to break the cycle in case the definition is not found.
                already_searched.append(self.oscal_model)
                # logger.debug(f"Moving to: {parser_object}")
                metaschema_tree = parser_object.recurse_metaschema(name, structure_type, parent, ignore_local=True, already_searched=already_searched)
                if metaschema_tree:
                    break
            
            if not ignore_local: # ignore_local is only false at the top level
                logger.error(f"Did not find <{structure_type} name='{name}' ... > in {self.oscal_model} nor any imports.")
                metaschema_tree = None

        else:
            if isinstance(result, list):
                # Duplicate definitions are not allowed in metaschema, so this would only happen if the metaschema was invliad.
                logger.warning(f"Found multiple {structure_type} objects named '{name}', using the first one")
                definition_obj = result[0]
            else:
                definition_obj = result
            # A single element was found as expected
            logger.debug(f"Found: <{structure_type} name='{name}' ... >")
            # logger.debug(f"Definition object ({str(type(definition_obj))}): {xml_to_string(definition_obj)}")

            # Create the metaschema tree
            metaschema_tree["name"] = name
            metaschema_tree["use-name"] = self.xpath_atomic("./use-name/text()", definition_obj) or metaschema_tree.get("use-name", "") or metaschema_tree.get("name", "")
            if structure_type in ["define-assembly", "assembly", "define-field", "field"]:
                metaschema_tree["path"] = f"{parent}/{metaschema_tree["use-name"]}"
            elif structure_type in ["define-flag", "flag"]:
                metaschema_tree["path"] = f"{parent}/@{metaschema_tree["use-name"]}"
            metaschema_tree["structure-type"] = structure_type.replace("define-", "")

            metaschema_tree["formal-name"] = self.xpath_atomic("./formal-name/text()", definition_obj) or metaschema_tree.get("formal-name", "")
            metaschema_tree["description"] = self.xpath_atomic("./description/text()", definition_obj) or metaschema_tree.get("description", "")
            metaschema_tree["remarks"] = self.xpath_atomic("./remarks/text()", definition_obj) or metaschema_tree.get("remarks", "")
            metaschema_tree["example"] = self.xpath_atomic("./example/text()", definition_obj) or metaschema_tree.get("example", "")
            metaschema_tree["root"] = misc.iif(parent == "", True, False)
            metaschema_tree["json-key"] = self.xpath_atomic("./json-key/text()", definition_obj) or metaschema_tree.get("", "")
            metaschema_tree["json-value-key"] = self.xpath_atomic("./json-value-key/text()", definition_obj) or metaschema_tree.get("", "")
            metaschema_tree["json-value-key-flag"] = self.xpath_atomic("./json-value-key-flag/text()", definition_obj) or metaschema_tree.get("", "")

            if definition_obj.attrib:
                for attr_name, attr_value in definition_obj.attrib.items():
                    match attr_name:
                        case "name":
                            # Skip the name attribute as it's already used in the metaschema tree
                            pass
                        case "as-type":
                            metaschema_tree["datatype"] = attr_value
                        case "scope":
                            metaschema_tree["scope"] = attr_value
                        case "required":
                            if attr_value == "yes":
                                metaschema_tree["min-occurs"] = "1"
                                metaschema_tree["max-occurs"] = "1"
                            else:
                                metaschema_tree["min-occurs"] = "0" 
                                metaschema_tree["max-occurs"] = "1" 
                        case "min-occurs":
                            metaschema_tree["min-occurs"] = attr_value
                        case "max-occurs":
                            metaschema_tree["max-occurs"] = attr_value
                        case "collapsible":
                            if attr_value == "yes":
                                metaschema_tree["json-collapsible"] = True
                            else:
                                metaschema_tree["json-collapsible"] = False
                            logger.debug(f"Collapsible: {metaschema_tree['collapsible']}")
                        case "deprecated":
                            if compare_semver(attr_value, self.oscal_version) <= 0:
                                metaschema_tree["deprecated"] = True
                            else:
                                metaschema_tree["sunsetting"] = attr_value
                        case "default":
                            if structure_type in ["define-field", "define-flag"]:
                                metaschema_tree["default"] = attr_value
                            else:
                                logger.warning(f"Unexpected attribute: <define-{structure_type} name='{name}' {attr_name}='{attr_value}'")
                        case "in-xml":
                            if structure_type in ["define-field", "field"]:
                                metaschema_tree["in-xml"] = attr_value
                            else:
                                logger.warning(f"Unexpected attribute: <define-{structure_type} name='{name}' {attr_name}='{attr_value}'")
                        case _:
                            logger.warning(f"Unknown attribute: <define-{structure_type} name='{name}' {attr_name}='{attr_value}'")
                    # Remove namespace if present
                    logger.debug(f"Attribute: {attr_name} = {attr_value}")
                
            # For any attribute that is not present, set the default defined in the spec
            if not metaschema_tree.get("datatype") :
                metaschema_tree["datatype"] = "string"
            if not metaschema_tree.get("scope"):
                metaschema_tree["scope"] = "global"

            if metaschema_tree.get("root"):
                metaschema_tree["min-occurs"] = "1"
                metaschema_tree["max-occurs"] = "1"

            if not metaschema_tree.get("min-occurs"):
                metaschema_tree["min-occurs"] = "0"
            if not metaschema_tree.get("max-occurs"):
                metaschema_tree["max-occurs"] = "unbounded"
            if not metaschema_tree.get("json-collapsible"):
                metaschema_tree["json-collapsible"] = False
            if not metaschema_tree.get("deprecated"):
                metaschema_tree["deprecated"] = False
            if not metaschema_tree.get("default"):
                metaschema_tree["default"] = None

            if structure_type in ["define-field", "field"] and not metaschema_tree.get("in-xml"):
                metaschema_tree["in-xml"] = "WRAPPED"

            if "source" in metaschema_tree:
                metaschema_tree["source"].append(self.oscal_model)
            else:
                metaschema_tree["source"] = [self.oscal_model]


            # Handle Flags defined or referenced in the Field or Assembly
            if structure_type in ["define-assembly", "assembly", "define-field", "field"]:
                temp_flags = self.xpath(f"./(define-flag | flag)", definition_obj)

                if temp_flags is not None:
                    metaschema_tree["flags"] = []
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
                            meta_object = self.recurse_metaschema(flag_name, flag_structure_type, metaschema_tree["path"], ignore_local=True, context=definition_obj)
                            if meta_object:
                                metaschema_tree["flags"].append(meta_object)
                else:
                    logger.debug(f"No flags found within {structure_type} {name}")
            
            # Handle Group As defined in fields and assemblies
            # if structure_type in ["define-assembly", "assembly", "define-field", "field"]:
            #     logger.debug(f"Looking for group-as in {structure_type} {name}")
            #     temp_group_as = self.xpath(f"./group-as", definition_obj)
            #     if temp_group_as is not None:
            #         if temp_group_as.attrib:
            #             logger.debug(f"Has attributes.")
            #             metaschema_tree["group-as"] = temp_group_as.attrib.get("name", "")
            #             if "in-json" in temp_group_as.attrib:
            #                 metaschema_tree["group-as-in-json"] = temp_group_as.attrib.get("in-json")
            #             if "in-xml" in temp_group_as.attrib:
            #                 metaschema_tree["group-as-in-xml"] = temp_group_as.attrib.get("in-json")

                # TODO: Handle group-as <<<<====---- ****
                # TODO: Handle group-as <<<<====---- ****
                # TODO: Handle group-as <<<<====---- ****
                
            # Handle model specification for defined assemblies
            # Handle model specification for defined assemblies
            # Handle model specification for defined assemblies
            if structure_type == "define-assembly":
                temp_children = self.xpath(f"./model/*", definition_obj)  

                # If a model is defined, we need to process it
                if temp_children is not None:
                    metaschema_tree["children"] = []
                    if not isinstance(temp_children, list):
                        temp_children = [temp_children]

                    # Loop through each child element
                    for child in temp_children:
                        child_structure_type = child.tag.split('}')[-1]  # Remove namespace
                        child_name = ""
                        if "ref" in child.attrib:
                            child_name = child.attrib['ref']
                        elif "name" in child.attrib:
                            child_name = child.attrib['name']
                        else:
                            logger.error (f"Child: {child_structure_type} contains neither @name nor @ref")
                        
                        logger.debug(f"Child: {child_structure_type} name: {child_name}")

                        if child_structure_type in ["define-assembly", "define-field"]:
                            child_context = self.xpath(f"./model", definition_obj)
                        else:
                            child_context = definition_obj

                        if child_context is None:
                            logger.error(f"Child context is None for {child_structure_type} {child_name}")

                        if child_name:
                            meta_object = self.recurse_metaschema(child_name, child_structure_type, parent=metaschema_tree["path"], ignore_local=False, context=child_context, already_searched=[])
                            if meta_object:
                                metaschema_tree["children"].append(meta_object)
                else:
                    logger.debug(f"No model found within {structure_type} {name}")

        if not metaschema_tree:
            logger.error(f"Did not find {structure_type} object: {name}")
            metaschema_tree = None


        return metaschema_tree


# -------------------------------------------------------------------------
def get_attribute_value(element, attribute_name, default=""):
    """
    Get the value of a specific attribute from an XML element.
    
    Args:
        element: The XML element to check
        attribute_name: The name of the attribute to look for
        default: The value to return if the attribute doesn't exist (default: empty string)
        
    Returns:
        The attribute value or the default value if the attribute doesn't exist
    """
    # Handle namespace prefixes if needed
    if '}' in attribute_name:
        clean_name = attribute_name.split('}', 1)[1]
    else:
        clean_name = attribute_name
        
    # Get the value with a default of empty string
    return element.get(clean_name, default)
# -------------------------------------------------------------------------

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
                    
                    # Save the parsed data to a file
                    # output_file = f"{model}_FULLY_RESOLVED_metaschema.xml"
                    
                    # logger.info(f"Successfully created {output_file}")
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


    try:
        exit_code = asyncio.run(main())
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
