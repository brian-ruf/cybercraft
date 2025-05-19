import asyncio
import sys
# import xml.etree.ElementTree as ET
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

OSCAL_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/1.0"
METASCHEMA_DEFAULT_NAMESPACE = "http://csrc.nist.gov/ns/oscal/metaschema/1.0"

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
def recurse_imports(tree, nsmap, support, oscal_version, content=""):
    """Handle import elements in the XML."""
    logger.debug("Handling imports")
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
            import_content = support.asset(oscal_version, model_name, "metaschema")
            if import_content:
                content += import_content

            try:
                temp_tree = ElementTree.fromstring(import_content)
                content += recurse_imports(temp_tree, nsmap, support, oscal_version)
                
            except ElementTree.ParseError as e:
                logger.error(f"Invalid inport {imp_file}")
                logger.error(f"Error {e}")

    return content
# -------------------------------------------------------------------------

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class MetaschemaParser:
    def __init__(self, metaschema, support):
        logger.debug(f"Initializing MetaschemaParser")
        self.content = metaschema
        self.valid_xml = False
        self.xml_namespace = ""
        self.oscal_version = ""
        self.oscal_model = ""
        self.schema_name = ""
        self.tree = None
        self.nsmap = {"": METASCHEMA_DEFAULT_NAMESPACE}
        self.support = support

    @classmethod
    async def create(cls, metaschema, support):
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
    def top_pass(self):
        """Perform the first pass of parsing."""
        logger.debug("Performing top pass")

        try:
            self.tree = ElementTree.fromstring(self.content)
            self.valid_xml = True
        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            self.valid_xml = False

        if self.valid_xml:
            self.oscal_model = self.xpath_atomic("/./METASCHEMA/define-assembly/root-name/text()")
            self.schema_name = self.xpath_atomic("/./METASCHEMA/schema-name/text()")
            self.oscal_version = self.xpath_atomic("/./METASCHEMA/schema-version/text()")

            self.handle_imports()
        else:        
            logger.error("Invalid XML content.")

        return self.valid_xml
    # -------------------------------------------------------------------------
    def handle_imports(self):
        """Handle import elements in the XML."""

        self.content  = recurse_imports(self.tree, self.nsmap, self.support, self.oscal_version)
        try:
            self.tree = ElementTree.fromstring(self.content)
            self.valid_xml = True
        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            self.valid_xml = False        


    # -------------------------------------------------------------------------

    def fetch_xml_content(self, url):
        """Fetch XML content from URL."""
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    # -------------------------------------------------------------------------
    def parse_xml_to_dict(self, element):
        """Convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = dict(element.attrib)
        
        # Add text content if it exists and is not just whitespace
        if element.text and element.text.strip():
            result['#text'] = element.text.strip()
        
        # Process child elements
        for child in element:
            child_tag = child.tag.split('}')[-1]  # Remove namespace
            child_dict = self.parse_xml_to_dict(child)
            
            if child_tag in result:
                if not isinstance(result[child_tag], list):
                    result[child_tag] = [result[child_tag]]
                result[child_tag].append(child_dict)
            else:
                result[child_tag] = child_dict
        
        return result

    # -------------------------------------------------------------------------
    def process_imports(self, element, current_url):
        """Process import elements recursively."""
        result = self.parse_xml_to_dict(element)
        
        # Handle imports
        imports = element.findall('.//ms:import', self.namespace)
        for imp in imports:
            href = imp.get('href')
            if href:
                import_url = urljoin(current_url, href)
                
                if import_url not in self.processed_files:
                    logger.info(f"Processing import: {import_url}")
                    self.processed_files.add(import_url)
                    
                    # Fetch and parse imported content
                    imported_content = self.fetch_xml_content(import_url)
                    if imported_content:
                        imported_tree = ET.fromstring(imported_content)
                        imported_dict = self.process_imports(imported_tree, import_url)
                        
                        # Merge imported content
                        self.merge_dict(result, imported_dict)
        
        return result

    # -------------------------------------------------------------------------
    def merge_dict(self, target, source):
        """Merge source dictionary into target dictionary."""
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], list):
                    if isinstance(value, list):
                        target[key].extend(value)
                    else:
                        target[key].append(value)
                else:
                    if isinstance(value, list):
                        target[key] = [target[key]] + value
                    else:
                        target[key] = [target[key], value]
            else:
                target[key] = value

    # -------------------------------------------------------------------------
    def _parse(self):
        """Main parsing function."""
        try:
            # Fetch initial content
            content = self.fetch_xml_content(self.base_url)
            if not content:
                return None
            
            # Parse initial XML
            root = ET.fromstring(content)
            
            # Process the entire tree including imports
            result = self.process_imports(root, self.base_url)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing metaschema: {e}")
            return None
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    def parse_metaschema(self, oscal_version, metaschema, parse_type):
        """Parse the metaschema."""
        logger.debug(f"Parsing metaschema for version: {oscal_version}, type: {parse_type}")

        pass
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
        if context is None:
            logger.debug("XPath [1]: " + xExpr)
            ret_value = elementpath.select(self.tree, xExpr, namespaces=self.nsmap)[0]
        else:
            logger.debug("XPath [1] (" + context.tag + "): " + xExpr)
            ret_value = elementpath.select(context, xExpr, namespaces=self.nsmap)[0]

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
    def serializer(self):
        logger.debug("Serializing for Output")
        ElementTree.indent(self.tree)
        out_string = ElementTree.tostring(self.tree, 'utf-8')
        logger.debug("LEN: " + str(len(out_string)))
        out_string = misc.normalize_content(out_string)
        out_string = out_string.replace("ns0:", "")
        out_string = out_string.replace(":ns0", "")
        
        return out_string
    
    # -------------------------------------------------------------------------
    def lookup(self, xExpr: str, attributes: list=[], children: list=[]):
        """
        Checks for the existence of an element based on an xpath expression.
        Returns a dict containing any of the following if available: id, uuid, title
        If aditional attributes or children are specified in the function call
        and found to be present, they are included in the dict as well. 
        Parameters:
        - xExpr (str): xpath expression. This should always evaluate to 0 or 1 nodes
        - attributes(list)[Optional]: a list of additional attributes to return
        - children(list)[Optional]: a list of additional children to return

        Return:
        - dict or None
        dict = {
           {'attribute/field name', 'value'},
           {'attribute/field name', 'value'}        
        }
        """
        ret_value = None
        target_node = self.xpath(xExpr)
        if target_node:
            ret_value = {}
            if 'id' in target_node.attrib:
                ret_value.append({"id", target_node.get("id")})
            if 'uuid' in target_node.attrib:
                ret_value.append({"uuid", target_node.get("uuid")})

            title = target_node.find('./title', self.nsmap)
            if title:
                ret_value.append({"title", title.text})

            for attribute in attributes:
                ret_value.append({attribute, target_node.get(attribute)})

            for child in children:
                child_node = target_node.find('./' + child, self.nsmap)
                if child_node:
                    ret_value.append({child, child_node.text})


        return ret_value


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
                    status = parser.top_pass()

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
