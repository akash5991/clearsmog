import json
from pathlib import Path

from clearsmog.models import CellDiffType
from clearsmog.notebook_diff import diff_notebooks

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_modified_cell_detected():
    diffs = diff_notebooks(load("notebook_old.ipynb"), load("notebook_new.ipynb"))
    types = [d.diff_type for d in diffs]
    assert CellDiffType.MODIFIED in types


def test_added_cell_detected():
    diffs = diff_notebooks(load("notebook_old.ipynb"), load("notebook_new.ipynb"))
    types = [d.diff_type for d in diffs]
    assert CellDiffType.ADDED in types


def test_unchanged_cell_not_in_output():
    diffs = diff_notebooks(load("notebook_old.ipynb"), load("notebook_new.ipynb"))
    # The imports cell and markdown cell are unchanged — should not appear
    unchanged_sources = [d for d in diffs if "import seaborn" in "".join(d.source_new)]
    assert not unchanged_sources


def test_image_change_detected():
    diffs = diff_notebooks(load("notebook_old.ipynb"), load("notebook_new.ipynb"))
    modified = [d for d in diffs if d.diff_type == CellDiffType.MODIFIED]
    assert any(d.has_image_change for d in modified)


def test_no_changes_returns_empty():
    old = load("notebook_new.ipynb")
    diffs = diff_notebooks(old, old)
    assert diffs == []


def test_new_notebook_all_added():
    new = load("notebook_new.ipynb")
    diffs = diff_notebooks(None, new)
    assert all(d.diff_type == CellDiffType.ADDED for d in diffs)


def test_removed_cell():
    old_nb = json.loads(load("notebook_new.ipynb"))
    new_nb = json.loads(load("notebook_new.ipynb"))
    del new_nb["cells"][-1]  # remove the plt.show() cell
    diffs = diff_notebooks(json.dumps(old_nb), json.dumps(new_nb))
    assert any(d.diff_type == CellDiffType.REMOVED for d in diffs)


def test_execution_count_ignored():
    old_nb = json.loads(load("notebook_old.ipynb"))
    new_nb = json.loads(load("notebook_old.ipynb"))
    new_nb["cells"][0]["execution_count"] = 99  # only change is execution count
    diffs = diff_notebooks(json.dumps(old_nb), json.dumps(new_nb))
    assert diffs == []
