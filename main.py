import sys
import os
from pathlib import Path
from core.pipeline import CodeExtractionPipeline
from core.logger import get_logger, initialize_logger

logger = get_logger(__name__)

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
            logger.debug(f"Single image collected | path: {path}")
            return [path]
        else:
            logger.error(f"File is not a supported image | path: {path} | supported: {SUPPORTED_IMAGE_EXTENSIONS}")
            raise ValueError("File is not a supported image")

    elif os.path.isdir(path):
        images = []
        for file in sorted(os.listdir(path)):
            if file.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                images.append(os.path.join(path, file))

        if not images:
            logger.error(f"No images found in directory | path: {path}")
            raise ValueError("No images found in directory")

        logger.info(f"Images collected from directory | path: {path} | count: {len(images)}")
        return images

    else:
        logger.error(f"Invalid path | path: {path}")
        raise ValueError("Invalid path")


def save_output(result, output_dir="outputs"):
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = result['filename'] or f"reconstructed.{result['format']}"
        output_path = os.path.join(output_dir, filename)
        
        logger.debug(f"Saving output | format: {result['format']} | filename: {filename}")
        
        if result['format'] == "ipynb":
            import json
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result['content'], f, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result['content'])
        
        logger.info(f"Output saved successfully | path: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save output | path: {output_path} | error: {str(e)}") # type: ignore
        raise


def main():
    # Initialize logger at application startup
    initialize_logger()
    
    logger.info("="*60)
    logger.info("Code Extraction Pipeline Started")
    logger.info(f"Arguments: {sys.argv[1:]}")
    
    if len(sys.argv) < 2:
        logger.error("No input path provided")
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
        
        logger.info(f"Found {len(image_paths)} image(s) to process")
        
        pipeline = CodeExtractionPipeline(debug=True)
        logger.info("Pipeline initialized | starting extraction")
        
        result = pipeline.run([Path(p) for p in image_paths])
        
        logger.debug(f"Pipeline completed | result type: {type(result)}")
        
        output_path = save_output(result)
        logger.info(f"Reconstruction complete | saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed | error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()