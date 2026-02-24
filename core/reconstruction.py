# reconstruction.py

from typing import List, Dict, Any
import json

from core.models import ImageBlock


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
            return {
                "filename": "reconstructed.txt",
                "format": "txt",
                "content": ""
            }

        fmt = blocks[0].format or "txt"

        # if fmt == "ipynb":
        if blocks[0].is_notebook:
            return self._reconstruct_notebook(blocks)

        else:
            return self._reconstruct_code(blocks)

    # ============================================================
    # STANDARD CODE FILE RECONSTRUCTION
    # ============================================================

    def _reconstruct_code(self, blocks: List[ImageBlock]) -> Dict[str, Any]:

        final_lines: List[str] = []

        for block in blocks:
            new_lines = block.cells[0]["content"].splitlines() if block.cells else block.code.splitlines() # type: ignore
            print("New block lines:", new_lines)
            if final_lines == []:
                final_lines.extend(new_lines)
                continue
            overlap = self._detect_overlap(final_lines, new_lines)
            final_lines.extend(new_lines[overlap:])
            print("Current final lines:", final_lines)
        
        final_code = "\n".join(final_lines)
        print("Final reconstructed code:", final_code)

        return {
            "filename": blocks[0].filename,
            "format": blocks[0].format,
            "content": final_code
        }

    # ============================================================
    # NOTEBOOK RECONSTRUCTION
    # ============================================================

    def _reconstruct_notebook(self, blocks: List[ImageBlock]) -> Dict[str, Any]:
        cells = []
        for block in blocks:
            if not block.cells:
                continue
            for cell in block.cells:
                merged = False
                # try merge with previous cell if overlap
                if cells and cell["type"] == "code" and cells[-1]["type"] == "code": # type: ignore
                    overlap = self._detect_overlap(
                        cells[-1]["content"].splitlines(),
                        cell["content"].splitlines() # type: ignore
                    )
                    if overlap > 0:
                        new_lines = cell["content"].splitlines()[overlap:] # type: ignore
                        cells[-1]["content"] += "\n" + "\n".join(new_lines)
                        merged = True
                if not merged:
                    cells.append(cell)
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