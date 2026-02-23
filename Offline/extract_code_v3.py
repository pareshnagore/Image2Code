import sys
import os
import easyocr
import cv2
import numpy as np


# -------------------------
# CONFIG
# -------------------------

LANGUAGE_EXTENSION = {
    "python": ".py",
    "javascript": ".js",
    "java": ".java",
    "cpp": ".cpp",
    "c": ".c",
    "txt": ".txt"
}


# -------------------------
# IMAGE PREPROCESSING
# (same as v1 benchmark)
# -------------------------

def preprocess_image(image_path):

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    return thresh


# -------------------------
# OCR EXTRACTION
# -------------------------

def extract_text(image):

    reader = easyocr.Reader(['en'], gpu=False)

    results = reader.readtext(image, detail=0)

    return results


# -------------------------
# WRITE CODE FILE
# -------------------------

def write_code_file(lines, language, output_name=None):

    ext = LANGUAGE_EXTENSION.get(language.lower(), ".txt")

    if output_name is None:
        output_name = "output" + ext
    else:
        if not output_name.endswith(ext):
            output_name += ext

    with open(output_name, "w", encoding="utf-8") as f:

        for line in lines:
            f.write(line)
            f.write("\n")

    return output_name


# -------------------------
# MAIN
# -------------------------

def main():

    if len(sys.argv) < 3:
        print("Usage:")
        print("python extract_code_v3.py <image_path> <language> [output_name]")
        return

    image_path = sys.argv[1]
    language = sys.argv[2]

    output_name = None

    if len(sys.argv) >= 4:
        output_name = sys.argv[3]

    print("Preprocessing image...")
    processed = preprocess_image(image_path)

    print("Running OCR...")
    lines = extract_text(processed)

    print("Writing code file...")
    filename = write_code_file(lines, language, output_name)

    print(f"\nSaved to: {filename}")


if __name__ == "__main__":
    main()