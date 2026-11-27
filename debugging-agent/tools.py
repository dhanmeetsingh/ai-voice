import json
import os
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
REPORT_NAME = "debug_report.md"


# STEP 1: DEFINE TOOLS
def read_logs() -> str:
    """Read up to 4096 bytes from the local application log."""
    with (ROOT / "data" / "app.log").open("rb") as log:
        return log.read(4096).decode("utf-8", errors="replace")


def get_error_details(error_code: str) -> str:
    """Look up a code observed in the logs in the local troubleshooting guide."""
    guide = json.loads((ROOT / "data" / "error_guide.json").read_text(encoding="utf-8"))
    if error_code not in guide:
        raise ValueError(f"Unknown error code: {error_code}")
    return json.dumps(guide[error_code], indent=2)


def save_report(content: str) -> str:
    """Save the full Markdown report. Takes report text only, with no path option."""
    if not content.strip() or len(content) > 8000:
        raise ValueError("Report must contain 1–8000 characters.")

    # Open the fixed directory without following a symlink. The final rename
    # replaces the directory entry, so an existing symlink cannot redirect writes.
    directory = os.open(ROOT / "reports", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    temp_name = f".{uuid4().hex}.tmp"
    try:
        fd = os.open(
            temp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as report:
                report.write(content.strip() + "\n")
            os.replace(temp_name, REPORT_NAME, src_dir_fd=directory, dst_dir_fd=directory)
        finally:
            try:
                os.unlink(temp_name, dir_fd=directory)
            except FileNotFoundError:
                pass
    finally:
        os.close(directory)
    return f"Saved to reports/{REPORT_NAME}"
