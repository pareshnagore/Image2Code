import easyocr
import cv2
import numpy as np
import sys
import os


# ---------- CONFIG ----------
LANGUAGE = "python"   # change later if needed
OUTPUT_FILE = "output.py"

# IDE noise keywords to ignore
NOISE_WORDS = [
    "Terminal", "Window", "Help",
    "Ln", "Col", "Spaces", "UTF-8",
    "MacBook", "Paresh", "Agent_ng",
]


# ---------- LOAD OCR ----------
print("Loading OCR model...")
reader = easyocr.Reader(['en'], gpu=False)


# ---------- READ IMAGE ----------
def load_image(path):
    img = cv2.imread(path)

    if img is None:
        raise Exception("Could not load image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    return gray


# ---------- FILTER NOISE ----------
def is_noise(text):
    text = text.strip()

    if text == "":
        return True

    for word in NOISE_WORDS:
        if word in text:
            return True

    return False


# ---------- GROUP INTO LINES ----------
def group_lines(results, y_threshold=12):

    boxes = []

    for bbox, text, conf in results:

        if conf < 0.30:
            continue

        if is_noise(text):
            continue

        x = int(bbox[0][0])
        y = int(bbox[0][1])

        boxes.append((x, y, text))

    # sort by Y first, then X
    boxes.sort(key=lambda b: (b[1], b[0]))

    lines = []
    current_line = []
    current_y = None

    for x, y, text in boxes:

        if current_y is None:
            current_y = y
            current_line = [(x, text)]
            continue

        if abs(y - current_y) <= y_threshold:
            current_line.append((x, text))
        else:
            lines.append(current_line)
            current_line = [(x, text)]
            current_y = y

    if current_line:
        lines.append(current_line)

    return lines


# ---------- REBUILD TEXT ----------
def rebuild_text(lines):

    output_lines = []

    for line in lines:

        line.sort(key=lambda item: item[0])

        line_text = ""
        last_x = 0

        for x, text in line:

            spaces = int((x - last_x) / 8)

            if spaces > 0:
                line_text += " " * spaces

            line_text += text
            last_x = x + len(text) * 8

        output_lines.append(line_text)

    return "\n".join(output_lines)


# ---------- MAIN ----------
def extract_code(image_path):

    img = load_image(image_path)

    print("Running OCR...")
    results = reader.readtext(img)

    lines = group_lines(results)

    code = rebuild_text(lines)

    return code


# ---------- ENTRY ----------
if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python extract_code_v5.py image.jpg")
        sys.exit()

    image_path = sys.argv[1]

    code = extract_code(image_path)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(code)

    print("\nSaved to:", OUTPUT_FILE)