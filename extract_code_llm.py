import ollama
import sys
import os
import base64
from PIL import Image
from dotenv import load_dotenv
import json

load_dotenv()

MODEL = "qwen3-vl:235b-cloud"
OLLAMA_HOST = "http://localhost:11434"  # Change if Ollama is on different host/port

PROMPT = """
You are a precise OCR engine specialized in extracting source code.

Your task:
1. Extract ONLY the source code from the image.
2. Identify the programming language
3. Identify the output file format using language and code structure (e.g. if it's Python code, save as .py; if it's HTML, save as .html, if it's python code but looks like a notebook, save as .ipynb, etc.)
4. Identify file name if it is visible in the image (e.g. from an ACTIVE IDE tab) and use it for output file naming.


Special handling for Jupyter notebooks:
- Extract only code cells
- Ignore outputs
- Ignore execution numbers
- Do NOT merge cells
- Preserve separate cells exactly including markdown cells if they are present
- Ensure valid notebook structure with "cells" array


STRICT RULES FOR FILENAME DETECTION:

1. ONLY use the ACTIVE tab (highlighted / brighter tab)
2. NEVER use background tabs
3. NEVER invent filenames
4. If filename NOT visible, use empty string ""

STRICT RULES FOR FORMAT DETECTION:

Priority order:
1. Filename extension from ACTIVE tab (highest priority), if confidence of active tab detection is high (>80% confidence), else move to next priority
2. Syntax visible in code (lowest priority)

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
  "format": "ipynb | python | javascript | html | cpp | json | yaml | text",
  "language": "python | javascript | cpp | html | ...",
  "filename": "optional_filename"  # include if filename is visible in the image, otherwise omit
  "line_numbers_visible": true,
  "start_line": 1,
  "end_line": 50,
  "total_lines": 50,
  "is_notebook": false,
  "cells": [
    {
      "type": "code | markdown",
      "content": "exact code or markdown for this cell",
      "start_line": 1,
      "end_line": 10
    },
  ]
}


ADDITIONAL REQUIRED METADATA FOR MULTI-IMAGE RECONSTRUCTION:

The output JSON MUST also include these fields:

{
  "tab_name": "exact visible ACTIVE tab name or empty string",
  "line_numbers_visible": true or false,
  "start_line": integer if line numbers visible, else null,
  "end_line": integer if line numbers visible, else null,
  "total_lines": integer count of lines visible in this image,
  "is_notebook": true or false
}

RULES:

- start_line and end_line MUST be exact numbers if visible
- NEVER guess line numbers
- If line numbers not visible, use null
- total_lines MUST count only actual code lines extracted
- tab_name MUST match exactly visible active tab text
- These fields are REQUIRED even if null
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
            "temperature": 0.0,
            "top_p": 0.0,
            "top_k": 1,
            "repeat_penalty": 1.0,
            "seed": 42,
            "num_predict": 4096,
            "num_ctx": 8192
        },
        format="json"
    )

    return response['message']['content']

def parse_response(response_text):
    try:
        # Sometimes model wraps JSON in ```json ```
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            response_text = response_text.replace("json", "", 1).strip()
        data = json.loads(response_text)
        # format_type = data.get("format", "python")
        # language = data.get("language", "python")
        # filename = data.get("filename", "")
        # cells = data.get("cells", [])
        return data
    except:
        # fallback if model returns raw code
        return {
            "language": "python",
            "format": "py",
            "code": response_text
        }
    
def save_as_ipynb(cells, output_file):
    notebook = {
        "cells": [],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5
    }
    for cell in cells:
        notebook["cells"].append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": cell["content"].splitlines(keepends=True)
        })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

# def save_as_ipynb(code, output_file):
#     notebook = {
#         "cells": [
#             {
#                 "cell_type": "code",
#                 "execution_count": None,
#                 "metadata": {},
#                 "outputs": [],
#                 "source": code.splitlines(keepends=True)
#             }
#         ],
#         "metadata": {},
#         "nbformat": 4,
#         "nbformat_minor": 5
#     } 
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(notebook, f, indent=2)

def save_output(code, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)

def save_as_code(cells, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for i, cell in enumerate(cells):
            f.write(cell["content"])
            if i != len(cells) - 1:
                f.write("\n")

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

    print(f"Extracting code using {MODEL}...........")

    response = extract_code(image_path)
    print("Raw response from model:")
    print(response)
    print("\nParsing response..........................")
    parsed = parse_response(response)

    format_ext = parsed.get("format", "python")
    language = parsed.get("language", "python")
    filename_from_image = parsed.get("filename", "")
    cells = parsed.get("cells", [])

    # language = parsed["language"].lower()
    # format_ext = parsed["format"].lower()
    # code = parsed["code"]
    # filename_from_image = parsed.get("filename")
    if filename_from_image:
        filename = filename_from_image.lower()
    else: 
        filename = name.lower()+"." + format_ext

    # choose correct extension
    output_file = f"outputs/{filename}"

    if format_ext == "ipynb":
        save_as_ipynb(cells, output_file)
    else:
        save_as_code(cells, output_file)

    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()