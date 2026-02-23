import ollama
import sys
import os
import base64
from PIL import Image
from dotenv import load_dotenv
import json

load_dotenv()


# MODEL = "qwen3-vl:8b"   # change to 4b if needed
MODEL = "qwen3-vl:235b-cloud"
# MODEL = "gemma3:27b-cloud"
OLLAMA_HOST = "http://localhost:11434"  # Change if Ollama is on different host/port

PROMPT = """
You are a precise OCR engine specialized in extracting source code.

Your task:
1. Extract ONLY the source code from the image.
2. Identify the programming language
3. Identify the output file format using language and code structure (e.g. if it's Python code, save as .py; if it's HTML, save as .html, if it's python code but looks like a notebook, save as .ipynb, etc.)
4. Identify file name if it is visible in the image (e.g. from an IDE tab) and use it for output file naming.


Special handling for Jupyter notebooks:
- Extract only code cells
- Ignore outputs
- Ignore execution numbers
- Do NOT merge cells
- Preserve separate cells exactly including markdown cells if they are present
- Ensure valid notebook structure with "cells" array

CRITICAL RULES:

1. Output ONLY code
2. Do NOT explain anything
3. Do NOT add comments
4. Do NOT fix or modify code
5. Do NOT hallucinate missing parts
6. Preserve exact indentation
7. Preserve exact symbols
8. Preserve exact variable names
9. Ignore IDE UI elements
10. Preserve line breaks, comments, etc. as they are in the image


OUTPUT FORMAT (STRICT JSON):

{
  "language": "python",
  "format": "py",
  "code": "full code here exactly",
  "filename": "optional_filename.py"  # include if filename is visible in the image, otherwise omit
}
"""


def extract_code(image_path):
    # Read and encode image as base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    client = ollama.Client(
        host=os.getenv("OLLAMA_CLOUD_HOST", OLLAMA_HOST),
        headers={
            "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"
        }
    )

    response = client.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": PROMPT,
                "images": [image_path]
            }
        ],
        options={
            "temperature": 0.0
        }
    )

    return response['message']['content']


def parse_response(response_text):
    try:
        data = json.loads(response_text)
        return data
    except:
        # fallback if model returns raw code
        return {
            "language": "python",
            "format": "py",
            "code": response_text
        }

def save_as_ipynb(code, output_file):
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code.splitlines(keepends=True)
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)


def save_output(code, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("python extract_code_llm.py image.jpg")
        return

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print("Image not found")
        return

    filename = os.path.basename(image_path)
    name = os.path.splitext(filename)[0]

    output_file = f"outputs/{name}.py"

    print("Extracting code using Qwen3-VL...")

    response = extract_code(image_path)
    parsed = parse_response(response)
    language = parsed["language"].lower()
    format_ext = parsed["format"].lower()
    code = parsed["code"]
    filename_from_image = parsed.get("filename")
    if filename_from_image:
        filename = filename_from_image.lower()
    else: 
        filename = name.lower()

    # choose correct extension
    output_file = f"outputs/{filename}.{format_ext}"

    if format_ext == "ipynb":
        save_as_ipynb(code, output_file)
    else:
        save_output(code, output_file)

    print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()