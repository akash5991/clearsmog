import difflib

from clearsmog.models import CellDiff, CellDiffType

_MARKER_PREFIX = "<!-- clearsmog:cell:"
_MARKER_SUFFIX = " -->"


def _marker(cell_key: str) -> str:
    return f"{_MARKER_PREFIX}{cell_key}{_MARKER_SUFFIX}"


def _source_diff_block(diff: CellDiff) -> str:
    if diff.diff_type == CellDiffType.ADDED:
        lines = "".join(f"+ {line}" for line in diff.source_new)
        return f"```diff\n{lines}\n```"
    if diff.diff_type == CellDiffType.REMOVED:
        lines = "".join(f"- {line}" for line in diff.source_old)
        return f"```diff\n{lines}\n```"

    unified = list(
        difflib.unified_diff(
            diff.source_old,
            diff.source_new,
            lineterm="",
            n=3,
        )
    )
    if not unified:
        return ""
    diff_text = "\n".join(unified[2:])  # skip --- +++ header lines
    return f"```diff\n{diff_text}\n```"


def build_comment(diff: CellDiff, filename: str) -> str:
    label = diff.diff_type.value.capitalize()
    title = f"### `{filename}` — Cell {diff.cell_index + 1} — {label} (`{diff.cell_type}`)"

    parts = [_marker(diff.cell_key), title]

    source_block = _source_diff_block(diff)
    if source_block:
        parts.append("**Source diff:**")
        parts.append(source_block)

    if diff.output_text_diff:
        output_text = "\n".join(diff.output_text_diff)
        parts.append("**Output diff:**")
        parts.append(f"```diff\n{output_text}\n```")

    if diff.has_image_change:
        parts.append("> **Image output changed** — open the notebook locally to compare plots.")

    return "\n\n".join(parts)
