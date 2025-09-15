#!/usr/bin/env python3
"""
make_nice_pdf.py

Generates a LaTeX-style serif PDF from a JSON conversation file.

Features / behavior (summary):
- Uses the best available system serif font on Ubuntu 24.04 (tries TeX Gyre Termes,
  DejaVu Serif, Liberation Serif, then Times). No external installs required.
- Body text uses ~11pt font with 1.2× leading (line spacing) for a dense, book-like look.
- Manages a local virtual environment (.venv):
    * creates .venv if necessary,
    * installs required packages inside it,
    * re-executes the script using the venv python so imports come from venv,
    * on SUCCESSFUL run removes .venv automatically (no orphan venvs).
    * on FAILURE leaves .venv intact for inspection.
- Supports JSON array files or NDJSON (one JSON object per line).
- Progress logging, defensive error handling, respects relative paths and filenames with spaces.

Usage:
    python3 make_nice_pdf.py <input.json> <output.pdf>

Author: generated (updated per user request)
"""

from __future__ import annotations
import sys
import os
import json
import subprocess
import importlib
import math
import datetime
from typing import List, Dict, Any, Optional
import glob
import shutil
import traceback

# -----------------------
# Configuration
# -----------------------
VENV_DIR = ".venv"
REQUIRED_PACKAGES = ["reportlab"]
PROGRESS_CHUNK = 50
PAGE_MARGIN_MM = 22               # book-like margins
BODY_FONT_SIZE = 11.0             # points
LEADING_MULTIPLIER = 1.2          # 1.2 × font size -> leading
HEADING_SPACE = 10
ITEMS_PER_PAGE_BREAK = 40
SEPARATOR_EVERY = 12

# Preferred TTF font name patterns to search for (order indicates priority)
# Only search for regular (non-italic, non-oblique) variants
PREFERRED_SERIF_PATTERNS = [
    "*TeXGyreTermes-Regular*.ttf",     # TeX Gyre Termes Regular
    "*Termes-Regular*.ttf",
    "*DejaVuSerif.ttf",               # DejaVu Serif (regular)
    "*LiberationSerif-Regular*.ttf",   # Liberation Serif Regular
    "*Times New Roman.ttf",
    "*Times.ttf",
]

# -----------------------
# Venv helpers
# -----------------------
def script_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def venv_path() -> str:
    return os.path.join(script_dir(), VENV_DIR)

def in_target_venv() -> bool:
    """Return True if current Python executable is inside our venv path."""
    venv_bin = os.path.join(venv_path(), "bin") + os.sep
    try:
        exe = os.path.abspath(sys.executable)
        return exe.startswith(os.path.abspath(venv_bin))
    except Exception:
        return False

