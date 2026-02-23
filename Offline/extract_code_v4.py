import sys
import easyocr
import os
import cv2


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

INDENT_SPACES = 4


# -------------------------
# OCR WITH BOUNDING BOXES
# -------------------------

def extract_with_boxes(image_path):

    reader = easyocr.Reader(['en'], gpu=False)

    # results = reader.readtext(
    #     image_path,
    #     detail=1,
    #     paragraph=False
    # )
    image = load_image_safe(image_path)
    cv2.imwrite("debug_input.png", image)

    results = reader.readtext(
        image,
        detail=1,
        paragraph=False,
        batch_size=1
    )

    lines = []

    for bbox, text, confidence in results:

        if text.strip() == "":
            continue

        x = bbox[0][0]
        y = bbox[0][1]

        lines.append({
            "text": text,
            "x": x,
            "y": y
        })

    return lines


# -------------------------
# SORT AND RECONSTRUCT
# -------------------------

def reconstruct_indentation(lines):

    # Sort by vertical position
    lines.sort(key=lambda l: l["y"])

    # Find leftmost position
    min_x = min(line["x"] for line in lines)

    # Estimate indent unit
    x_positions = sorted(set(line["x"] for line in lines))

    if len(x_positions) > 1:
        indent_unit = min(
            x_positions[i+1] - x_positions[i]
            for i in range(len(x_positions)-1)
            if x_positions[i+1] - x_positions[i] > 2
        )
    else:
        indent_unit = 20  # fallback default

    reconstructed = []

    for line in lines:

        indent_level = round((line["x"] - min_x) / indent_unit)

        indent = " " * (indent_level * INDENT_SPACES)

        reconstructed.append(indent + line["text"])

    return reconstructed


# -------------------------
# WRITE FILE
# -------------------------

def write_code_file(lines, language, output_name=None):

    ext = LANGUAGE_EXTENSION.get(language.lower(), ".txt")

    if output_name is None:
        output_name = "output_v4" + ext
    else:
        if not output_name.endswith(ext):
            output_name += ext

    with open(output_name, "w", encoding="utf-8") as f:

        for line in lines:
            f.write(line)
            f.write("\n")

    return output_name


def load_image_safe(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    img = cv2.imread(path)

    if img is None:
        print("ERROR: OpenCV failed to load image")
        sys.exit(1)

    h, w = img.shape[:2]

    if h == 0 or w == 0:
        print("ERROR: Image has zero size")
        sys.exit(1)

    print(f"Loaded image: {w}x{h}")
    return img

# -------------------------
# MAIN
# -------------------------

def main():

    if len(sys.argv) < 3:
        print("Usage:")
        print("python extract_code_v4.py <image_path> <language> [output_name]")
        return

    image_path = sys.argv[1]
    language = sys.argv[2]

    output_name = None

    if len(sys.argv) >= 4:
        output_name = sys.argv[3]

    print("Running OCR with bounding boxes...")

    lines = extract_with_boxes(image_path)

    print("Reconstructing indentation...")

    reconstructed = reconstruct_indentation(lines)

    print("Writing code file...")

    filename = write_code_file(
        reconstructed,
        language,
        output_name
    )

    print(f"\nSaved to: {filename}")


if __name__ == "__main__":
    main()