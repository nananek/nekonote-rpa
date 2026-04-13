"""Tests for nekonote.excel (CSV tests only — openpyxl tests need the dep)."""

import pytest

from nekonote import excel
from nekonote.errors import FileNotFoundError


class TestCSV:
    def test_write_read_csv_dicts(self, tmp_path):
        f = str(tmp_path / "data.csv")
        data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
        excel.write_csv(f, data)
        result = excel.read_csv(f)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == "25"

    def test_write_read_csv_lists(self, tmp_path):
        f = str(tmp_path / "data.csv")
        data = [["name", "age"], ["Alice", "30"]]
        excel.write_csv(f, data)
        result = excel.read_csv(f, header=False)
        assert len(result) == 2
        assert result[0] == ["name", "age"]

    def test_write_csv_japanese(self, tmp_path):
        f = str(tmp_path / "jp.csv")
        data = [{"名前": "太郎", "年齢": "25"}]
        excel.write_csv(f, data)
        result = excel.read_csv(f)
        assert result[0]["名前"] == "太郎"

    def test_write_csv_tsv(self, tmp_path):
        f = str(tmp_path / "data.tsv")
        data = [{"a": "1", "b": "2"}]
        excel.write_csv(f, data, delimiter="\t")
        result = excel.read_csv(f, delimiter="\t")
        assert result[0]["a"] == "1"

    def test_read_csv_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            excel.read_csv(str(tmp_path / "missing.csv"))


class TestExcel:
    """Tests that require openpyxl."""

    @pytest.fixture(autouse=True)
    def _check_openpyxl(self):
        pytest.importorskip("openpyxl")

    def test_write_read_dicts(self, tmp_path):
        f = str(tmp_path / "test.xlsx")
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        excel.write(f, data)
        result = excel.read(f)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == 25

    def test_write_read_lists(self, tmp_path):
        f = str(tmp_path / "test.xlsx")
        data = [["name", "age"], ["Alice", 30]]
        excel.write(f, data)
        result = excel.read(f, header=False)
        assert len(result) == 2

    def test_read_cell(self, tmp_path):
        f = str(tmp_path / "cell.xlsx")
        excel.write(f, [{"A": "hello"}])
        value = excel.read_cell(f, cell="A1")
        assert value == "A"  # header row

    def test_write_cell(self, tmp_path):
        f = str(tmp_path / "wc.xlsx")
        excel.write(f, [{"x": 1}])
        excel.write_cell(f, cell="C1", value="injected")
        value = excel.read_cell(f, cell="C1")
        assert value == "injected"

    def test_get_sheet_names(self, tmp_path):
        f = str(tmp_path / "sheets.xlsx")
        excel.write(f, [{"a": 1}], sheet="Data")
        names = excel.get_sheet_names(f)
        assert "Data" in names

    def test_append(self, tmp_path):
        f = str(tmp_path / "app.xlsx")
        excel.write(f, [{"a": 1, "b": 2}])
        excel.append(f, [{"a": 3, "b": 4}])
        result = excel.read(f)
        assert len(result) == 2

    def test_read_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            excel.read(str(tmp_path / "nope.xlsx"))

    def test_japanese_data(self, tmp_path):
        f = str(tmp_path / "jp.xlsx")
        data = [{"名前": "太郎", "年齢": 25}]
        excel.write(f, data)
        result = excel.read(f)
        assert result[0]["名前"] == "太郎"
