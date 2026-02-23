import cv2
import numpy as np


def preprocess_for_code(image_path, debug=False):

    img = cv2.imread(image_path)

    if img is None:
        raise Exception("Failed to load image")

    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale (VERY important)
    gray = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # Mild denoise (not aggressive)
    gray = cv2.fastNlMeansDenoising(
        gray,
        None,
        h=10,
        templateWindowSize=7,
        searchWindowSize=21
    )

    # Contrast enhancement using CLAHE (best for dark IDE)
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    if debug:
        cv2.imwrite("debug_processed_v3.png", enhanced)

    return enhanced