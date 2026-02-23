import easyocr
import cv2
import sys
import os

# Noise words commonly from IDE UI
NOISE_WORDS = {
    "Terminal", "Window", "Help",
    "MacBook", "Air",
    "Ln", "Col", "Spaces", "UTF-8", "LF"
}

VERTICAL_THRESHOLD = 10
CONF_THRESHOLD = 0.30
SPACES_PER_INDENT = 4


def load_image(path):

    if not os.path.exists(path):
        print("File not found")
        sys.exit(1)

    img = cv2.imread(path)

    if img is None:
        print("Failed to load image")
        sys.exit(1)

    return img


def is_noise(text):

    t = text.strip()

    if t in NOISE_WORDS:
        return True

    if len(t) == 0:
        return True

    return False


def group_lines(results):

    items = []

    for bbox, text, conf in results:

        if conf < CONF_THRESHOLD:
            continue

        if is_noise(text):
            continue

        x = bbox[0][0]
        y = bbox[0][1]

        items.append({
            "text": text,
            "x": x,
            "y": y
        })

    if not items:
        return []

    # sort top-to-bottom
    items.sort(key=lambda i: i["y"])

    lines = []
    current_line = []
    base_y = items[0]["y"]

    for item in items:

        if abs(item["y"] - base_y) <= VERTICAL_THRESHOLD:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]
            base_y = item["y"]

    if current_line:
        lines.append(current_line)

    return lines


def reconstruct_code(lines):

    if not lines:
        return ""

    # Find global minimum x
    min_x = min(word["x"] for line in lines for word in line)

    code_lines = []

    for line in lines:

        # sort left-to-right
        line.sort(key=lambda w: w["x"])

        first_x = line[0]["x"]

        # relative indentation
        indent_pixels = first_x - min_x

        indent_level = int(indent_pixels / 25)

        indent = " " * (indent_level * SPACES_PER_INDENT)

        text = " ".join(word["text"] for word in line)

        code_lines.append(indent + text)

    return "\n".join(code_lines)


def extract_code(image_path, output_path):

    print("Loading image...")
    image = load_image(image_path)

    print("Loading OCR model...")
    reader = easyocr.Reader(['en'], gpu=False)

    print("Running OCR...")
    results = reader.readtext(
        image,
        detail=1,
        paragraph=False
    )

    lines = group_lines(results)

    code = reconstruct_code(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Usage:")
        print("python extract_code_v8.py image.jpg output.py")
        sys.exit(1)

    image_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = "output_v8.py"

    extract_code(image_path, output_path)