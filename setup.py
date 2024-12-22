from setuptools import setup
import os

here = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

INSTALL_REQUIRES = []
with open(os.path.join(here, "requirements.txt")) as r:
    for rq in r.readlines():
        INSTALL_REQUIRES.append(rq.strip("\n"))

EXTRAS_REQUIRE = {
    "browser": ["playwright"],
}

DESCRIPTION = "A library for downloading a website into a single file"
NAME = "webonefile"
AUTHOR = "radian462"
AUTHOR_EMAIL = "no-number-email@proton.me"
URL = "https://github.com/radian462/webonefile"
LICENSE = "MIT License"
KEYWORDS = "webonefile,website,archive,downloader"
DOWNLOAD_URL = "https://github.com/radian462/webonefile"
VERSION = "0.1.0"
PYTHON_REQUIRES = ">=3.8"
PACKAGES = ["webonefile"]
CLASSIFIERS = [
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3 :: Only",
]

with open("README-EN.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name=NAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license=LICENSE,
    keywords=KEYWORDS,
    url=URL,
    version=VERSION,
    download_url=DOWNLOAD_URL,
    python_requires=PYTHON_REQUIRES,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    packages=PACKAGES,
    classifiers=CLASSIFIERS,
)
