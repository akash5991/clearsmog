from clearsmog.comment_builder import build_comment
from clearsmog.models import CellDiff, CellDiffType


def _make_diff(**kwargs) -> CellDiff:
    defaults = dict(
        cell_index=2,
        diff_type=CellDiffType.MODIFIED,
        cell_type="code",
        source_old=["sns.scatterplot(x='col1', y='col2', data=df)\n"],
        source_new=["sns.scatterplot(x='col1', y='col2', data=df, palette='viridis')\n"],
        output_text_diff=[],
        has_image_change=False,
        cell_key="2:abc123",
    )
    defaults.update(kwargs)
    return CellDiff(**defaults)


def test_marker_present():
    comment = build_comment(_make_diff(), "analysis.ipynb")
    assert "<!-- clearsmog:cell:2:abc123 -->" in comment


def test_title_contains_filename_and_index():
    comment = build_comment(_make_diff(), "analysis.ipynb")
    assert "analysis.ipynb" in comment
    assert "Cell 3" in comment  # cell_index 2 → displayed as 3


def test_source_diff_shown_for_modified():
    comment = build_comment(_make_diff(), "analysis.ipynb")
    assert "```diff" in comment
    assert "palette" in comment


def test_image_change_note():
    comment = build_comment(_make_diff(has_image_change=True), "analysis.ipynb")
    assert "Image output changed" in comment


def test_no_image_note_when_no_change():
    comment = build_comment(_make_diff(has_image_change=False), "analysis.ipynb")
    assert "Image output changed" not in comment


def test_added_cell_shows_plus_lines():
    diff = _make_diff(
        diff_type=CellDiffType.ADDED,
        source_old=[],
        source_new=["plt.show()\n"],
        cell_key="3:def456",
    )
    comment = build_comment(diff, "analysis.ipynb")
    assert "+ plt.show()" in comment


def test_output_diff_shown():
    diff = _make_diff(output_text_diff=["- old result\n", "+ new result\n"])
    comment = build_comment(diff, "analysis.ipynb")
    assert "Output diff" in comment
    assert "old result" in comment