def run_cmd(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command, streaming output to stdout/stderr."""
    print(f"[CMD] {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)

def ensure_venv_exists() -> None:
    """Create venv if it doesn't exist."""
    vpath = venv_path()
    if os.path.isdir(vpath):
        print(f"[VENV] found existing venv at: {vpath}")
        return
    print(f"[VENV] creating venv at: {vpath} ...")
    try:
        run_cmd([sys.executable, "-m", "venv", vpath])
    except subprocess.CalledProcessError as e:
        sys.exit(f"[FATAL] Failed to create venv: {e}")

def get_venv_python() -> str:
    """Return the path to the venv python executable."""
    py = os.path.join(venv_path(), "bin", "python")
    if os.name == "nt":
        py = os.path.join(venv_path(), "Scripts", "python.exe")
    return py

def install_packages_in_venv(pkgs: List[str]) -> None:
    """Install the required packages into the venv using venv's pip."""
    vpy = get_venv_python()
    if not os.path.exists(vpy):
        sys.exit(f"[FATAL] venv python not found at {vpy}")
    try:
        run_cmd([vpy, "-m", "pip", "install", "--upgrade", "pip", "--disable-pip-version-check"])
    except subprocess.CalledProcessError as e:
        sys.exit(f"[FATAL] Failed to upgrade pip inside venv: {e}")
    try:
        cmd = [vpy, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check"] + pkgs
        run_cmd(cmd)
    except subprocess.CalledProcessError as e:
        sys.exit(f"[FATAL] Failed to install packages {pkgs} in venv: {e}")

def ensure_dependencies_and_reexec_if_needed() -> None:
    """
    Ensure REQUIRED_PACKAGES are importable. If not:
      - create venv (if missing),
      - install missing packages in the venv,
      - re-exec this script using the venv Python.
    This function returns only if imports succeed in the current interpreter.
    """
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if not missing:
        # All good in the current interpreter
        print("[DEP] All required packages present in current interpreter.")
        return

    # If we're already running inside the target venv and packages are missing -> install into this venv and re-exec
    if in_target_venv():
        print("[DEP] Running inside target venv but packages missing:", missing)
        install_packages_in_venv(missing)
        vpy = get_venv_python()
        print(f"[DEP] Re-execing with {vpy} ...")
        os.execv(vpy, [vpy] + sys.argv)

    # Not running in venv: create venv and install
    print("[DEP] Required packages missing:", missing)
    ensure_venv_exists()
    install_packages_in_venv(missing)
    # Re-exec the script using the venv python
    vpy = get_venv_python()
    print(f"[DEP] Re-execing script with venv python: {vpy}")
    os.execv(vpy, [vpy] + sys.argv)

# Ensure dependencies are available (may re-exec)
ensure_dependencies_and_reexec_if_needed()

# -----------------------
# Now safe to import reportlab
# -----------------------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import ttfonts
    from reportlab.pdfbase import pdfmetrics
except Exception as e:
    sys.exit(f"[FATAL] Failed to import reportlab after venv setup: {e}")

# -----------------------
# Font discovery & registration
# -----------------------
def find_serif_ttf() -> Optional[str]:
    """
    Search common font directories for a high-quality serif TTF matching preferred patterns.
    Return the first match path or None. Only matches regular (non-italic) variants.
    """
    # Common font directories on Linux
    search_dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
        os.path.expanduser("~/.local/share/fonts"),
        os.path.expanduser("~/.fonts"),
        "/usr/local/share/fonts",
        "/usr/share/fonts/truetype/dejavu",
    ]
    for d in search_dirs:
        for patt in PREFERRED_SERIF_PATTERNS:
            pattern = os.path.join(d, "**", patt)
            matches = glob.glob(pattern, recursive=True)
            if matches:
                # Filter out italic/oblique variants
                for match in matches:
                    basename = os.path.basename(match).lower()
                    if "italic" not in basename and "oblique" not in basename:
                        return os.path.abspath(match)
    
    # Last resort: search for any "*Serif*.ttf" in these dirs, avoiding italic variants
    for d in search_dirs:
        matches = glob.glob(os.path.join(d, "**", "*Serif*.ttf"), recursive=True)
        for match in matches:
            basename = os.path.basename(match).lower()
            if "italic" not in basename and "oblique" not in basename:
                return os.path.abspath(match)
    return None

SERIF_FONT_BASE = "CustomSerif"
USE_SERIF_TTF = False

def register_best_serif() -> str:
    """
    Try to register a found system TTF as the base serif font.
    Returns the font name to use for body text. Falls back to Times-Roman.
    Only registers regular (non-italic) variants.
    """
    global USE_SERIF_TTF
    ttf_path = find_serif_ttf()
    if ttf_path:
        try:
            pdfmetrics.registerFont(ttfonts.TTFont(SERIF_FONT_BASE, ttf_path))
            USE_SERIF_TTF = True
            print(f"[FONT] Registered system serif TTF: {ttf_path}")
            return SERIF_FONT_BASE
        except Exception as e:
            print(f"[FONT] Could not register TTF at {ttf_path}: {e}")
    # fallback
    print("[FONT] No preferred TTF found. Falling back to built-in Times-Roman.")
    return "Times-Roman"

BASE_SERIF = register_best_serif()

def serif_bold_name() -> str:
    # Never use bold or italic - always return the same regular font
    return BASE_SERIF

# -----------------------
# JSON reading & PDF building
# -----------------------
def read_json_input(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        items = []
        for i, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON on line {i}: {e}")
        return items
    raise ValueError("Unsupported JSON format")

def safe_get(obj: Dict[str, Any], keys: List[str], fallback: Optional[str] = None) -> Optional[str]:
    for k in keys:
        if k in obj and obj[k] is not None:
            v = obj[k]
            if isinstance(v, (str, int, float, bool)):
                return str(v)
            try:
                return json.dumps(v, ensure_ascii=False)
            except Exception:
                return str(v)
    return fallback

def make_paragraph(text: str, style) -> Paragraph:
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\r\n", "\n").replace("\r", "\n")
    safe = safe.replace("\n\n", "<br/><br/>").replace("\n", "<br/>")
    return Paragraph(safe, style)

def build_pdf(items: List[Dict[str, Any]], out_path: str, title: Optional[str] = None) -> None:
    margin = PAGE_MARGIN_MM * mm
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=title or "Conversation Export",
        author="make_nice_pdf.py",
    )

    styles = getSampleStyleSheet()

    # Typography: body uses BASE_SERIF with BODY_FONT_SIZE and leading = BODY_FONT_SIZE * LEADING_MULTIPLIER
    leading = float(BODY_FONT_SIZE) * float(LEADING_MULTIPLIER)

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName=BASE_SERIF,  # Use regular font, not bold
        fontSize=18,
        spaceAfter=HEADING_SPACE * 1.2,
        alignment=TA_LEFT,
    )
    role_style = ParagraphStyle(
        "RoleHeading",
        parent=styles["Heading3"],
        fontName=BASE_SERIF,  # Use regular font, not bold
        fontSize=11.5,
        leading=leading,
        spaceBefore=HEADING_SPACE,
        spaceAfter=6,
        textColor=colors.HexColor("#0b2a4a"),
    )
    content_style = ParagraphStyle(
        "Content",
        parent=styles["BodyText"],
        fontName=BASE_SERIF,
        fontSize=BODY_FONT_SIZE,
        leading=leading,
        spaceAfter=max(6, int(leading * 0.35)),
        alignment=TA_JUSTIFY,
    )
    toc_style = ParagraphStyle(
        "TOC",
        parent=styles["Normal"],
        fontName=BASE_SERIF,
        fontSize=10,
        leading=12,
    )

    story = []
    story.append(Paragraph(title or "LLM Conversation Export", title_style))
    story.append(Paragraph(f"Generated: {datetime.datetime.now().astimezone().isoformat(timespec='seconds')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    counts: Dict[str, int] = {}
    for it in items:
        role = safe_get(it, ["agent_name", "agent_id", "role"], fallback="Unknown") or "Unknown"
        counts[role] = counts.get(role, 0) + 1

    if counts:
        toc_lines = ["<b>Participants ({}):</b>".format(len(counts))]  # Keep this <b> tag for emphasis
        for role, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            toc_lines.append(f"{role}: {cnt} message{'s' if cnt != 1 else ''}")
        story.append(Paragraph("<br/>".join(toc_lines), toc_style))
        story.append(Spacer(1, 12))

    if not items:
        story.append(Paragraph("No messages found in input file.", styles["Normal"]))
        doc.build(story)
        return

    total = len(items)
    for idx, item in enumerate(items, start=1):
        role = safe_get(item, ["agent_name", "agent_id", "role"], fallback="Unknown") or "Unknown"
        content = safe_get(item, ["content", "message", "text", "artifact"], fallback="(no content)") or "(no content)"

        story.append(Paragraph(role, role_style))
        story.append(make_paragraph(content, content_style))
        story.append(Spacer(1, 6))

        if idx % SEPARATOR_EVERY == 0:
            story.append(Paragraph("—", styles["Normal"]))
            story.append(Spacer(1, 6))

        if idx % ITEMS_PER_PAGE_BREAK == 0 and idx < total:
            story.append(PageBreak())

        if idx % PROGRESS_CHUNK == 0 or idx == total:
            percent = math.floor((idx / total) * 100)
            print(f"[{idx}/{total}] messages rendered ({percent}%).")

    try:
        doc.build(story)
    except Exception as e:
        raise RuntimeError(f"Failed to generate PDF: {e}")

# -----------------------
# Venv cleanup (auto remove on success)
# -----------------------
def cleanup_venv_on_success() -> None:
    """
    Remove the .venv directory used for this run.
    Only called after a successful PDF build. If deletion fails, warn but continue.
    """
    vpath = venv_path()
    if not os.path.isdir(vpath):
        print("[CLEANUP] No .venv to remove.")
        return
    try:
        print(f"[CLEANUP] Removing venv at {vpath} ...")
        shutil.rmtree(vpath, ignore_errors=False)
        print("[CLEANUP] .venv removed.")
    except Exception as e:
        print(f"[CLEANUP] Warning: failed to remove .venv: {e}")

# -----------------------
# CLI / main
# -----------------------
def main(argv: List[str]) -> int:
    if len(argv) < 3:
        print("Usage: python3 make_nice_pdf.py <input.json> <output.pdf>")
        return 2

    in_path = os.path.expanduser(argv[1])
    out_path = os.path.expanduser(argv[2])

    in_path = os.path.normpath(in_path)
    out_path = os.path.normpath(out_path)

    print(f"[INFO] Reading input file: {in_path}")
    try:
        items = read_json_input(in_path)
    except Exception as e:
        print(f"[ERROR] Failed to read input file: {e}")
        return 4

    print(f"[INFO] Parsed {len(items)} messages. Generating PDF -> {out_path}")

    out_dir = os.path.dirname(out_path) or "."
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        print(f"[ERROR] Could not create output directory {out_dir}: {e}")
        return 3

    # Build PDF and on success attempt venv cleanup
    try:
        build_pdf(items, out_path, title="LLM Conversation Export")
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        traceback.print_exc()
        # leave venv intact for debugging
        return 5

    # If we got here, PDF build succeeded. Remove .venv now to avoid orphaning it.
    try:
        cleanup_venv_on_success()
    except Exception as e:
        print(f"[WARN] cleanup step failed: {e}")

    print("[INFO] Done. PDF created successfully.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
