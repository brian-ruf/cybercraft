import os
import fnmatch
import argparse
from xml.etree import ElementTree as ET
from xml.dom import minidom
from pathlib import Path

def generate_qrc(root_dir, output_qrc, exclude_patterns=None):
    """
    Generate a Qt resource collection file (.qrc) with a single qresource element.
    Only includes files in subdirectories, not in the root directory.
    
    Args:
        root_dir (str): The root directory containing the resources
        output_qrc (str): The output .qrc file path
        exclude_patterns (list): Optional list of glob patterns to exclude
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate input parameters
        if not root_dir:
            raise ValueError("Root directory path cannot be empty")
        if not output_qrc:
            raise ValueError("Output .qrc file path cannot be empty")
            
        # Convert to Path objects for better path handling
        root_path = Path(root_dir).resolve()
        output_path = Path(output_qrc)
        
        # Check if root directory exists
        if not root_path.exists():
            raise FileNotFoundError(f"Root directory does not exist: {root_path}")
        if not root_path.is_dir():
            raise NotADirectoryError(f"Specified path is not a directory: {root_path}")
            
        # Set default exclude patterns if none provided
        if exclude_patterns is None:
            exclude_patterns = []
            
        # Create the root element and single qresource element
        rcc = ET.Element('RCC')
        qresource = ET.SubElement(rcc, 'qresource', prefix='/')
        
        def should_exclude(path):
            relative_path = os.path.relpath(path, root_path).replace('\\', '/')
            return any(fnmatch.fnmatch(relative_path, pattern) for pattern in exclude_patterns)
        
        def get_sorted_items(directory):
            try:
                items = os.listdir(directory)
                items = [item for item in items if not should_exclude(os.path.join(directory, item))]
                return sorted(items, key=lambda x: (not os.path.isdir(os.path.join(directory, x)), x.lower()))
            except PermissionError as e:
                print(f"Warning: Permission denied accessing directory: {directory}")
                return []
            except OSError as e:
                print(f"Warning: Error accessing directory {directory}: {e}")
                return []
        
        def process_directory(current_dir, is_root=False):
            items = get_sorted_items(current_dir)
            
            for item in items:
                full_path = os.path.join(current_dir, item)
                if os.path.isdir(full_path):
                    # Process subdirectories
                    process_directory(full_path, is_root=False)
                elif not is_root:  # Only process files if not in root directory
                    try:
                        # Add file to the single qresource element
                        file_element = ET.SubElement(qresource, 'file')
                        # Create relative path from root
                        rel_path = os.path.relpath(full_path, root_path).replace('\\', '/')
                        file_element.text = rel_path
                    except OSError as e:
                        print(f"Warning: Error processing file {full_path}: {e}")
        
        # Start the recursive processing from root directory
        process_directory(str(root_path), is_root=True)
        
        # Convert to string with minidom for pretty formatting
        rough_string = ET.tostring(rcc, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        
        # Remove empty lines that minidom sometimes generates
        pretty_lines = [line for line in pretty_xml.splitlines() if line.strip()]
        pretty_xml = '\n'.join(pretty_lines) + '\n'
        
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            print(f"Successfully generated {output_path}")
            return True
        except IOError as e:
            print(f"Error writing output file {output_path}: {e}")
            return False
            
    except ValueError as e:
        print(f"Invalid input: {e}")
        return False
    except FileNotFoundError as e:
        print(f"Directory not found: {e}")
        return False
    except NotADirectoryError as e:
        print(f"Not a directory: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Generate Qt resource collection file (.qrc)')
    parser.add_argument('--input', '-i', default='.',
                      help='Input resource directory (default: current directory)')
    parser.add_argument('--output', '-o', default='resources.qrc',
                      help='Output .qrc file (default: resources.qrc)')
    args = parser.parse_args()

    # Default exclusion patterns
    exclude_patterns = [
        '*.pyc',
        '__pycache__/*',
        '__pycache__',
        '.git/*',
        '.git*',
        '.DS_Store',
        'thumbs.db',
        '*.bak',
        'temp/*',
        '*.tmp',
        '*.bat',
        '*.py'
    ]
    
    try:
        success = generate_qrc(args.input, args.output, exclude_patterns)
        if not success:
            print("Failed to generate .qrc file")
    except Exception as e:
        print(f"Error running script: {e}")
