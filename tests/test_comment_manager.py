from clearsmog.comment_manager import parse_bot_comments


def test_parses_marker():
    comments = [
        {"id": 101, "body": "<!-- clearsmog:cell:2:abc123 -->\n### Cell 3"},
        {"id": 102, "body": "A regular human comment"},
        {"id": 103, "body": "<!-- clearsmog:cell:0:xyz789 -->\n### Cell 1"},
    ]
    result = parse_bot_comments(comments)
    assert result == {"2:abc123": 101, "0:xyz789": 103}


def test_ignores_non_bot_comments():
    comments = [{"id": 999, "body": "LGTM!"}]
    result = parse_bot_comments(comments)
    assert result == {}


def test_empty_list():
    assert parse_bot_comments([]) == {}
