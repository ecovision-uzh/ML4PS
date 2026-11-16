"""Summarise the problems found in notebooks executed with `jupyter nbconvert --execute --allow-errors`.

    python tools/nb_report.py executed/*.ipynb

For each notebook it lists, per code cell, the exceptions raised (name and first line of the message) and the
error-like lines printed by shell commands (`!cmd`), which do not raise. It also lists the distinct warnings.
It never prints cell sources, so it is safe to run on the solution notebooks.

Exit code 1 if any notebook raised an exception, 0 otherwise. Standard library only.
"""
import json
import re
import sys
from pathlib import Path

SHELL_ERROR = re.compile(r"command not found|not recognized as an internal|^\s*error[:\[]|^fatal:|^ERROR|No such file",
                         re.IGNORECASE)
WARNING = re.compile(r"\b\w*Warning\b:")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def first_line(text, limit=200):
    line = ANSI.sub("", text).strip().splitlines()[0] if text.strip() else ""
    return line if len(line) <= limit else line[: limit - 3] + "..."


def report(path):
    nb = json.loads(Path(path).read_text(encoding="utf-8"))
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    errors, shell_errors, warnings = [], [], {}
    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        for out in cell.get("outputs", []):
            if out["output_type"] == "error":
                errors.append((idx, out["ename"], first_line(out.get("evalue", ""))))
            elif out["output_type"] == "stream":
                for line in ANSI.sub("", "".join(out.get("text", ""))).splitlines():
                    if WARNING.search(line):
                        key = line.strip()[:200]
                        warnings.setdefault(key, idx)
                    elif SHELL_ERROR.search(line):
                        shell_errors.append((idx, line.strip()[:200]))
    print(f"== {path}")
    print(f"   {len(code_cells)} code cells, {len(errors)} exception(s), {len(shell_errors)} shell error line(s), "
          f"{len(warnings)} distinct warning(s)")
    for idx, ename, evalue in errors:
        print(f"   [cell {idx}] {ename}: {evalue}")
    for idx, line in shell_errors:
        print(f"   [cell {idx}] (shell) {line}")
    for line, idx in warnings.items():
        print(f"   [cell {idx}] (warning) {line}")
    return len(errors)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    n_errors = sum(report(p) for p in sys.argv[1:])
    sys.exit(1 if n_errors else 0)


if __name__ == "__main__":
    main()
