from datetime import date
from pathlib import Path
import csv
import io
import json
import re
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from build import build
from collectors import namebio
from records import stat_cells


class MarketTests(unittest.TestCase):
    def test_real_capture_and_reported_window_semantics(self):
        edition = json.loads((ROOT / "data/market.json").read_text())
        names = {r["extension"]: r for r in edition["records"]}
        self.assertTrue({".ca", ".games", ".lol"} <= names.keys())
        self.assertIn("1y", names[".ca"]["periods"])
        self.assertTrue(all(r["periods"]["all"]["sale_count"] > 0 for r in names.values()))
        self.assertTrue(re.fullmatch("[0-9a-f]{64}", edition["source_sha256"]))
        self.assertIn("—", stat_cells({"sale_count": 0, "price_sum": 0, "price_avg": 0, "price_max": 0}))

    def test_invalid_or_truncated_refresh_keeps_last_good_result(self):
        with tempfile.TemporaryDirectory() as d:
            original = (ROOT / "data/market.json").read_bytes()
            path = Path(d) / "market.json"
            path.write_bytes(original)
            with self.assertRaises(ValueError):
                namebio.refresh(path, date.today(), b"error page")
            self.assertEqual(path.read_bytes(), original)

    def test_new_compound_idn_and_duplicate_extension(self):
        headings = ["extension"] + [f"{p}_{f}" for p in namebio.PERIODS for f in namebio.FIELDS]
        fp = io.StringIO()
        w = csv.DictWriter(fp, headings)
        w.writeheader()
        row = {h: 0 for h in headings}
        row.update(
            extension=".café.uk", all_sale_count=1, all_price_avg=200, all_price_sum=200, all_price_max=200
        )
        w.writerow(row)
        result = namebio.parse(fp.getvalue().encode(), date.today())
        self.assertEqual(result["records"][0]["extension"], ".café.uk")
        self.assertRegex(result["records"][0]["slug"], r"^tld-[a-z0-9]+(?:-[a-z0-9]+)*$")
        w.writerow(row)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            namebio.parse(fp.getvalue().encode(), date.today())

    def test_trailing_space_rows_preserve_complementary_published_windows(self):
        columns = ["extension"] + [f"{p}_{f}" for p in namebio.PERIODS for f in namebio.FIELDS]
        stream = io.StringIO()
        writer = csv.DictWriter(stream, columns)
        writer.writeheader()
        source = dict.fromkeys(columns, 0)
        writer.writerow({**source, "extension": ".bot", "all_sale_count": 78, "1y_sale_count": 47})
        writer.writerow({**source, "extension": ".bot ", "all_retail_sale_count": 47, "5y_sale_count": 78})
        edition = namebio.parse(stream.getvalue().encode(), date.today())
        self.assertEqual(edition["source_rows"], 2)
        self.assertEqual(len(edition["records"]), 1)
        periods = edition["records"][0]["periods"]
        self.assertEqual(
            [periods[p]["sale_count"] for p in ("all", "1y", "all_retail", "5y")], [78, 47, 47, 78]
        )

    def test_all_routes_have_one_canonical_and_capture_backs_the_default(self):
        build(ROOT)
        site = ROOT / "dist"
        data = json.loads((site / "data/market.json").read_text())
        urls = [e.text for e in ET.parse(site / "sitemap.xml").findall(".//{*}loc")]
        self.assertEqual(len(set(urls)), len(data["records"]) + 1)
        for url in urls:
            path = site / url.split("/domainalmanac/", 1)[1] / "index.html"
            html = path.read_text()
            self.assertEqual(html.count('rel="canonical"'), 1)
            self.assertIn(f'rel="canonical" href="{url}"', html)
        home = (site / "index.html").read_text()
        self.assertNotIn("{{", home)
        self.assertIn("NameBio", home)
        self.assertIn("Voice.com", home)
        self.assertIn('rel="canonical" href="https://coolcode.ca/domainalmanac/"', home)
        self.assertEqual(
            json.loads((site / "data/status.json").read_text())["extensions"], len(data["records"])
        )
