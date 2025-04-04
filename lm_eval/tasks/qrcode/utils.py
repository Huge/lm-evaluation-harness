import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Any, Dict, List, Optional, Union

import cairosvg
import datasets
from PIL import Image


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
    Handles both single inputs and multiple validation cases.
    """
    # Handle single input case
    if "input_text" in doc and isinstance(doc["input_text"], str):
        return f"Please generate an SVG file containing a QR code that encodes the following text: {doc['input_text']}"

    # Fallback for other cases
    return f"Please generate an SVG file containing a QR code that encodes the following text: {doc.get('input_text', '')}"


def get_target_from_doc(doc: Dict[str, Any]) -> str:
    """
    Get target from a document.
    """
    return doc.get("svg_output", "")


def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    """
    Process the dataset to ensure it has the expected format.
    Handles both single documents and validation cases.
    """

    def _process_doc(doc):
        # If it's a validation set, process each case individually
        if "validation" in doc:
            return [
                {"input_text": case["input_text"], "svg_output": case["svg_output"]}
                for case in doc["validation"]
            ]

        # If it's already in the right format, return as is
        if "input_text" in doc and "svg_output" in doc:
            return doc

        # For datasets loaded with different structures
        processed_doc = {}
        for key, value in doc.items():
            if key in ["input_text", "input"]:
                processed_doc["input_text"] = value
            elif key in ["svg_output", "output", "target"]:
                processed_doc["svg_output"] = value

        # Defaults if fields not found
        if "input_text" not in processed_doc:
            processed_doc["input_text"] = doc.get(list(doc.keys())[0], "")
        if "svg_output" not in processed_doc:
            processed_doc["svg_output"] = ""

        return processed_doc

    # Process each document individually
    processed = []
    for doc in dataset:
        result = _process_doc(doc)
        if isinstance(result, list):
            processed.extend(result)
        else:
            processed.append(result)

    return datasets.Dataset.from_list(processed)


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
        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=png_data)
        png_data.seek(0)

        # Open the image and decode the QR code
        img = Image.open(png_data)
        decoded_objects = decode(img)

        if decoded_objects:
            # Return the decoded text from the first QR code found
            return decoded_objects[0].data.decode("utf-8")
        else:
            return ""
    except Exception as e:
        print(f"Error decoding QR code: {e}")
        return ""


def qrcode_accuracy(
    predictions: List[str], references: List[str], **kwargs
) -> Dict[str, float]:
    """
    Calculate the accuracy of the QR code generation.
    A successful generation means the decoded QR code matches the original input text.
    """
    correct = 0
    total = 0

    for i, generation in enumerate(predictions):
        input_text = references[i]

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

    return {"qrcode_accuracy": float(correct) / float(total) if total > 0 else 0.0}


def svg_validity(
    samples: Union[List[Dict[str, Any]], List[str]],
    references: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Calculate the percentage of outputs that are valid SVG files.

    Args:
        samples: List of samples, either as dictionaries with 'prediction' key
                 or as direct list of predictions
        references: Optional list of reference texts (not used in this metric)

    Returns:
        Dictionary with SVG validity percentage
    """
    valid_count = 0
    total = 0

    # Handle different input types
    for sample in samples:
        # If sample is a dictionary, get the prediction
        if isinstance(sample, dict):
            generation = sample.get("prediction", "")
        # If sample is a string, use it directly
        elif isinstance(sample, str):
            generation = sample
        else:
            continue

        if not generation:
            continue

        total += 1

        if is_valid_svg(generation):
            valid_count += 1

    return {"svg_validity": float(valid_count) / float(total) if total > 0 else 0.0}
