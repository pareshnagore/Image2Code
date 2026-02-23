import easyocr
import cv2
import sys
from pathlib import Path


def extract_code(image_path):

    if not Path(image_path).exists():
        raise Exception("Image file does not exist")

    img = cv2.imread(image_path)

    if img is None:
        raise Exception("OpenCV failed to load image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    reader = easyocr.Reader(['en'], gpu=False)

    results = reader.readtext(gray, detail=0, paragraph=True)

    return "\n".join(results)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python extract_code.py image.png")
        sys.exit(1)

    image_path = sys.argv[1]

    code = extract_code(image_path)

    print("\nExtracted Code:\n")
    print(code)