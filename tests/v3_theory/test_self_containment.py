"""Runtime code must not point at a sibling worktree."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_theory_sources_do_not_name_sibling_worktrees() -> None:
    needles = ("COMP 3314 GP/v1", "COMP 3314 GP/v2", "../v1", "../v2")
    roots = [ROOT / "method_extension" / "v3_theory", ROOT / "experiments" / "v3_theory", ROOT / "configs" / "v3"]
    for folder in roots:
        for path in folder.rglob("*"):
            if path.suffix not in {".py", ".yaml", ".yml", ".md"}:
                continue
            text = path.read_text(errors="ignore")
            for needle in needles:
                assert needle not in text, f"{path} contains {needle}"
