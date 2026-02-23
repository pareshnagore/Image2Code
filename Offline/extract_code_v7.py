import easyocr
import cv2
import sys
import os

# IDE noise words to ignore
NOISE_WORDS = {
    "Terminal", "Window", "Help", "MacBook", "Air",
    "Ln", "Col", "Spaces", "UTF-8", "LF"
}

# Tunable parameters
LINE_VERTICAL_THRESHOLD = 12   # pixels
INDENT_SPACES_PER_LEVEL = 4
INDENT_PIXEL_WIDTH = 40


def load_image_safe(path):
    if not os.path.exists(path):
        print("ERROR: File not found")
        sys.exit(1)

    img = cv2.imread(path)

    if img is None:
        print("ERROR: Failed to load image")
        sys.exit(1)

    print(f"Loaded image: {img.shape[1]}x{img.shape[0]}")
    return img


def is_noise(text):
    t = text.strip()
    if t in NOISE_WORDS:
        return True

    if len(t) <= 1 and not t.isalnum():
        return True

    return False


def group_into_lines(results):
    """
    Groups OCR words into lines based on vertical position.
    """
    items = []

    for (bbox, text, conf) in results:

        if conf < 0.30:
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

    # sort by vertical position
    items.sort(key=lambda i: i["y"])

    lines = []
    current_line = []
    current_y = None

    for item in items:

        if current_y is None:
            current_line.append(item)
            current_y = item["y"]
            continue

        if abs(item["y"] - current_y) <= LINE_VERTICAL_THRESHOLD:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]
            current_y = item["y"]

    if current_line:
        lines.append(current_line)

    return lines


def reconstruct_code(lines):

    code_lines = []

    for line in lines:

        # sort words left-to-right
        line.sort(key=lambda i: i["x"])

        first_x = line[0]["x"]

        indent_level = int(first_x / INDENT_PIXEL_WIDTH)

        indent = " " * (indent_level * INDENT_SPACES_PER_LEVEL)

        text = " ".join(word["text"] for word in line)

        code_lines.append(indent + text)

    return "\n".join(code_lines)


def extract_code(image_path, output_path):

    image = load_image_safe(image_path)

    print("Loading OCR model...")
    reader = easyocr.Reader(['en'], gpu=False)

    print("Running OCR...")
    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,
        batch_size=1
    )

    lines = group_into_lines(results)

    code = reconstruct_code(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"\nSaved to {output_path}")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage:")
        print("python extract_code_v7.py image.jpg output.py")
        sys.exit(1)

    image_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = "output_v7.py"

    extract_code(image_path, output_path)