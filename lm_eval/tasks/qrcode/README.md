# QR Code Generation Evaluation Task

This task evaluates an LLM's ability to generate valid QR codes in SVG format. It measures how often the model outputs a valid SVG-encoded QR code that decodes back to the correct text.

## Overview

The evaluation process follows these steps:

1. **Data Preparation**: A list of text strings is used as input for QR code generation.
2. **Prompt Construction**: For each input text, a prompt instructs the LLM to generate an SVG file containing a QR code that encodes the given text.
3. **Model Interaction**: The prompt is sent to the LLM, which should output an SVG string encoding the requested text.
4. **Validity Checks**:
   - Parse as SVG: Checks that the LLM output is valid XML/SVG.
   - Decode the QR Code: Converts the SVG to an image and extracts the decoded text.
5. **Comparison**: If the decoded text matches the original prompt text, then the test is a "pass."
6. **Report Metrics**: Computes the percentage of passes and valid SVG outputs.

## Metrics

- **qrcode_accuracy**: Percentage of generated QR codes that decode to the correct input text.
- **svg_validity**: Percentage of outputs that are valid SVG files.

## Dependencies

This task requires the following Python packages:
- pyzbar (for QR code decoding)
- cairosvg (for SVG to PNG conversion)
- PIL/Pillow (for image processing)

The task will attempt to install missing dependencies automatically.

## Example Usage

```bash
python main.py \
  --model openai \
  --model_args model=gpt-4 \
  --tasks qrcode \
  --num_fewshot 0
```

## Notes

- Models with strong visual and code generation capabilities are expected to perform better on this task.
- The QR code standard supports different error correction levels, but this evaluation does not specify any particular level.
- The task measures both the ability to generate valid SVG and the correctness of the QR code encoding.
