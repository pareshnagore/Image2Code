from typing import List
from pathlib import Path
from core.models import ImageBlock
from core.extractor import ExtractionResult, ImageExtractor
from core.timestamp import get_image_timestamp
from core.grouping import BlockGrouper, BlockGroup
from core.ordering import BlockOrderer
from core.reconstruction import CodeReconstructor


class CodeExtractionPipeline:
    """
    Core pipeline orchestrating extraction, grouping, ordering,
    and reconstruction of code from multiple images.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug

    def _log(self, msg: str):
        if self.debug:
            print(f"[PIPELINE] {msg}")

    def extract_blocks(self, image_paths: List[Path]) -> List[ImageBlock]:
        """
        Step 1: Extract structured blocks from each image using LLM.
        """

        blocks: List[ImageBlock] = []

        self._log(f"Extracting: {image_paths}")

        extractor = ImageExtractor()
        extraction: ExtractionResult = extractor.extract_from_images(image_paths)

        # for image_path in image_paths:

        #     self._log(f"Extracting: {image_path}")

        #     extractor = ImageExtractor()
        #     extraction: ExtractionResult = extractor.extract_from_images(image_path)

        #     timestamp = extract_timestamp(image_path)

        #     block = ImageBlock(
        #         image_path=image_path,
        #         timestamp=timestamp,
        #         extraction=extraction
        #     )

        #     blocks.append(block)

        self._log(f"Extracted {len(extraction.blocks)} blocks")

        return extraction.blocks

    def group_blocks(self, blocks: List[ImageBlock]):
        """
        Step 2: Group blocks belonging to same file/script/notebook
        """
        groups = BlockGrouper().group(blocks)
        self._log(f"Created {len(groups)} groups")
        return groups

    # def order_blocks(self, groups):
    #     """
    #     Step 3: Order blocks correctly within each group
    #     """
    #     ordered_groups = []
    #     for group in groups:
    #         ordered = BlockOrderer().order(group)
    #         ordered_groups.append(ordered)
    #     self._log("Ordering complete")
    #     return ordered_groups
    
    def order_blocks(self, blocks: List[ImageBlock]) -> List[ImageBlock]:
        ordered = BlockOrderer().order(blocks)
        self._log("Ordering complete")
        return ordered

    # def reconstruct(self, ordered_groups):
    #     """
    #     Step 4: Reconstruct final files from ordered blocks
    #     """
    #     results = []
    #     for ordered in ordered_groups:
    #         result = CodeReconstructor().reconstruct(ordered)
    #         results.append(result)
    #     self._log("Reconstruction complete")
    #     return results
    
    def reconstruct(self, ordered_blocks: List[ImageBlock]):
        result = CodeReconstructor().reconstruct(ordered_blocks)
        self._log("Reconstruction complete")
        return result

    def run(self, image_paths: List[Path]):
        """
        Full pipeline execution.
        """
        if not image_paths:
            raise ValueError("No image paths provided")
        self._log("Starting pipeline")
        blocks = self.extract_blocks(image_paths)
        # groups = self.group_blocks(blocks)
        # ordered_groups = self.order_blocks(groups)
        # results = self.reconstruct(ordered_groups)
        print(blocks)
        ordered_blocks = self.order_blocks(blocks)
        results = self.reconstruct(ordered_blocks)

        self._log("Pipeline complete")
        return results