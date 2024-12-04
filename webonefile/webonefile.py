from base64 import b64encode
import os
from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def webonefile(url: str, headers: dict = None, proxies: dict = None) -> str:
    logger = getLogger("Webonefile")
    handler = StreamHandler()
    logger.setLevel(INFO)
    formatter = Formatter("[%(levelname)s] %(message)s - %(asctime)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    base_url = urlparse(url).scheme + "://" + urlparse(url).netloc

    r = requests.get(url, headers=headers or {}, proxies=proxies or {})
    soup = BeautifulSoup(r.text, "html.parser")

    resource_tags = soup.find_all(src=True)

    for tag in resource_tags:
        tag_parsed = urlparse(tag["src"])
        if (
            (tag_parsed.scheme and tag_parsed.netloc)
            or tag_parsed.path
            and tag_parsed.scheme != "data"
        ):
            if tag_parsed.scheme and tag_parsed.netloc:
                tag_url = tag["src"]
            elif tag["src"].startswith("//"):
                final_url = requests.head(
                    url,
                    headers=headers or {},
                    proxies=proxies or {},
                    allow_redirects=True,
                ).url
                scheme = "https" if final_url.startswith("https://") else "http"
                tag_url = scheme + "://" + tag["src"].replace("//", "")
            else:
                tag_url = base_url + tag["src"]

        if tag["src"]:
            logger.info(f"Downloading {tag_url}")

            b64_template = "data:%s/%s;base64,%s"
            if tag.name in ["img"]:
                src_r = requests.get(
                    tag_url, headers=headers or {}, proxies=proxies or {}
                )

                src_ext = os.path.splitext(tag_parsed.path)[1][1:]
                mime_type = "image"
                b64_src = b64encode(src_r.content).decode("utf-8")
                tag["src"] = b64_template % (mime_type, src_ext, b64_src)

    with open("test.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify())


if __name__ == "__main__":
    webonefile("https://google.co.jp")
