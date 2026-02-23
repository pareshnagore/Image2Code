import cv2
import sys

img = cv2.imread(sys.argv[1])

if img is None:
    print("Image failed to load")
else:
    print("Image loaded:", img.shape)