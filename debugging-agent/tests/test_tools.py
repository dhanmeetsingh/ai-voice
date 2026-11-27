import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tools
from main import validate_call


class ToolValidationTests(unittest.TestCase):
    def test_allowed_call(self):
        tool, arguments = validate_call("get_error_details", {"error_code": "DB_TIMEOUT"})
        self.assertIn("pool exhaustion", tool(**arguments))

    def test_rejects_undeclared_tool(self):
        with self.assertRaisesRegex(ValueError, "not allowed"):
            validate_call("shell", {"command": "ls"})

    def test_rejects_malformed_arguments(self):
        for name, arguments in [
            ("read_logs", {"path": "/tmp/file"}),
            ("get_error_details", {}),
            ("get_error_details", {"error_code": 123}),
            ("get_error_details", {"error_code": "  "}),
            ("get_error_details", ["DB_TIMEOUT"]),
            ("save_report", {"content": "report", "path": "../other.md"}),
        ]:
            with self.subTest(name=name, arguments=arguments):
                with self.assertRaises(ValueError):
                    validate_call(name, arguments)

    def test_unknown_error_code(self):
        with self.assertRaisesRegex(ValueError, "Unknown error code"):
            tools.get_error_details("UNKNOWN")

    def test_read_logs_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data" / "app.log").write_bytes(b"x" * 5000)
            with patch.object(tools, "ROOT", root):
                self.assertEqual(len(tools.read_logs()), 4096)

    def test_report_replaces_symlink_without_touching_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / "reports"
            reports.mkdir()
            outside = root / "outside.md"
            outside.write_text("keep me")
            report = reports / tools.REPORT_NAME
            report.symlink_to(outside)

            with patch.object(tools, "ROOT", root):
                tools.save_report("first report")
                tools.save_report("second report")
            self.assertFalse(report.is_symlink())
            self.assertEqual(report.read_text(), "second report\n")
            self.assertEqual(outside.read_text(), "keep me")
            self.assertEqual(list(reports.iterdir()), [report])

    def test_report_directory_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            (root / "reports").symlink_to(outside)
            with patch.object(tools, "ROOT", root):
                with self.assertRaises(OSError):
                    tools.save_report("report")
            self.assertEqual(list(outside.iterdir()), [])

    def test_report_size_limit(self):
        with self.assertRaisesRegex(ValueError, "8000"):
            tools.save_report("x" * 8001)
