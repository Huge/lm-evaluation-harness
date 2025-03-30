#!/usr/bin/env python
# QR Code Generation Evaluation Script
# This script evaluates an LLM's ability to generate valid QR codes in SVG format

from io import BytesIO
import json
import os
import time
import xml.etree.ElementTree as ET

from PIL import Image
import cairosvg
import requests

# Install pyzbar if not already installed
try:
    from pyzbar.pyzbar import decode
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyzbar"])
    from pyzbar.pyzbar import decode

# Test Strings for QR Code Generation
TEST_STRINGS = [
    "Hello World",
    "https://example.com",
    "12345",
    "Lorem ipsum dolor sit amet",
    "https://github.com/EleutherAI/lm-evaluation-harness",
    "QR Code Test",
    "OpenAI GPT-4",
    "Cascade AI Assistant",
    "user@example.com",
    "Tel: +1-123-456-7890"
]

# Configuration
MODEL = os.getenv("MODEL", "deepseek/deepseek-chat-v3-0324:free")
API_KEY = os.getenv("API_KEY", "sk-or-v1-aaaaaaa")
BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

def create_prompt(input_text):
    """Create a prompt for the model"""
    return [
        {"role": "system", "content": "You are a helpful assistant that generates valid SVG QR codes."},
        {"role": "user", "content": f"Please generate an SVG file containing a QR code that encodes the following text: {input_text}. Return only the SVG code."}
    ]

def generate_qr_code(input_text):
    """Generate a QR code for the given input text using the model"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": MODEL,
        "messages": create_prompt(input_text),
        "max_tokens": 4096
    }
    
    try:
        response = requests.post(BASE_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling API: {e}")
        return None

def is_valid_svg(svg_content):
    """Check if the model output is valid SVG"""
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

def decode_qr_from_svg(svg_content):
    """Decode the QR code from SVG content"""
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

def save_svg_to_file(svg_content, filename):
    """Save SVG content to a file"""
    try:
        # Extract the SVG content
        svg_start = svg_content.find("<svg")
        svg_end = svg_content.find("</svg>", svg_start) + 6
        svg_content = svg_content[svg_start:svg_end]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        return True
    except Exception as e:
        print(f"Error saving SVG: {e}")
        return False

def main():
    """Main evaluation function"""
    print(f"QR Code Generation Evaluation")
    print(f"Model: {MODEL}")
    print(f"Evaluating on {len(TEST_STRINGS)} test strings")
    print(f"===============================")
    
    results = []
    valid_count = 0
    correct_count = 0
    
    # Create output directory for SVGs
    os.makedirs("qr_outputs", exist_ok=True)
    
    for i, input_text in enumerate(TEST_STRINGS):
        print(f"[{i+1}/{len(TEST_STRINGS)}] Testing: {input_text}")
        
        # Generate QR code
        svg_content = generate_qr_code(input_text)
        if not svg_content:
            print("  ❌ Failed to generate output")
            results.append({
                "input_text": input_text,
                "valid_svg": False,
                "decoded_text": None,
                "is_correct": False
            })
            continue
        
        # Check SVG validity
        is_valid = is_valid_svg(svg_content)
        if is_valid:
            valid_count += 1
            print("  ✅ SVG is valid")
        else:
            print("  ❌ SVG is invalid")
            results.append({
                "input_text": input_text,
                "valid_svg": False,
                "decoded_text": None,
                "is_correct": False
            })
            continue
        
        # Decode QR code
        decoded_text = decode_qr_from_svg(svg_content)
        if decoded_text:
            print(f"  Decoded: '{decoded_text}'")
        else:
            print("  ❌ Failed to decode QR code")
            
        # Check if decoded text matches input
        is_correct = decoded_text == input_text
        if is_correct:
            correct_count += 1
            print("  ✅ Content matches")
        else:
            print("  ❌ Content does not match")
            
        # Save the SVG file
        filename = f"qr_outputs/qr_{i+1:02d}_{input_text.replace(' ', '_').replace('://', '_').replace('/', '_')[:30]}.svg"
        save_svg_to_file(svg_content, filename)
        print(f"  💾 Saved to {filename}")
        
        results.append({
            "input_text": input_text,
            "valid_svg": is_valid,
            "decoded_text": decoded_text,
            "is_correct": is_correct
        })
        
        # Add a delay to avoid rate limiting
        time.sleep(2)
    
    # Calculate metrics
    total = len(TEST_STRINGS)
    svg_validity_rate = valid_count / total
    qr_accuracy_rate = correct_count / total
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Total tests: {total}")
    print(f"Valid SVGs: {valid_count}/{total} ({svg_validity_rate:.2%})")
    print(f"Correct QR codes: {correct_count}/{total} ({qr_accuracy_rate:.2%})")
    
    # Save results to file
    report = {
        "model": MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {
            "svg_validity": svg_validity_rate,
            "qr_accuracy": qr_accuracy_rate
        },
        "results": results
    }
    
    with open("qr_evaluation_results.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Generate a human-readable report
    with open("qr_evaluation_report.md", "w") as f:
        f.write(f"# QR Code Generation Evaluation Report\n\n")
        f.write(f"**Model:** {MODEL}  \n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
        
        f.write(f"## Metrics\n\n")
        f.write(f"- **SVG Validity Rate:** {valid_count}/{total} ({svg_validity_rate:.2%})\n")
        f.write(f"- **QR Code Accuracy:** {correct_count}/{total} ({qr_accuracy_rate:.2%})\n\n")
        
        f.write(f"## Test Results\n\n")
        f.write(f"| # | Input Text | Valid SVG | Decoded Text | Match |\n")
        f.write(f"|---|-----------|-----------|--------------|-------|\n")
        
        for i, result in enumerate(results):
            input_text = result["input_text"]
            valid_svg = "✅" if result["valid_svg"] else "❌"
            decoded_text = result["decoded_text"] if result["decoded_text"] else "N/A"
            is_correct = "✅" if result["is_correct"] else "❌"
            
            f.write(f"| {i+1} | {input_text} | {valid_svg} | {decoded_text} | {is_correct} |\n")
    
    print(f"Results saved to qr_evaluation_results.json")
    print(f"Report saved to qr_evaluation_report.md")

if __name__ == "__main__":
    main()
