"""Test the comparison, navigation, fallback and phone layout under a real project subpath."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
import json
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    screenshots = ROOT / "browser-checks"
    screenshots.mkdir(exist_ok=True)
    with TemporaryDirectory() as temp:
        shutil.copytree(ROOT / "dist", Path(temp) / "domainalmanac")
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=temp))
        Thread(target=server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{server.server_port}/domainalmanac/"
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(executable_path=os.getenv("CHROMIUM_PATH"))
                page = browser.new_page(viewport={"width": 1150, "height": 820})
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(url)
                page.locator("#controls").wait_for()
                assert page.locator("#results tr").count() == 3
                page.get_by_label("First extension", exact=True).fill(".com")
                page.get_by_label("Third extension", exact=True).fill("")
                page.locator("#period").select_option("3m")
                page.get_by_role("button", name="Compare sales").click()
                assert "tld=com" in page.url and "period=3m" in page.url
                assert page.locator("#results tr").count() == 2
                page.reload()
                page.locator("#controls").wait_for()
                assert (
                    page.locator("#tld").input_value() == ".com"
                    and page.locator("#period").input_value() == "3m"
                )
                page.get_by_role("link", name=".com", exact=True).click()
                assert page.locator("h1").text_content() == ".com domain sales"
                page.get_by_role("link", name="Compare .com with another extension").click()
                page.locator("#controls").wait_for()
                assert page.locator("#tld").input_value() == ".com"
                page.locator("#also").fill(".no-such-extension-example")
                page.get_by_role("button", name="Compare sales").click()
                assert "No published extension" in page.locator("#feedback").text_content()
                page.goto(url)
                page.locator("#controls").wait_for()
                page.screenshot(path=str(screenshots / "desktop.png"))
                page.set_viewport_size({"width": 360, "height": 780})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(screenshots / "mobile.png"))
                off = browser.new_context(java_script_enabled=False, viewport={"width": 360, "height": 780})
                static = off.new_page()
                static.goto(url)
                assert static.locator("#results tr").count() == 3
                static.get_by_role("link", name=".ca", exact=True).click()
                assert static.locator("h1").text_content() == ".ca domain sales"
                assert static.locator("tbody tr").count() == 10
                assert not errors, errors
                browser.close()
        finally:
            server.shutdown()
    print("Passed desktop, mobile, shared URL, input, directory/profile and no-JavaScript browser checks.")


if __name__ == "__main__":
    main()
