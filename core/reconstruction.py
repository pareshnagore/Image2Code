# reconstruction.py

from typing import List, Dict, Any
import json

from core.models import ImageBlock
from core.logger import get_logger

logger = get_logger(__name__)


class CodeReconstructor:
    """
    Reconstructs final code file from ordered ImageBlocks.

    Responsibilities:
    - merge blocks
    - remove duplicate overlaps
    - preserve exact code
    - reconstruct notebook cells
    """

    # ============================================================
    # PUBLIC ENTRY POINT
    # ============================================================

    def reconstruct(self, blocks: List[ImageBlock]) -> Dict[str, Any]:
        """
        Returns reconstruction result:
        {
            "format": "py" | "ipynb" | "js" | etc,
            "content": str OR notebook_json
        }
        """
        if not blocks:
            logger.warning("Reconstruct: No blocks provided")
            return {
                "filename": "reconstructed.txt",
                "format": "txt",
                "content": ""
            }

        fmt = blocks[0].format or "txt"
        logger.info(f"Starting reconstruction | block_count: {len(blocks)} | format: {fmt}")

        # if fmt == "ipynb":
        if blocks[0].is_notebook:
            logger.info(f"Reconstruction type: NOTEBOOK")
            return self._reconstruct_notebook(blocks)

        else:
            logger.info(f"Reconstruction type: CODE")
            return self._reconstruct_code(blocks)

    # ============================================================
    # STANDARD CODE FILE RECONSTRUCTION
    # ============================================================

    def _reconstruct_code(self, blocks: List[ImageBlock]) -> Dict[str, Any]:

        final_lines: List[str] = []

        for idx, block in enumerate(blocks, 1):
            new_lines = block.cells[0]["content"].splitlines() if block.cells else block.code.splitlines() # type: ignore
            
            logger.debug(f"Processing code block {idx}/{len(blocks)} | lines: {len(new_lines)}")
            
            if final_lines == []:
                final_lines.extend(new_lines)
                logger.debug(f"First block appended | total_lines: {len(final_lines)}")
                continue
            
            overlap = self._detect_overlap(final_lines, new_lines)
            
            if overlap > 0:
                logger.debug(f"Overlap detected | block: {idx} | overlap_lines: {overlap}")
            
            final_lines.extend(new_lines[overlap:])
            logger.debug(f"Block merged | total_lines: {len(final_lines)}")
        
        final_code = "\n".join(final_lines)
        
        logger.info(f"Code reconstruction complete | final_lines: {len(final_lines)} | filename: {blocks[0].filename}")

        return {
            "filename": blocks[0].filename,
            "format": blocks[0].format,
            "content": final_code
        }

    # ============================================================
    # NOTEBOOK RECONSTRUCTION
    # ============================================================

    def _reconstruct_notebook(self, blocks: List[ImageBlock]) -> Dict[str, Any]:
        logger.info(f"Notebook reconstruction starting | block_count: {len(blocks)}")
        
        cells = []
        for block_idx, block in enumerate(blocks, 1):
            if not block.cells:
                logger.debug(f"Block {block_idx}: no cells found")
                continue
            
            logger.debug(f"Processing block {block_idx} | cells_count: {len(block.cells)}")
            
            for cell_idx, cell in enumerate(block.cells, 1):
                merged = False
                # try merge with previous cell if overlap
                if cells and cell["type"] == "code" and cells[-1]["type"] == "code": # type: ignore
                    overlap = self._detect_overlap(
                        cells[-1]["content"].splitlines(),
                        cell["content"].splitlines() # type: ignore
                    )
                    if overlap > 0:
                        logger.debug(f"Cell merge: overlap detected | lines: {overlap}")
                        new_lines = cell["content"].splitlines()[overlap:] # type: ignore
                        cells[-1]["content"] += "\n" + "\n".join(new_lines)
                        merged = True
                
                if not merged:
                    cells.append(cell)
                    logger.debug(f"Cell added | type: {cell['type']} | merged: {merged}") # type: ignore
        
        notebook = {
            "cells": [
                {
                    "cell_type": "code" if c["type"] == "code" else "markdown",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": c["content"].splitlines(keepends=True)
                }
                for c in cells
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
        logger.info(f"Notebook reconstruction complete | cells_count: {len(cells)}")

        return {
            "filename": blocks[0].filename,
            "format": "ipynb",
            "content": notebook
        }

    # ============================================================
    # OVERLAP DETECTION
    # ============================================================

    def _detect_overlap(self, existing_lines: List[str], new_lines: List[str], max_window: int = 10) -> int:
        """
        Detect number of overlapping lines.
        Returns count of overlapping lines.
        """

        max_check = min(max_window, len(existing_lines), len(new_lines))
        for size in range(max_check, 0, -1):
            if existing_lines[-size:] == new_lines[:size]:
                return size
        return 0