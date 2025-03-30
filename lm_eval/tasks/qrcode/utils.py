import os
import tempfile
import uuid
from io import BytesIO
from typing import Dict, Any, List

import numpy as np
import xml.etree.ElementTree as ET
from PIL import Image
import cairosvg
import datasets

# Install pyzbar if not already installed
try:
    from pyzbar.pyzbar import decode
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzbar"])
    from pyzbar.pyzbar import decode

def get_text_from_doc(doc: Dict[str, Any]) -> str:
    """
    Generate prompt text from a document.
    """
    return f"Please generate an SVG file containing a QR code that encodes the following text: {doc.get('input_text', '')}"

def get_target_from_doc(doc: Dict[str, Any]) -> str:
    """
    Get target from a document.
    """
    return doc.get('svg_output', '')

def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    """
    Process the dataset to ensure it has the expected format.
    """
    def _process_doc(doc):
        # If it's already in the right format, return as is
        if 'input_text' in doc and 'svg_output' in doc:
            return doc
            
        # For datasets loaded with different structures
        # Extract what we need and reformat
        processed_doc = {}
        
        # Try to find the relevant fields
        for key, value in doc.items():
            if key in ['input_text', 'input']:
                processed_doc['input_text'] = value
            elif key in ['svg_output', 'output', 'target']:
                processed_doc['svg_output'] = value
        
        # If we couldn't find the expected fields, use defaults
        if 'input_text' not in processed_doc:
            processed_doc['input_text'] = doc.get(list(doc.keys())[0], "")
        if 'svg_output' not in processed_doc:
            processed_doc['svg_output'] = ""
            
        return processed_doc

    return dataset.map(_process_doc)

def is_valid_svg(svg_content: str) -> bool:
    """
    Check if the model output is valid SVG by trying to parse it as XML.
    """
    try:
        # Check if the content contains SVG tags
        if not ("<svg" in svg_content and "</svg>" in svg_content):
            return False
            
        # Extract the SVG content (in case there's additional text)
        svg_start = svg_content.find("<svg")
        svg_end = svg_content.find("</svg>", svg_start) + 6
        svg_content = svg_content[svg_start:svg_end]
        
        # Try to parse as XML
        ET.fromstring(svg_content)
        return True
    except ET.ParseError:
        return False
    except Exception:
        return False

def decode_qr_from_svg(svg_content: str) -> str:
    """
    Convert the SVG to a PNG image, then decode the QR code.
    Returns the decoded text or an empty string if decoding fails.
    """
    try:
        # Extract the SVG content (in case there's additional text)
        svg_start = svg_content.find("<svg")
        svg_end = svg_content.find("</svg>", svg_start) + 6
        svg_content = svg_content[svg_start:svg_end]
        
        # Convert SVG to PNG using cairosvg
        png_data = BytesIO()
        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=png_data)
        png_data.seek(0)
        
        # Open the image and decode the QR code
        img = Image.open(png_data)
        decoded_objects = decode(img)
        
        if decoded_objects:
            # Return the decoded text from the first QR code found
            return decoded_objects[0].data.decode('utf-8')
        else:
            return ""
    except Exception as e:
        print(f"Error decoding QR code: {e}")
        return ""

def qrcode_accuracy(samples: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the accuracy of the QR code generation.
    A successful generation means the decoded QR code matches the original input text.
    """
    correct = 0
    total = 0
    
    for sample in samples:
        input_text = sample.get("doc", {}).get("input_text", "")
        generation = sample.get("prediction", "")
        
        if not input_text or not generation:
            continue
            
        total += 1
        
        # Skip if not a valid SVG
        if not is_valid_svg(generation):
            continue
            
        # Decode the QR code
        decoded_text = decode_qr_from_svg(generation)
        
        # Check if the decoded text matches the input
        if decoded_text == input_text:
            correct += 1
    
    return {
        "qrcode_accuracy": float(correct) / float(total) if total > 0 else 0.0
    }

def svg_validity(samples: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the percentage of outputs that are valid SVG files.
    """
    valid_count = 0
    total = 0
    
    for sample in samples:
        generation = sample.get("prediction", "")
        
        if not generation:
            continue
            
        total += 1
        if is_valid_svg(generation):
            valid_count += 1
    
    return {
        "svg_validity": float(valid_count) / float(total) if total > 0 else 0.0
    }
