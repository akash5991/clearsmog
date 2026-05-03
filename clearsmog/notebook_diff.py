import copy
import difflib
import hashlib
import json

from clearsmog.models import CellDiff, CellDiffType

_VOLATILE_CELL_FIELDS = {"execution_count", "id"}
_VOLATILE_OUTPUT_FIELDS = {"execution_count", "metadata"}
_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/svg+xml"}


def _strip_volatile_metadata(cell: dict) -> dict:
    cell = copy.deepcopy(cell)
    for field in _VOLATILE_CELL_FIELDS:
        cell.pop(field, None)
    cell.pop("metadata", None)
    for output in cell.get("outputs", []):
        for field in _VOLATILE_OUTPUT_FIELDS:
            output.pop(field, None)
    return cell


def _cell_source_hash(cell: dict) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        source = "".join(source)
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _cell_key(cell_index: int, source_hash: str) -> str:
    return f"{cell_index}:{source_hash}"


def _source_lines(cell: dict) -> list[str]:
    source = cell.get("source", "")
    if isinstance(source, list):
        return source
    return source.splitlines(keepends=True)


def _extract_text_outputs(cell: dict) -> list[str]:
    lines = []
    for output in cell.get("outputs", []):
        output_type = output.get("output_type", "")
        if output_type in {"stream", "execute_result", "display_data"}:
            text = output.get("text", output.get("data", {}).get("text/plain", ""))
            if isinstance(text, list):
                lines.extend(text)
            elif text:
                lines.append(str(text))
        elif output_type == "error":
            lines.append(f"[Error] {output.get('ename')}: {output.get('evalue')}\n")
    return lines


def _has_image_output_change(old_cell: dict | None, new_cell: dict | None) -> bool:
    def image_outputs(cell: dict) -> list[str]:
        result = []
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            for mime in _IMAGE_MIME_TYPES:
                if mime in data:
                    content = data[mime]
                    result.append(content if isinstance(content, str) else "".join(content))
        return result

    old_images = image_outputs(old_cell) if old_cell else []
    new_images = image_outputs(new_cell) if new_cell else []
    return old_images != new_images


def _diff_text_outputs(old_cell: dict | None, new_cell: dict | None) -> list[str]:
    old_lines = _extract_text_outputs(old_cell) if old_cell else []
    new_lines = _extract_text_outputs(new_cell) if new_cell else []
    if old_lines == new_lines:
        return []
    return list(
        difflib.unified_diff(old_lines, new_lines, fromfile="old output", tofile="new output")
    )


def _match_cells(
    old_cells: list[dict], new_cells: list[dict]
) -> list[tuple[dict | None, dict | None]]:
    old_hashes = [_cell_source_hash(c) for c in old_cells]
    new_hashes = [_cell_source_hash(c) for c in new_cells]

    matcher = difflib.SequenceMatcher(None, old_hashes, new_hashes, autojunk=False)
    pairs: list[tuple[dict | None, dict | None]] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for old, new in zip(old_cells[i1:i2], new_cells[j1:j2]):
                pairs.append((old, new))
        elif tag == "replace":
            old_chunk = old_cells[i1:i2]
            new_chunk = new_cells[j1:j2]
            for k in range(max(len(old_chunk), len(new_chunk))):
                old = old_chunk[k] if k < len(old_chunk) else None
                new = new_chunk[k] if k < len(new_chunk) else None
                pairs.append((old, new))
        elif tag == "delete":
            for old in old_cells[i1:i2]:
                pairs.append((old, None))
        elif tag == "insert":
            for new in new_cells[j1:j2]:
                pairs.append((None, new))

    return pairs


def diff_notebooks(old_json: str | None, new_json: str) -> list[CellDiff]:
    new_nb = json.loads(new_json)
    old_nb = json.loads(old_json) if old_json else {"cells": []}

    old_cells = [_strip_volatile_metadata(c) for c in old_nb.get("cells", [])]
    new_cells = [_strip_volatile_metadata(c) for c in new_nb.get("cells", [])]

    pairs = _match_cells(old_cells, new_cells)
    results: list[CellDiff] = []

    for index, (old, new) in enumerate(pairs):
        if old is None:
            diff_type = CellDiffType.ADDED
            cell_type = new.get("cell_type", "code")
            src_hash = _cell_source_hash(new)
        elif new is None:
            diff_type = CellDiffType.REMOVED
            cell_type = old.get("cell_type", "code")
            src_hash = _cell_source_hash(old)
        elif _cell_source_hash(old) == _cell_source_hash(new) and old.get("outputs") == new.get(
            "outputs"
        ):
            continue  # truly unchanged
        else:
            diff_type = CellDiffType.MODIFIED
            cell_type = new.get("cell_type", "code")
            src_hash = _cell_source_hash(new)

        results.append(
            CellDiff(
                cell_index=index,
                diff_type=diff_type,
                cell_type=cell_type,
                source_old=_source_lines(old) if old else [],
                source_new=_source_lines(new) if new else [],
                output_text_diff=_diff_text_outputs(old, new),
                has_image_change=_has_image_output_change(old, new),
                cell_key=_cell_key(index, src_hash),
            )
        )

    return results
