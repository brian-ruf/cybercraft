import asyncio
import sys
# import json
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

OSCAL_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"
METASCHEMA_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/metaschema/1.0"
METASCHEMA_TOP_IGNNORE = ["schema-name", "schema-version", "short-name", "namespace", "json-base-uri", "remarks", "import"]
METASCHEMA_TOP_KEEP = ["define-assembly", "define-field", "define-flag", "constraint"]
METASCHEMA_ROOT_ELEMENT = "METASCHEMA"
CONSTRAINT_ROOT_ELEMENT = "metaschema-meta-constraints"
CONSTRAINT_TOP_IGNORE = []
CONSTRAINT_TOP_KEEP = ["context"]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    - 
    """
    
    ret_value=None
    if context is None:
        logger.debug("XPath [1]: " + xExpr)
        ret_value = elementpath.select(tree, xExpr, namespaces=nsmap)
    else:
        logger.debug("XPath [1] (" + context.tag + "): " + xExpr)
        ret_value = elementpath.select(context, xExpr, namespaces=nsmap)
    logger.debug(str(type(ret_value)))
    return ret_value
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
async def recurse_imports(tree, nsmap, support, oscal_version, content=""):
    """Recursively assemble metaschema import statements."""
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
# -------------------------------------------------------------------------
def xml_to_string(element):
    """Convert an XML element to a string."""
    element_str = ""
    
    try:
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
        ret_value += f"XML Namespace: {self.xml_namespace}\n"
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
        logger.debug(f"{self.oscal_model}: {misc.iif(self.top_level, "TOP", "NOT TOP")}")

    # -------------------------------------------------------------------------
    async def handle_imports(self):
        """Handle import elements in the XML."""

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


    # -------------------------------------------------------------------------
    def find_here(self, name, type, allow_local=True):
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
    def find_in_imports(self, name, type):
        """Look for a define-field, define-flag, or define-asssembly by name in the imports."""
        logger.debug(f"Finding {type} with name: {name} in imports")
        ret_value = None
        for imp in self.imports:
            if type == "define-field":
                ret_value = imp.xpath(f"/./METASCHEMA/define-field[@name='{name}']")
            elif type == "define-flag":
                ret_value = imp.xpath(f"/./METASCHEMA/define-flag[@name='{name}']")
            elif type == "define-assembly":
                ret_value = imp.xpath(f"/./METASCHEMA/define-assembly[@name='{name}']")
            else:
                logger.error(f"Unknown type: {type}")

            if ret_value:
                break

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
        ret_value=""

        try:
            if context is None:
                logger.debug("XPath [1]: " + xExpr)
                ret_value = elementpath.select(self.tree, xExpr, namespaces=self.nsmap)[0]
            else:
                logger.debug("XPath [1] (" + context.tag + "): " + xExpr)
                ret_value = elementpath.select(context, xExpr, namespaces=self.nsmap)[0]

        except SyntaxError as e:
            logger.error(f"XPath syntax error: {e} in {xExpr}")
        except IndexError as e:
            logger.warning(f"XPath result not found: {e}")
        except Exception as e:
            logger.error(f"Other XPath error: {e}")

        return str(ret_value)

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
        - 
        """
        

        return xpath(self.tree, self.nsmap, xExpr, context)

    # -------------------------------------------------------------------------
    def build_metaschema_tree(self):
        """
        Build the metaschema tree.
        """
        logger.debug("Building metaschema tree")
        metaschema_tree = {}

        try:
            metaschema_tree = recurse_metaschema(self.tree, self.nsmap, self.oscal_model)
        except Exception as e:
            logger.error(f"Error building metaschema tree: {e}")
            metaschema_tree = {}

        return metaschema_tree
    # -------------------------------------------------------------------------
 


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
                        logger.debug(f"Parsed data: {parser}")
                    else:
                        logger.error("Failed to parse the XML content.")
                    
                    # Save the parsed data to a file
                    output_file = f"{model}_FULLY_RESOLVED_metaschema.xml"
                    
                    logger.info(f"Successfully created {output_file}")
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
