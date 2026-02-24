from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Cell:
    """
    Represents a single notebook or code cell extracted from an image.
    """

    type: str  # "code" or "markdown"
    content: str

    start_line: Optional[int] = None
    end_line: Optional[int] = None

    def line_count(self) -> int:
        if not self.content:
            return 0
        return len(self.content.splitlines())


@dataclass
class ImageBlock:
    """
    Represents complete extracted data from one image.

    This is the core object passed through the entire pipeline:
    extraction → grouping → ordering → reconstruction
    """

    # Required: source image
    image_path: str

    # Extracted code content
    code: str = ""

    # Notebook cells (if notebook)
    cells: List[Cell] = field(default_factory=list)

    # File metadata (LLM extracted)
    format: str = "txt" 
    language: str = "text"
    filename: str = ""
    # tab_name: str = ""

    # Line metadata (for ordering)
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    total_lines: Optional[int] = None

    # Notebook flag
    is_notebook: bool = False

    # Local metadata (extracted from file system)
    timestamp: Optional[float] = None

    # Derived grouping key
    group_key: Optional[str] = None

    # Debug / optional raw JSON from LLM
    raw_response: Optional[Dict[str, Any]] = None

    def compute_total_lines(self) -> int:
        """
        Compute total lines safely if missing.
        """
        if self.total_lines is not None:
            return self.total_lines

        if self.code:
            return len(self.code.splitlines())

        if self.cells:
            return sum(cell.line_count() for cell in self.cells)

        return 0

    def has_line_numbers(self) -> bool:
        """
        Check if reliable line numbers are available.
        """
        return (
            self.start_line is not None and
            self.end_line is not None and
            self.start_line >= 0 and
            self.end_line >= self.start_line
        )

    def line_span(self) -> int:
        """
        Returns number of lines spanned.
        """
        if self.has_line_numbers():
            return self.end_line - self.start_line + 1 # type: ignore
        return self.compute_total_lines()

    def has_code(self) -> bool:
        """
        Check if any code content exists.
        """
        return bool(self.code.strip()) or bool(self.cells)

    def determine_group_key(self) -> str:
        """
        Determine grouping key based on priority.
        Priority order:
        1. filename
        2. tab_name
        3. fallback to image_path
        """

        if self.filename:
            self.group_key = self.filename.strip()
            return self.group_key

        # if self.tab_name:
        #     self.group_key = self.tab_name.strip()
        #     return self.group_key

        self.group_key = self.image_path
        return self.group_key

    def __repr__(self) -> str:
        """
        Clean debug representation.
        """
        return (
            f"ImageBlock("
            f"image='{self.image_path}', "
            f"filename='{self.filename}', "
            f"start={self.start_line}, "
            f"end={self.end_line}, "
            f"timestamp={self.timestamp})"
        )