from base64 import b64encode
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

    for src in soup.find_all(src=True):
        if src["src"]:
            src_parsed = urlparse(src["src"])
            if (src_parsed.scheme and src_parsed.netloc) or src_parsed.path or src_parsed.scheme != "data":
                if src_parsed.scheme and src_parsed.netloc:
                    src_url = src["src"]
                elif src["src"].startswith("//"):
                    final_url = requests.head(
                        url,
                        headers=headers or {},
                        proxies=proxies or {},
                        allow_redirects=True,
                    ).url
                    scr_scheme = "https" if final_url.startswith("https://") else "http"
                    src_url = scr_scheme + "://" + src["src"].replace("//", "")
                else:
                    src_url = base_url + src["src"]

                logger.info(f"Downloading {src_url}")
                if src.name == "script" or src.name == "style":
                    src_r = requests.get(
                        src_url, headers=headers or {}, proxies=proxies or {}
                    )
                    del src["src"]
                    src.string = src_r.text
                elif src.name == "iframe":
                    pass
                elif src.name in ["img"]:
                    src_r = requests.get(
                        src_url, headers=headers or {}, proxies=proxies or {}
                    )

                    mime_type = src_r.headers['Content-Type']
                    b64_src = b64encode(src_r.content).decode('utf-8')
                    src["src"] = f"data:{mime_type};base64,{b64_src}"

    with open("test.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify())


if __name__ == "__main__":
    webonefile(
        "https://github.com/",
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        },
    )
