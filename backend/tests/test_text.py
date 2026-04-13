"""Tests for nekonote.text (string + datetime utilities)."""

from nekonote import text


class TestStringOps:
    def test_replace(self):
        assert text.replace("hello world", "world", "python") == "hello python"

    def test_split(self):
        assert text.split("a,b,c", ",") == ["a", "b", "c"]

    def test_join(self):
        assert text.join(["a", "b", "c"], "-") == "a-b-c"

    def test_trim(self):
        assert text.trim("  hello  ") == "hello"

    def test_to_upper(self):
        assert text.to_upper("hello") == "HELLO"

    def test_to_lower(self):
        assert text.to_lower("HELLO") == "hello"

    def test_length(self):
        assert text.length("hello") == 5
        assert text.length("日本語") == 3

    def test_substring(self):
        assert text.substring("hello world", 0, 5) == "hello"
        assert text.substring("hello world", 6) == "world"

    def test_contains(self):
        assert text.contains("hello world", "world") is True
        assert text.contains("hello world", "xyz") is False

    def test_starts_with(self):
        assert text.starts_with("hello", "hel") is True
        assert text.starts_with("hello", "xyz") is False

    def test_ends_with(self):
        assert text.ends_with("hello", "llo") is True

    def test_pad_left(self):
        assert text.pad_left("42", 5, "0") == "00042"

    def test_pad_right(self):
        assert text.pad_right("hi", 5) == "hi   "


class TestRegex:
    def test_regex_match_groups(self):
        result = text.regex_match("order-12345", r"order-(\d+)")
        assert result == ["12345"]

    def test_regex_match_no_match(self):
        assert text.regex_match("hello", r"\d+") == []

    def test_regex_find_all(self):
        result = text.regex_find_all("a1 b2 c3", r"\d")
        assert result == ["1", "2", "3"]

    def test_regex_replace(self):
        result = text.regex_replace("2024/01/15", r"(\d{4})/(\d{2})/(\d{2})", r"\1-\2-\3")
        assert result == "2024-01-15"


class TestEncoding:
    def test_base64_roundtrip(self):
        encoded = text.base64_encode("hello")
        assert text.base64_decode(encoded) == "hello"

    def test_base64_japanese(self):
        encoded = text.base64_encode("日本語")
        assert text.base64_decode(encoded) == "日本語"

    def test_url_encode_decode(self):
        encoded = text.url_encode("日本語 テスト")
        assert "%" in encoded
        assert text.url_decode(encoded) == "日本語 テスト"


class TestDateTime:
    def test_now_iso(self):
        result = text.now()
        assert "T" in result  # ISO format

    def test_today_iso(self):
        result = text.today()
        assert len(result) == 10  # YYYY-MM-DD

    def test_format_datetime(self):
        result = text.format_datetime("2024-01-15T10:30:00", "yyyy/MM/dd")
        assert result == "2024/01/15"

    def test_parse_datetime_iso(self):
        result = text.parse_datetime("2024-01-15")
        assert result.startswith("2024-01-15")

    def test_parse_datetime_custom_format(self):
        result = text.parse_datetime("15/01/2024", "%d/%m/%Y")
        assert "2024-01-15" in result

    def test_add_time(self):
        result = text.add_time("2024-01-15T10:00:00", days=1, hours=2)
        assert "2024-01-16T12:00:00" in result

    def test_diff_time(self):
        result = text.diff_time("2024-01-15", "2024-01-10")
        assert result["days"] == 5
        assert result["hours"] == 120.0
