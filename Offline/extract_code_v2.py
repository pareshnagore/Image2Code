import easyocr
import sys
import cv2
from pathlib import Path
from image_preprocess_v2 import preprocess_for_code


def extract_code(image_path):

    if not Path(image_path).exists():
        raise Exception("Image not found")

    print("Preprocessing image...")
    processed = preprocess_for_code(image_path, debug=True)

    print("Loading OCR model...")
    reader = easyocr.Reader(
        ['en'],
        gpu=False,
        verbose=False
    )

    print("Running OCR...")

    # detail=1 gives bounding boxes
    results = reader.readtext(
        processed,
        detail=1,
        paragraph=False,
        contrast_ths=0.1,
        adjust_contrast=0.5,
        text_threshold=0.5,
        low_text=0.2
    )

    # Sort lines by vertical position
    results_sorted = sorted(results, key=lambda x: x[0][0][1])

    lines = []

    for bbox, text, confidence in results_sorted:

        if confidence > 0.3:  # filter noise
            lines.append(text)

    code = "\n".join(lines)

    return code


def save_output(code, output_file="output_v2.txt"):

    with open(output_file, "w") as f:
        f.write(code)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python extract_code_v2.py image.png")
        sys.exit(1)

    image_path = sys.argv[1]

    code = extract_code(image_path)

    print("\nExtracted Code:\n")
    print(code)

    save_output(code)

    print("\nSaved to output_v2.txt")