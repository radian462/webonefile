from base64 import b64encode
import html
import os
from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def webonefile(
    url: str, headers: dict = None, proxies: dict = None, ignore_robots: bool = True
) -> str:
    headers = headers or {}
    proxies = proxies or {}

    logger = getLogger("Webonefile")
    handler = StreamHandler()
    logger.setLevel(INFO)
    formatter = Formatter("[%(levelname)s] %(message)s - %(asctime)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    PARSED_URL = urlparse(url)
    ROOT_DIRECTORY = PARSED_URL.scheme + "://" + PARSED_URL.netloc
    SCHEME = PARSED_URL.scheme

    r = requests.get(url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(r.text, "html.parser")

    resource_tags = soup.find_all(src=True) + soup.find_all("link")

    def get_robots() -> dict:
        robots_rules = {}
        robots = requests.get(
            f"{ROOT_DIRECTORY}/robots.txt", headers=headers, proxies=proxies
        )

        if robots.status_code == 200:
            for line in robots.text.split("\n"):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if line.lower().startswith("user-agent:"):
                    user_agent = line.split(":", 1)[1].strip()
                    robots_rules[user_agent] = {"Disallow": [], "Allow": []}
                elif line.lower().startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if user_agent and path:
                        robots_rules[user_agent]["Disallow"].append(path)
                elif line.lower().startswith("allow:"):
                    path = line.split(":", 1)[1].strip()
                    if user_agent and path:
                        robots_rules[user_agent]["Allow"].append(path)

            return robots_rules
        else:
            return {}

    def resolve_url(url: str) -> str:
        PARSED_RESOURCE = urlparse(url)
        if (
            PARSED_RESOURCE.scheme
            and PARSED_RESOURCE.scheme in ["data", "http", "https"]
        ) or url.startswith("#"):
            return url
        elif url.startswith("//"):
            return f"{SCHEME}:{url}"
        elif url.startswith("/"):
            return f"{ROOT_DIRECTORY}{url}"
        else:
            return f"{ROOT_DIRECTORY}/{url}"

    # リソース保存
    for tag in resource_tags:
        if tag.get("src"):
            tag_url = resolve_url(tag["src"])
            tag_parsed = urlparse(tag_url)

            b64_template = "data:%s/%s;base64,%s"
            if tag_parsed.scheme != "data":
                if tag.name in ["img"]:
                    logger.info(f"Downloading {tag_url}")
                    src_r = requests.get(tag_url, headers=headers, proxies=proxies)

                    src_ext = os.path.splitext(tag_parsed.path)[1][1:]
                    mime_type = "image"
                    b64_src = b64encode(src_r.content).decode("utf-8")
                    tag["src"] = b64_template % (mime_type, src_ext, b64_src)
                if tag.name in ["script"]:
                    logger.info(f"Downloading {tag_url}")
                    script_text = requests.get(
                        tag_url, headers=headers, proxies=proxies
                    ).text

                    escaped_script = html.escape(script_text)
                    tag.string = escaped_script

        elif tag.name == "link":
            if "stylesheet" in tag.get("rel"):
                if tag.get("href"):
                    origin_url = tag["href"]
                elif tag.get("data-href"):
                    origin_url = tag["data-href"]

                tag_url = resolve_url(origin_url)

                logger.info(f"Downloading {tag_url}")
                css_text = requests.get(tag_url, headers=headers, proxies=proxies).text

                style_tag = soup.new_tag("style")
                style_tag.string = css_text
                tag.replace_with(style_tag)

    # urlを絶対パス化
    for tag in soup.find_all(href=True):
        tag["href"] = resolve_url(tag["href"])

    with open("test.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify())


if __name__ == "__main__":
    webonefile("https://zenn.dev/radian462/articles/907966dde6cb9f")
