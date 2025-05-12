import xml.etree.ElementTree as ET
import json
import urllib.request
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaschemaParser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.namespace = {'ms': 'http://csrc.nist.gov/ns/oscal/metaschema/1.0'}
        self.processed_files = set()

    def fetch_xml_content(self, url):
        """Fetch XML content from URL."""
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

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

    def parse(self):
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

def main():
    base_url = "https://github.com/usnistgov/OSCAL/releases/download/v1.1.3/oscal_complete_metaschema_RESOLVED.xml"
    
    parser = MetaschemaParser(base_url)
    result = parser.parse()
    
    if result:
        # Save to file
        with open('metaschema_complete.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        logger.info("Successfully created metaschema_complete.json")
    else:
        logger.error("Failed to parse metaschema")

if __name__ == "__main__":
    main()
