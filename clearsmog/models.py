from dataclasses import dataclass, field
from enum import Enum


class CellDiffType(Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class CellDiff:
    cell_index: int
    diff_type: CellDiffType
    cell_type: str  # "code", "markdown", "raw"
    source_old: list[str] = field(default_factory=list)
    source_new: list[str] = field(default_factory=list)
    output_text_diff: list[str] = field(default_factory=list)  # unified diff lines
    has_image_change: bool = False
    cell_key: str = ""  # hash used to identify this cell across pushes
