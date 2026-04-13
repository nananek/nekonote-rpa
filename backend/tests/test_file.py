"""Tests for nekonote.file."""

import pytest

from nekonote import file
from nekonote.errors import FileNotFoundError


class TestFileOps:
    def test_copy(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("hello")
        dst = str(tmp_path / "dst.txt")
        result = file.copy(str(src), dst)
        assert "dst.txt" in result
        assert (tmp_path / "dst.txt").read_text() == "hello"

    def test_move(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("data")
        dst = str(tmp_path / "moved.txt")
        file.move(str(src), dst)
        assert not src.exists()
        assert (tmp_path / "moved.txt").read_text() == "data"

    def test_delete(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_text("bye")
        file.delete(str(f))
        assert not f.exists()

    def test_rename(self, tmp_path):
        f = tmp_path / "old.txt"
        f.write_text("x")
        result = file.rename(str(f), "new.txt")
        assert "new.txt" in result
        assert not f.exists()
        assert (tmp_path / "new.txt").exists()

    def test_exists(self, tmp_path):
        f = tmp_path / "exists.txt"
        f.write_text("y")
        assert file.exists(str(f)) is True
        assert file.exists(str(tmp_path / "nope.txt")) is False

    def test_get_info(self, tmp_path):
        f = tmp_path / "info.txt"
        f.write_text("content")
        info = file.get_info(str(f))
        assert info["name"] == "info.txt"
        assert info["extension"] == ".txt"
        assert info["size"] == 7
        assert info["is_file"] is True

    def test_copy_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc:
            file.copy(str(tmp_path / "missing.txt"), str(tmp_path / "dst.txt"))
        assert exc.value.code == "FILE_NOT_FOUND"


class TestDirOps:
    def test_create_dir(self, tmp_path):
        d = str(tmp_path / "a" / "b" / "c")
        result = file.create_dir(d)
        assert "c" in result
        assert (tmp_path / "a" / "b" / "c").is_dir()

    def test_delete_dir(self, tmp_path):
        d = tmp_path / "rmdir"
        d.mkdir()
        (d / "file.txt").write_text("x")
        file.delete_dir(str(d))
        assert not d.exists()

    def test_list_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.xlsx").write_text("b")
        (tmp_path / "c.txt").write_text("c")
        result = file.list_files(str(tmp_path), pattern="*.txt")
        assert len(result) == 2

    def test_list_dirs(self, tmp_path):
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "file.txt").write_text("x")
        result = file.list_dirs(str(tmp_path))
        assert len(result) == 2


class TestTextOps:
    def test_read_write(self, tmp_path):
        f = str(tmp_path / "rw.txt")
        file.write_text(f, "hello world")
        assert file.read_text(f) == "hello world"

    def test_append(self, tmp_path):
        f = str(tmp_path / "app.txt")
        file.write_text(f, "line1\n")
        file.append_text(f, "line2\n")
        assert file.read_text(f) == "line1\nline2\n"

    def test_unicode_text(self, tmp_path):
        content = "\u65e5\u672c\u8a9e\u30c6\u30b9\u30c8"
        f = str(tmp_path / "jp.txt")
        file.write_text(f, content)
        assert file.read_text(f) == content


class TestZipOps:
    def test_zip_unzip(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("aaa")
        f2.write_text("bbb")
        archive = str(tmp_path / "test.zip")
        file.zip(archive, [str(f1), str(f2)])
        assert (tmp_path / "test.zip").exists()

        out = str(tmp_path / "extracted")
        file.unzip(archive, out)
        assert (tmp_path / "extracted" / "a.txt").read_text() == "aaa"
        assert (tmp_path / "extracted" / "b.txt").read_text() == "bbb"
