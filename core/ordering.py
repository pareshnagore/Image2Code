# ordering.py

from typing import List, Optional, Tuple
from datetime import datetime

from core.models import ImageBlock


class BlockOrderer:
    """
    Orders ImageBlocks belonging to same logical file.

    Priority order:

    1. line numbers
    2. timestamp
    3. overlap detection
    4. fallback
    """

    def order(self, blocks: List[ImageBlock]) -> List[ImageBlock]:
        if len(blocks) <= 1:
            return blocks
        
        # Strategy 1: line numbers
        ordered = self._order_by_line_numbers(blocks)
        if ordered:
            return ordered
        
        # Strategy 2: timestamp
        ordered = self._order_by_timestamp(blocks)
        if ordered:
            return ordered
        
        # Strategy 3: overlap detection
        ordered = self._order_by_overlap(blocks)
        if ordered:
            return ordered
        
        # Strategy 4: fallback
        return blocks

    # ------------------------------------------------------------------

    def _order_by_line_numbers(self, blocks: List[ImageBlock]) -> Optional[List[ImageBlock]]:
        valid = [b for b in blocks if b.start_line is not None]
        if len(valid) < len(blocks):
            return None
        return sorted(blocks, key=lambda b: b.start_line, reverse=False) # type: ignore

    # ------------------------------------------------------------------

    def _order_by_timestamp(self, blocks: List[ImageBlock]) -> Optional[List[ImageBlock]]:
        valid = [b for b in blocks if b.timestamp is not None]
        if len(valid) < len(blocks):
            return None
        return sorted(blocks, key=lambda b: b.timestamp, reverse=False) # type: ignore

    # ------------------------------------------------------------------

    def _order_by_overlap(self, blocks: List[ImageBlock]) -> Optional[List[ImageBlock]]:
        if len(blocks) < 2:
            return blocks
        # find best chain greedily
        unused = blocks.copy()
        ordered = [unused.pop(0)]
        while unused:
            last = ordered[-1]
            next_block = self._find_best_next(last, unused)
            if not next_block:
                return None
            ordered.append(next_block)
            unused.remove(next_block)
        return ordered

    # ------------------------------------------------------------------

    def _find_best_next(self, current: ImageBlock, candidates: List[ImageBlock]) -> Optional[ImageBlock]:
        best_candidate = None
        best_score = 0
        current_lines = current.code.splitlines()
        for candidate in candidates:
            candidate_lines = candidate.code.splitlines()
            score = self._overlap_score(current_lines, candidate_lines)
            if score > best_score:
                best_score = score
                best_candidate = candidate
        return best_candidate

    # ------------------------------------------------------------------

    def _overlap_score(self, lines_a: List[str], lines_b: List[str], window: int = 15) -> int:
        """
        Returns number of matching overlapping lines.
        compares tail of A with head of B
        """
        max_check = min(window, len(lines_a), len(lines_b))
        for size in range(max_check, 0, -1):
            tail = lines_a[-size:]
            head = lines_b[:size]
            if tail == head:
                return size
        return 0