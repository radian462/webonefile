import base64
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def webonefile(url: str, headers: dict = {}, proxies: dict = {}) -> str:
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    
    for src in soup.find_all(src=True):
        if src['src']:
            src_parsed = urlparse(src['src'])
            if (src_parsed.hostname and src_parsed.scheme) or src_parsed.path:
                print(src.name)
                
    

if __name__ == "__main__":
    webonefile(
        "http://web.archive.org/web/20241118000048/https://google.com/",
        headers={
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "ja,en-US;q=0.9,en;q=0.8",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        },
    )
