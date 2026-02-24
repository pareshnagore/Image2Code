import sys
import os
from pathlib import Path
from core.pipeline import CodeExtractionPipeline

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

def collect_images_from_path(path: str):
    """
    Accepts either:
    - single image
    - directory containing images
    Returns ordered list of image paths (filesystem order only)
    """
    if os.path.isfile(path):
        if path.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
            return [path]
        else:
            raise ValueError("File is not a supported image")

    elif os.path.isdir(path):
        images = []
        for file in sorted(os.listdir(path)):
            if file.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                images.append(os.path.join(path, file))

        if not images:
            raise ValueError("No images found in directory")

        return images

    else:
        raise ValueError("Invalid path")


def save_output(result, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    filename = result['filename'] or f"reconstructed.{result['format']}"
    output_path = os.path.join(output_dir, filename)
    if result['format'] == "ipynb":
        import json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result['content'], f, indent=2)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result['content'])
    return output_path


def main():
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("python main.py <image_or_directory>")
        print("\nExamples:")
        print("python main.py image1.jpg")
        print("python main.py ./images_folder/\n")
        return
    input_paths = sys.argv[1:]
    image_paths = []
   

    try:
        for path in input_paths:
            image_paths.extend(collect_images_from_path(path))
        # image_paths = collect_images_from_path(input_path)
        print(f"\nFound {len(image_paths)} image(s)")
        pipeline = CodeExtractionPipeline(debug=True)
        result = pipeline.run([Path(p) for p in image_paths])
        print(type(result))
        print(result)
        output_path = save_output(result)
        print(f"\nReconstruction complete")
        print(f"Saved to: {output_path}")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()