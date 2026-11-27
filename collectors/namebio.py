"""Collect NameBio's public TLDStats once per edition and publish only validated aggregate records."""

from argparse import ArgumentParser
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import csv
import io
import json
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD = "https://api.namebio.com/tldstats-download"
DOCS = "https://api.namebio.com/docs/"
PERIODS = {
    "1y": "Past year",
    "1m": "Past month",
    "3m": "Past 3 months",
    "1w": "Past week",
    "2y": "Past 2 years",
    "3y": "Past 3 years",
    "5y": "Past 5 years",
    "all": "All recorded sales",
    "all_retail": "All-time retail",
    "all_wholesale": "All-time wholesale",
}
FIELDS = ("sale_count", "price_sum", "price_avg", "price_max", "price_stddev")


def extension_slug(extension):
    if not extension.startswith("."):
        raise ValueError(f"Unexpected extension {extension!r}")
    labels = extension[1:].split(".")
    if not labels or any(not label for label in labels):
        raise ValueError("Empty extension label")
    ascii_labels = [label.encode("idna").decode("ascii").lower() for label in labels]
    if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in ascii_labels):
        raise ValueError(f"Invalid label {extension!r}")
    # The source contains compound suffixes such as .co.uk and Unicode IDNs. Encode
    # any punctuation unambiguously, staying within the hub sitemap slug alphabet.
    return "tld-" + "-d-".join(
        re.sub(r"-+", lambda m: "-h" + str(len(m[0])) + "-", label) for label in ascii_labels
    )


def amount(value):
    try:
        n = Decimal(value)
    except (TypeError, InvalidOperation) as e:
        raise ValueError(f"Unrecognised statistic {value!r}") from e
    if not n.is_finite() or n < 0:
        raise ValueError("Expected a nonnegative finite statistic")
    return int(n) if n == n.to_integral_value() else float(n)


def parse(content, checked):
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    columns = {"extension"} | {f"{p}_{f}" for p in PERIODS for f in FIELDS}
    if not columns.issubset(reader.fieldnames or []):
        raise ValueError("Unexpected NameBio CSV header")
    groups = {}
    rows = 0
    for row in reader:
        rows += 1
        extension = row["extension"].strip().lower()
        slug = extension_slug(extension)
        periods = {}
        for p in PERIODS:
            values = {f: amount(row[p + "_" + f]) for f in FIELDS}
            if not isinstance(values["sale_count"], int) or (
                not values["sale_count"] and any(values.values())
            ):
                raise ValueError("Inconsistent sample size for " + extension)
            periods[p] = values
        if slug not in groups:
            groups[slug] = {"extension": extension, "slug": slug, "periods": periods}
            continue
        # The official CSV splits .bot between ".bot" and ".bot " with
        # complementary populated windows. Keep each published window once.
        existing = groups[slug]["periods"]
        for key, stats in periods.items():
            if stats["sale_count"]:
                if existing[key]["sale_count"]:
                    raise ValueError("Duplicate populated window " + key + " for " + extension)
                existing[key] = stats
    records = []
    for record in groups.values():
        periods = record["periods"]
        if periods["all"]["sale_count"]:
            records.append(record)
        elif any(stats["sale_count"] for stats in periods.values()):
            raise ValueError("Window sales without an all-time sample: " + record["extension"])
    if not records:
        raise ValueError("Empty aggregate edition")
    return {
        "checked_at": checked.isoformat(),
        "source_url": DOCS,
        "download_url": DOWNLOAD,
        "source_sha256": sha256(content).hexdigest(),
        "source_rows": rows,
        "attribution": "Sales statistics courtesy of NameBio. Prices in US dollars. Coverage is limited to sales reported to the publisher.",
        "definitions": PERIODS,
        "records": sorted(records, key=lambda r: r["extension"]),
    }


def refresh(path, checked, content=None):
    if content is None:
        request = Request(
            DOWNLOAD,
            headers={"User-Agent": "CoolCode Domain Market Almanac (+https://coolcode.ca/domainalmanac/)"},
        )
        with urlopen(request, timeout=90) as response:
            content = response.read()
    edition = parse(content, checked)
    previous = json.loads(path.read_text()) if path.exists() else None
    if len(edition["records"]) < 300 or (
        previous and len(edition["records"]) < len(previous["records"]) * 0.8
    ):
        raise ValueError("Coverage dropped unexpectedly; previous capture retained")
    if previous and checked < date.fromisoformat(previous["checked_at"]):
        raise ValueError("A newer capture already exists")
    path.parent.mkdir(exist_ok=True, parents=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, encoding="utf-8", delete=False) as fp:
        json.dump(edition, fp, ensure_ascii=False, separators=(",", ":"))
        fp.write("\n")
    Path(fp.name).replace(path)
    print(f"Captured {len(edition['records'])} extensions with recorded sales on {checked}")


if __name__ == "__main__":
    p = ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, help="Replay an official CSV download")
    p.add_argument("--as-of", type=date.fromisoformat, help="Original UTC retrieval date of a saved file")
    p.add_argument("--output", type=Path, default=ROOT / "data/market.json")
    a = p.parse_args()
    if bool(a.csv) != bool(a.as_of):
        p.error("When replaying include both --csv and --as-of")
    refresh(a.output, a.as_of or datetime.now(timezone.utc).date(), a.csv.read_bytes() if a.csv else None)
