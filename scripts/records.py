"""Build the no-JavaScript edition and the child sitemap from published statistics."""

from collections import defaultdict
from html import escape
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

BASE = "https://coolcode.ca/domainalmanac/"
ORDER = ("1w", "1m", "3m", "1y", "2y", "3y", "5y", "all", "all_retail", "all_wholesale")


def usd(value):
    return "${:,.2f}".format(value).removesuffix(".00")


def stat_cells(stats, highest_count=None):
    count = stats["sale_count"]
    measure = f"{count:,}"
    if highest_count:
        width = round(100 * count / highest_count, 1)
        measure = f'<span class="count-value" style="--share:{width}%">{count:,}</span>'
    return (
        f"<td>{measure}</td><td>{usd(stats['price_sum'])}</td>"
        f"<td>{usd(stats['price_avg']) if count else '—'}</td><td>{usd(stats['price_max']) if count else '—'}</td>"
    )


def frame(route, title, summary, body):
    root = "../../" if route else "../"
    url = BASE + "records/" + route
    return f'''<!doctype html><html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{escape(summary, quote=True)}"><title>{escape(title)} · Domain Market Almanac</title><link rel="canonical" href="{url}"><link rel="icon" href="{root}favicon.svg"><link rel="stylesheet" href="{root}style.css"><script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head><body class="profile" data-tool="domainalmanac"><header class="mast"><nav><a href="{root}">Domain Market Almanac</a><a href="{root}records/">Extension directory</a></nav></header><main>{body}</main><footer>Reported sales statistics courtesy of <a href="https://namebio.com/">NameBio</a>. <a href="{root}#sources">Methods and sources</a> · <a href="https://coolcode.ca/">CoolCode.ca</a></footer></body></html>'''


def describe(record):
    ext = record["extension"]
    annual = record["periods"]["1y"]
    n = annual["sale_count"]
    if n == 0:
        all_time = record["periods"]["all"]["sale_count"]
        return f"NameBio shows {all_time:,} recorded {ext} sales all-time and zero in the past year."
    unit = "sale" if n == 1 else "sales"
    return f"NameBio reports {n:,} {ext} {unit} totaling US{usd(annual['price_sum'])} in the past year."


def write_records(stage, edition):
    rows = edition["records"]
    dest = stage / "records"
    dest.mkdir()
    windows = edition["definitions"]
    date = edition["checked_at"]
    ordered = sorted(rows, key=lambda r: (r["periods"]["all"]["sale_count"], r["extension"]))
    directory = defaultdict(list)
    urls = [BASE + "records/"]
    for i, r in enumerate(ordered):
        ext = r["extension"]
        name = escape(ext)
        route = r["slug"] + "/"
        title = ext + " reported domain sales and prices"
        summary = describe(r)
        nearby = ordered[max(0, i - 1) : i] + ordered[i + 1 : i + 2]
        others = "".join(
            f'<li><a href="../{o["slug"]}/">{escape(o["extension"])}</a> · {o["periods"]["all"]["sale_count"]:,} recorded sales all-time</li>'
            for o in nearby
        )
        query = urlencode(
            {
                "tld": ext[1:],
                "compare": nearby[0]["extension"][1:] if nearby else "",
                "also": "",
                "period": "1y",
            }
        )
        period_rows = "".join(
            f'<tr><th scope="row">{escape(windows[p])}</th>{stat_cells(r["periods"][p])}</tr>'
            for p in ORDER
        )
        body = f'''<nav class="trail" aria-label="Breadcrumb"><a href="../">Extension directory</a></nav><h1>{name} domain sales</h1><p class="lede">{escape(summary)} Figures are in US dollars. Source checked <time datetime="{date}">{date}</time>.</p><a class="action" href="../../?{escape(query, quote=True)}">Compare {name} with another extension</a>
<section><h2>Reported sales by time window</h2><div class="table-wrap" tabindex="0" aria-label="{name} sales breakdown"><table><thead><tr><th scope="col">Window</th><th scope="col">Sales</th><th scope="col">Total USD</th><th scope="col">Average USD</th><th scope="col">Highest USD</th></tr></thead><tbody>{period_rows}</tbody></table></div><p class="small">Rolling windows overlap. An em dash means the window had zero recorded sales. The retail and wholesale categories are published only for the all-time period.</p></section>
<section><h2>Explore similar-sized samples</h2><p>These extensions sit next to {name} in order of all-time recorded sales. Compare how their reported prices and recent activity differ.</p><ul>{others}</ul></section><section><h2>Source and scope</h2><p>These figures come from NameBio’s public TLDStats and cover reported aftermarket transactions. The dataset supplies counts and USD aggregates. It does not identify which names sold in a particular window. Individual asking prices and registration fees are separate measures. <a href="{escape(edition["source_url"], quote=True)}">Read NameBio’s definitions</a> · <a href="{escape(edition["download_url"], quote=True)}">Open the publisher’s extension data</a>.</p></section>'''
        path = dest / r["slug"]
        path.mkdir()
        (path / "index.html").write_text(frame(route, title, summary, body), encoding="utf-8")
        urls.append(BASE + "records/" + route)
        letter = ext[1].upper() if ext[1].isascii() and ext[1].isalpha() else "Other"
        directory[letter].append(r)
    sections = []
    for group, items in sorted(directory.items()):
        links = "".join(
            f'<li><a href="{r["slug"]}/">{escape(r["extension"])}</a> · {r["periods"]["all"]["sale_count"]:,} sales</li>'
            for r in sorted(items, key=lambda r: r["extension"])
        )
        sections.append(
            f'<section id="group-{group}"><h2>{group}</h2><ul class="extension-list">{links}</ul></section>'
        )
    jumps = " ".join(f'<a href="#group-{letter}">{letter}</a>' for letter in sorted(directory))
    summary = f"Explore {len(rows):,} domain extensions with at least one sale reported to NameBio. Each profile includes rolling windows and all-time retail and wholesale statistics."
    body = (
        f'<div class="intro"><h1>Domain extension directory</h1><p>{summary}</p><p>Counts in this directory are all-time. Source checked {date}.</p></div><nav class="subnav" aria-label="Jump to letter">{jumps}</nav>'
        + "".join(sections)
    )
    (dest / "index.html").write_text(
        frame("", "Reported domain sales by extension", summary, body), encoding="utf-8"
    )
    sitemap = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in sorted(urls):
        ET.SubElement(ET.SubElement(sitemap, "url"), "loc").text = url
    ET.ElementTree(sitemap).write(stage / "sitemap.xml", encoding="utf-8", xml_declaration=True)
