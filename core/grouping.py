# grouping.py

from collections import defaultdict
from typing import Dict, List, Tuple

from core.models import ImageBlock


class BlockGroup:
    """
    Represents one logical code file reconstructed from multiple images.
    """

    def __init__(self, key: Tuple[str, str, str]):
        self.key = key
        self.blocks: List[ImageBlock] = []

    def add(self, block: ImageBlock):
        self.blocks.append(block)

    def size(self) -> int:
        return len(self.blocks)

    def total_lines(self) -> int:
        return sum(block.line_span() for block in self.blocks)


class BlockGrouper:
    """
    Groups ImageBlocks into logical files.

    Grouping priority:
    1. filename
    2. language + format
    """

    def group(self, blocks: List[ImageBlock]) -> List[BlockGroup]:

        groups: Dict[Tuple[str, str, str], BlockGroup] = {}
        for block in blocks:
            key = self._make_group_key(block)
            if key not in groups:
                groups[key] = BlockGroup(key)
            groups[key].add(block)

        return list(groups.values())

    # -------------------------

    def _make_group_key(self, block: ImageBlock) -> Tuple[str, str, str]:
        """
        Returns grouping key.
        priority:
        filename > language+format > unknown
        """

        filename = block.filename or ""
        language = block.language or ""
        fmt = block.format or ""

        if filename:
            return ("filename", filename, "")

        if language or fmt:
            return ("langfmt", language, fmt)

        return ("unknown", "", "")