import base64
import json
import os, sys
from pathlib import Path
from typing import List, Optional
from unittest import result
import ollama
from core.models import ImageBlock
from core.timestamp import get_image_timestamp, to_epoch_seconds
from dotenv import load_dotenv
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
  "format": "ipynb | py | js | html | cpp | json | yaml | txt",
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


class ExtractionResult:
    def __init__(self):
        self.blocks: List[ImageBlock] = []
        self.failed_images: List[Path] = []

    def add_block(self, block: ImageBlock):
        self.blocks.append(block)

    def add_failure(self, path: Path):
        self.failed_images.append(path)


class ImageExtractor:
    def __init__(
        self,
        model: str = MODEL,
        temperature: float = 0,
        top_p: float = 0.0,
        top_k: int = 1,
        repeat_penalty: float = 1.0,
        seed: int = 42,
        num_predict: int = 4096,
        num_ctx: int = 8192
    ):
        self.model = model
        self.options = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "seed": seed,
            "num_predict": num_predict,
            "num_ctx": num_ctx
        }
        self.client = ollama.Client(
            host=os.getenv("OLLAMA_CLOUD_HOST", OLLAMA_HOST),
            headers={
                "Authorization": f"Bearer {os.getenv('OLLAMA_API_KEY')}"
            }
        )

    # ----------------------------
    # Utilities
    # ----------------------------

    def _encode_image(self, path: Path) -> str:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    def _get_timestamp(self, path: Path):
        try:
            return path.stat().st_mtime
        except Exception:
            return None

    # ----------------------------
    # LLM Extraction
    # ----------------------------

    def _extract_llm(self, image_path: Path) -> Optional[dict]:
        prompt = PROMPT.strip()
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_path],
                    }
                ],
                options=self.options,
                format="json"
            )

            return response["message"]["content"]
            # return json.loads(text)

        except Exception as e:
            print(f"LLM extraction failed: {image_path} : {e}")
            return None

    # ----------------------------
    # Public extraction functions
    # ----------------------------

    def extract_from_image(self, image_path: Path) -> Optional[ImageBlock]:
        response_text = self._extract_llm(image_path)
        if not response_text:
            return None
        try:
            # Sometimes model wraps JSON in ```json ```
            if "```" in response_text:
                response_text = response_text.split("```")[1] # type: ignore
                response_text = response_text.replace("json", "", 1).strip()
            data = json.loads(response_text) # type: ignore
            timestamp = to_epoch_seconds(get_image_timestamp(str(image_path)))
            block = ImageBlock(
                image_path= str(image_path),
                format = data.get("format", "txt"),
                language = data.get("language", "text"),
                filename = data.get("filename", ""),
                start_line = data.get("start_line", None),
                end_line = data.get("end_line", None),
                total_lines=data.get("total_lines", None),
                is_notebook=data.get("is_notebook", False),
                timestamp=timestamp,
                cells = data.get("cells", []),
                code = "\n".join(cell["content"] for cell in data.get("cells", []))
            )
            return block
        except:
            # fallback if model returns raw code
            code_str = json.dumps(response_text) if isinstance(response_text, dict) else (response_text if response_text else "")
            return ImageBlock(
                image_path=str(image_path),
                format="txt",
                language="text",
                filename="",
                start_line=None,
                end_line=None,
                total_lines=None,
                is_notebook=False,
                timestamp=to_epoch_seconds(get_image_timestamp(str(image_path))),  
                code=code_str
            )

    def extract_from_images(self, image_paths: List[Path]) -> ExtractionResult:
        extraction = ExtractionResult()
        for path in image_paths:
            block = self.extract_from_image(path)
            if block:
                extraction.add_block(block)
            else:
                extraction.add_failure(path)
        return extraction