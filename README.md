# Domain Market Almanac

<!-- coolcode:guide -->
Compare the past year for .ca, .games and .lol, then open an extension for its longer record. Read the number of reported transactions beside the dollar average. A single sale can move a small sample considerably.
<!-- /coolcode:guide -->

[Open the comparison](https://coolcode.ca/domainalmanac/) · [Browse extension records](https://coolcode.ca/domainalmanac/records/)

## What is measured

The app reads the public [NameBio TLDStats documentation](https://api.namebio.com/docs/) and takes one daily copy of the [publisher’s complete aggregate CSV](https://api.namebio.com/tldstats-download). Each extension with at least one all-time recorded transaction receives a static profile. The CSV includes compound suffixes as well as top-level domains. The publisher splits some statistics for .bot across two spellings that differ by a trailing space. The importer normalises the spelling, keeps each populated window once and rejects overlapping populated windows. Amounts and totals are in USD. All-time retail and wholesale have separate source categories. The rolling windows combine reported sales and overlap one another. Private, unreported transactions are outside the sample. A zero count is meaningful, but a price average or highest price from zero sales is undefined. Prices charged for registration or renewal and unsold asking prices are different measures.

The comparison accepts any published extension, including IDNs. Its query parameters are `tld`, `compare`, `also` and `period`. Each profile includes a complete window table, source links and links to neighbouring extensions by all-time sample size. The site also links to a separate documented transaction, the $30 million cash sale of Voice.com detailed in [MicroStrategy’s SEC filing](https://www.sec.gov/Archives/edgar/data/1050446/000156459019026999/R19.htm), and to [CIRA’s Canadian registry report](https://www.cira.ca/en/resources/documents/about/fiscal-year-26-annual-report-to-members/). Registry portfolio counts describe registrations under management. They do not give a count of aftermarket transactions.

## Source and refresh

NameBio permits incorporation of its free aggregate endpoints into products with linked attribution. NameBio calculates its TLD statistics hourly at half past the hour and limits complete CSV downloads to one per hour. CoolCode schedules one download daily at 07:47 UTC and records the UTC capture date and SHA-256. No registration or paid API key is needed. Individual NameBio transactions, comparables, and daily-sale APIs are outside this edition. This app links to NameBio's own download for spreadsheet access. Source terms are in its [API documentation](https://api.namebio.com/docs/).

The offline build reads the last validated `data/market.json`. An unsuccessful download, malformed column, conflicting extension statistics, or unexpectedly small capture stops the scheduled workflow before any replacement or new deployment. The previous published site remains available. Git retains past committed editions. The browser reads a local snapshot after the page loads, and selections remain in the URL for sharing. Opening an explicitly linked external source visits its publisher.

## Expand or customize

```sh
python collectors/namebio.py
python -m unittest discover -s tests -v
node --test tests/*.test.mjs
python scripts/build.py
python -m http.server 8000 --directory dist
```

For an already downloaded authentic CSV, use `python collectors/namebio.py --csv FILE --as-of YYYY-MM-DD` with its actual capture date. The output path defaults to `data/market.json`. To change entry presets, edit `config/market.json`; every extension available in the capture remains selectable. The build workflow validates source, runs Chromium on the project subpath and preserves a deployable artifact. Successful main builds in the domainalmanac repository deploy the tested artifact to https://coolcode.ca/domainalmanac/ through GitHub Pages. PRs build and test locally retained data. The weekly schedule guard monitors only the two identified workflows and preserves manual disabling.
