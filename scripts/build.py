"""Build the captured market edition without network requests."""

from html import escape
import json
from pathlib import Path
import re
import shutil
import tempfile
from records import stat_cells, write_records
from search_metadata import add_search_metadata

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT):
    edition = json.loads((root / "data/market.json").read_text(encoding="utf-8"))
    defaults = json.loads((root / "config/market.json").read_text())
    tool = json.loads((root / "tool.json").read_text())
    rows = edition["records"]
    records = {r["extension"]: r for r in rows}
    if (
        len(records) != len(rows)
        or len({r["slug"] for r in rows}) != len(rows)
        or not all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", r["slug"]) for r in rows)
    ):
        raise ValueError("Invalid or duplicate extension route")
    period = defaults["period"]
    if (
        len(defaults["defaults"]) != 3
        or set(defaults["defaults"]) - set(records)
        or period not in edition["definitions"]
    ):
        raise ValueError("Default comparison does not exist in this capture")
    edition["presets"] = defaults
    output = root / "dist"
    source = root / "web"
    if output.is_symlink() or source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Unsafe symlink in website paths")
    with tempfile.TemporaryDirectory(dir=root) as temp:
        stage = Path(temp) / "site"
        shutil.copytree(source, stage)
        (stage / "data").mkdir()
        (stage / "data/market.json").write_text(
            json.dumps(edition, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        (stage / "data/status.json").write_text(
            json.dumps({"checked_at": edition["checked_at"], "extensions": len(rows)}) + "\n"
        )
        write_records(stage, edition)
        default_rows = []
        highest = max(records[e]["periods"][period]["sale_count"] for e in defaults["defaults"])
        for ext in defaults["defaults"]:
            r = records[ext]
            default_rows.append(
                f'<tr><th scope="row"><a href="./records/{r["slug"]}/">{escape(ext)}</a></th>{stat_cells(r["periods"][period], highest)}</tr>'
            )
        replacements = {
            "TITLE": escape(tool["title"]),
            "DESCRIPTION": escape(tool["description"], quote=True),
            "CHECKED_AT": edition["checked_at"],
            "COUNT": f"{len(rows):,}",
            "DEFAULT_COMPARISON": "".join(default_rows),
            "DEFAULT_PERIOD": escape(edition["definitions"][period]),
            "SOURCE_URL": escape(tool["source"], quote=True),
            "VISIT_COUNTER": '<script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script>',
            "ISSUE_LINK": '<a href="https://coolcode.ca/report/?tool=domainalmanac" referrerpolicy="no-referrer">Report an issue</a>',
        }
        template = stage / "index.html"
        page = template.read_text(encoding="utf-8")
        for k, v in replacements.items():
            page = page.replace("{{" + k + "}}", v)
        if "{{" in page:
            raise ValueError("Unresolved homepage template marker")
        template.write_text(
            add_search_metadata(page, tool, category="FinanceApplication"), encoding="utf-8"
        )
        (stage / ".nojekyll").touch()
        if output.exists():
            shutil.rmtree(output)
        stage.rename(output)
    print(f"Built {len(rows):,} extension records, the directory and the market comparison")


if __name__ == "__main__":
    build()
