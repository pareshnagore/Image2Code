test_single_image py
8 Set USE_TESSERACT-True to use Tesseract instead of EasyOCR (try if output is gibberish) _
9
10
11 import 05
12 from main import run workflow
13
14 # Edit these to test
15 IMAGE_PATH Images/20260221_195444.jpg
16 OUTPUT_DIR "output"
17 USE_TESSERACT False # True Tesseract, False EasyOCR (default, better for screenshots)
18
19 if name_ main __
20 if not 0S.path.isfile( IMAGE_PATH) :
21 print(f"Error: Image not found: {IMAGE_PATH}"
22 exit(1)
23
24 output_name 05 . path. splitext (0s.path.basename IMAGE_PATH) [0]
25 result run workflow
26 [IMAGE_PATH]
27 output_dir-OUTPUT_DIR,
28 Language_override-None,
29 output_filename-output_name,
30 use_easyocr-not USE_TESSERACT ,
31
32 if result: