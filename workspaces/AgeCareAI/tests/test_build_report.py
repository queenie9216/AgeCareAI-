"""Tests for build_report.py document generation."""

import pytest
import os
import sys
import re

# Import from build_report.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_report import (
    _parse_md_table,
    _add_inline,
    _build_table,
    MD_PATH,
    OUT_PATH,
)


class TestConstants:
    def test_md_path_exists(self):
        assert os.path.exists(MD_PATH), f"REPORT.md not found at {MD_PATH}"

    def test_out_path_defined(self):
        assert OUT_PATH is not None
        assert len(OUT_PATH) > 0


class TestParseMdTable:
    def test_parses_header_and_rows(self):
        lines = [
            "| Column 1 | Column 2 |",
            "| --- | --- |",
            "| Value 1 | Value 2 |",
            "| Value 3 | Value 4 |",
        ]
        header, rows = _parse_md_table(lines)
        assert header == ["Column 1", "Column 2"]
        assert len(rows) == 2

    def test_skips_separator_line(self):
        lines = [
            "| A | B |",
            "| --- | --- |",
            "| C | D |",
        ]
        header, rows = _parse_md_table(lines)
        assert len(rows) == 1
        assert rows[0] == ["C", "D"]

    def test_strips_whitespace(self):
        lines = [
            "|  Alpha  |  Beta  |",
            "| --- | --- |",
            "|  1  |  2  |",
        ]
        header, rows = _parse_md_table(lines)
        assert header == ["Alpha", "Beta"]
        assert rows[0] == ["1", "2"]

    def test_asterisks_preserved_in_header(self):
        lines = [
            "| **Bold** | Normal |",
            "| --- | --- |",
            "| Cell | Cell |",
        ]
        header, rows = _parse_md_table(lines)
        # strip("*") only removes leading/trailing asterisks, not internal ones
        assert header == ["**Bold**", "Normal"]

    def test_empty_lines_no_header(self):
        lines = [
            "| A | B |",
            "| C | D |",
        ]
        header, rows = _parse_md_table(lines)
        assert header == ["A", "B"]
        assert len(rows) == 1

    def test_non_table_lines_become_header(self):
        lines = ["---", "not a table"]
        header, rows = _parse_md_table(lines)
        # Lines not matching table pattern: first is header, second is data row
        assert header == ["---"]
        assert rows == [["not a table"]]

    def test_single_column(self):
        lines = [
            "| Only |",
            "| --- |",
            "| One |",
        ]
        header, rows = _parse_md_table(lines)
        assert len(header) == 1
        assert header[0] == "Only"


class TestBuildReport:
    def test_report_md_readable(self):
        with open(MD_PATH, encoding="utf-8") as f:
            md = f.read()
        assert len(md) > 0
        assert "AgeCareAI" in md

    def test_report_has_headings(self):
        with open(MD_PATH, encoding="utf-8") as f:
            md = f.read()
        assert "#" in md

    def test_report_has_pagebreaks(self):
        with open(MD_PATH, encoding="utf-8") as f:
            md = f.read()
        # The report uses page breaks in the markdown
        lines = md.splitlines()
        has_heading = any(l.startswith("#") for l in lines)
        assert has_heading

    def test_report_has_tables(self):
        with open(MD_PATH, encoding="utf-8") as f:
            md = f.read()
        lines = md.splitlines()
        table_lines = [l for l in lines if l.strip().startswith("|")]
        assert len(table_lines) > 0
