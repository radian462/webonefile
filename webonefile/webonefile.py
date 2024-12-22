from base64 import b64encode
import html
from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO
import time
from traceback import format_exc
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .exception import RetryLimitExceededError


class browser:
    def __init__(self) -> None:
        self.logger = getLogger("Webonefile")
        handler = StreamHandler()
        formatter = Formatter("[%(levelname)s] %(message)s - %(asctime)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(INFO)

        # Quotation from https://github.com/rajatomar788/pywebcopy/blob/9f35b4b6a4da2125e70d8f7a21100de1f09012f4/pywebcopy/urls.py
        self.common_suffix_map = {
            "application/epub+zip": "epub",  # Electronic publication (EPUB)
            "application/javascript": "js",  # JavaScript module
            "application/gzip": "gz",  # GZip Compressed Archive
            "application/java-archive": "jar",  # Java Archive (JAR)
            "application/json": "json",  # JSON format
            "application/ld+json": "jsonld",  # JSON-LD format
            "application/msword": "doc",  # Microsoft Word
            "application/octet-stream": "bin",  # Any kind of binary data
            "application/ogg": "ogx",  # OGG
            "application/pdf": "pdf",  # Adobe Portable Document Format (PDF)
            "application/php": "php",  # Hypertext Preprocessor (Personal Home Page)
            "application/rtf": "rtf",  # Rich Text Format (RTF)
            "application/vnd.amazon.ebook": "azw",  # Amazon Kindle eBook format
            "application/vnd.apple.installer+xml": "mpkg",  # Apple Installer Package
            "application/vnd.mozilla.xul+xml": "xul",  # XUL
            "application/vnd.ms-excel": "xls",  # Microsoft Excel
            "application/vnd.ms-fontobject": "eot",  # MS Embedded OpenType fonts
            "application/vnd.ms-powerpoint": "ppt",  # Microsoft PowerPoint
            "application/vnd.oasis.opendocument.presentation": "odp",  # OpenDocument presentation document
            "application/vnd.oasis.opendocument.spreadsheet": "ods",  # OpenDocument spreadsheet document
            "application/vnd.oasis.opendocument.text": "odt",  # OpenDocument text document
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",  # Microsoft PowerPoint (OpenXML)
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",  # Microsoft Excel (OpenXML)
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",  # Microsoft Word (OpenXML)
            "application/vnd.rar": "rar",  # RAR archive
            "application/vnd.visio": "vsd",  # Microsoft Visio
            "application/x-7z-compressed": "7z",  # 7-zip archive
            "application/x-abiword": "abw",  # AbiWord document
            "application/x-bzip": "bz",  # BZip archive
            "application/x-bzip2": "bz2",  # BZip2 archive
            "application/x-csh": "csh",  # C-Shell script
            "application/x-freearc": "arc",  # Archive document (multiple files embedded)
            "application/x-sh": "sh",  # Bourne shell script
            "application/x-shockwave-flash": "swf",  # Small web format (SWF) or Adobe Flash document
            "application/x-tar": "tar",  # Tape Archive (TAR)
            "application/xhtml+xml": "xhtml",  # XHTML
            "application/xml": "xml",  # XML
            "text/xml": "xml",  # XML
            "application/zip": "zip",  # ZIP archive
            "audio/aac": "aac",  # AAC audio
            "audio/midi": "mid",  # Musical Instrument Digital Interface (MIDI)
            "audio/x-midi": "midi",  # Musical Instrument Digital Interface (MIDI)
            "audio/mpeg": "mp3",  # MP3 audio
            "audio/ogg": "oga",  # OGG audio
            "audio/opus": "opus",  # Opus audio
            "audio/wav": "wav",  # Waveform Audio Format
            "audio/webm": "weba",  # WEBM audio
            "font/otf": "otf",  # OpenType font
            "font/ttf": "ttf",  # TrueType Font
            "font/woff": "woff",  # Web Open Font Format (WOFF)
            "font/woff2": "woff2",  # Web Open Font Format (WOFF)
            "image/bmp": "bmp",  # Windows OS/2 Bitmap Graphics
            "image/gif": "gif",  # Graphics Interchange Format (GIF)
            "image/jpeg": "jpeg",  # JPEG images
            "image/jpg": "jpg",  # JPG images
            "image/png": "png",  # Portable Network Graphics
            "image/svg+xml": "svg",  # Scalable Vector Graphics (SVG)
            "image/tiff": "tiff",  # Tagged Image File Format (TIFF)
            "image/x-icon": "ico",  # Icon format
            "image/vnd.microsoft.icon": "ico",  # Icon format
            "image/webp": "webp",  # WEBP image
            "text/calendar": "ics",  # iCalendar format
            "text/css": "css",  # Cascading Style Sheets (CSS)
            "text/csv": "csv",  # Comma-separated values (CSV)
            "text/html": "html",  # HyperText Markup Language (HTML)
            "text/javascript": "mjs",  # JavaScript module
            "text/plain": "txt",  # Text, (generally ASCII or ISO 8859-n)
            "video/3gpp": "3gp",  # 3GPP audio/video container
            "audio/3gpp": "3gp",  # 3GPP audio/video container
            "video/3gpp2": "3g2",  # 3GPP2 audio/video container
            "audio/3gpp2": "3g2",  # 3GPP2 audio/video container
            "video/mp2t": "ts",  # MPEG transport stream
            "video/mpeg": "mpeg",  # MPEG Video
            "video/ogg": "ogv",  # OGG video
            "video/webm": "webm",  # WEBM video
            "video/x-msvideo": "avi",  # AVI: Audio Video Interleave
            "video/mp4": "mp4",  # MP4 video
        }

        self.resource_type = {"img": "image", "audio": "audio", "video": "video"}

    def webonefile(
        self,
        url: str,
        headers: dict | None = None,
        proxies: dict | None = None,
        ignore_robots: bool = True,
        cool_times: float | None = None,
        max_tries: int = 3,
        debug: bool = False,
    ) -> str:
        # Fetch robots.txt
        def get_robots() -> dict:
            robots_rules = {}
            robots = self.session.get(f"{ROOT_DIRECTORY}/robots.txt")

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

        def make_b64(url: str) -> str:
            b64_template = "data:%s/%s;base64,%s"
            r = self.session.get(url)

            content_type = r.headers.get("Content-Type")
            b64_src = b64encode(r.content).decode("utf-8")
            return b64_template % (
                self.resource_type.get(tag.name),
                self.common_suffix_map[content_type],
                b64_src,
            )

        headers = headers or {}
        proxies = proxies or {}

        if cool_times is None:
            cool_times = 0

        if debug == True:
            self.logger.setLevel(DEBUG)
        else:
            self.logger.setLevel(INFO)

        PARSED_URL = urlparse(url)
        ROOT_DIRECTORY = PARSED_URL.scheme + "://" + PARSED_URL.netloc
        SCHEME = PARSED_URL.scheme

        self.session = requests.Session()
        self.session.headers.update(headers)
        self.session.proxies.update(proxies)

        for i in range(max_tries):
            try:
                r = self.session.get(url)
                break
            except Exception as e:
                self.logger.debug(f"Attempt {i + 1} failed\n{format_exc()}")
                if i + 1 == max_tries:
                    raise RetryLimitExceededError(format_exc())

        soup = BeautifulSoup(r.text, "html.parser")

        resource_tags = (
            soup.find_all(src=True)
            + soup.find_all(srcset=True)
            + soup.find_all(attrs={"data-srcset": True})
            + soup.find_all("link")
        )

        # Save resource
        for tag in resource_tags:
            if tag.get("src"):
                tag_url = resolve_url(tag["src"])
                tag_parsed = urlparse(tag_url)

                if tag_parsed.scheme != "data":
                    if tag.name and tag.name in self.resource_type.keys():
                        self.logger.info(f"Downloading {tag_url}")
                        for i in range(max_tries):
                            try:
                                tag["src"] = make_b64(tag_url)
                                break
                            except Exception as e:
                                self.logger.debug(f"Attempt {i + 1} failed\n{format_exc()}")
                                if i + 1 == max_tries:
                                    raise RetryLimitExceededError(format_exc())

                    elif tag.name in ["script"]:
                        self.logger.info(f"Downloading {tag_url}")
                        for i in range(max_tries):
                            try:
                                script_text = self.session.get(tag_url).text

                                escaped_script = html.escape(script_text)
                                tag.string = escaped_script
                                break
                            except Exception as e:
                                self.logger.debug(f"Attempt {i + 1} failed\n{format_exc()}")
                                if i + 1 == max_tries:
                                    raise RetryLimitExceededError(format_exc())

            elif tag.get("srcset") or tag.get("data-srcset"):
                attr = "srcset" if tag.get("srcset") else "data-srcset"
                tag_url = resolve_url(tag[attr])
                tag_parsed = urlparse(tag_url)

                if tag_parsed.scheme != "data":
                    self.logger.info(f"Downloading {tag_url}")
                    for i in range(max_tries):
                        try:
                            tag[attr] = make_b64(tag_url)
                            break
                        except Exception as e:
                            self.logger.debug(f"Attempt {i + 1} failed\n{format_exc()}")
                            if i + 1 == max_tries:
                                raise RetryLimitExceededError(format_exc())

            elif tag.name == "link":
                if "stylesheet" in tag.get("rel"):
                    if tag.get("href"):
                        origin_url = tag["href"]
                    elif tag.get("data-href"):
                        origin_url = tag["data-href"]

                    tag_url = resolve_url(origin_url)

                    self.logger.info(f"Downloading {tag_url}")
                    for i in range(max_tries):
                        try:
                            css_text = self.session.get(tag_url).text
                            break
                        except Exception as e:
                            self.logger.debug(f"Attempt {i + 1} failed\n{format_exc()}")
                            if i + 1 == max_tries:
                                raise RetryLimitExceededError(format_exc())

                    style_tag = soup.new_tag("style")
                    style_tag.string = css_text
                    tag.replace_with(style_tag)

            time.sleep(cool_times)

        # Convert URL to absolute path
        for tag in soup.find_all(href=True):
            tag["href"] = resolve_url(tag["href"])

        with open("test.html", "w", encoding="utf-8") as file:
            file.write(soup.prettify())

