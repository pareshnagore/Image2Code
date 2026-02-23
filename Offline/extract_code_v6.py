import easyocr
import numpy as np
import cv2
import sys
from pathlib import Path


# Initialize OCR reader once
reader = easyocr.Reader(['en'], gpu=False)


def extract_code(image_path):

    # Load image
    img = cv2.imread(image_path)

    if img is None:
        raise Exception("Could not load image")

    # Run OCR with bounding boxes
    results = reader.readtext(img, detail=1, paragraph=False)

    if not results:
        return ""

    # Sort by vertical position (top to bottom)
    results.sort(key=lambda x: min(pt[1] for pt in x[0]))

    # Determine left margin reference
    min_x = min(min(pt[0] for pt in r[0]) for r in results)

    indent_scale = 4  # pixels per indent level (adjustable)

    lines = []

    for bbox, text, conf in results:

        # Skip very low confidence garbage
        if conf < 0.30:
            continue

        x = min(pt[0] for pt in bbox)

        indent_level = int((x - min_x) / 20)

        indent = "    " * indent_level

        line = indent + text

        lines.append(line)

    return "\n".join(lines)


def save_code(code, output_path):

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)


def main():

    if len(sys.argv) < 2:
        print("Usage: python extract_code_v6.py image.jpg")
        return

    image_path = sys.argv[1]

    output_path = Path(image_path).stem + "_v6.py"

    print("Extracting code...")

    code = extract_code(image_path)

    save_code(code, output_path)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()