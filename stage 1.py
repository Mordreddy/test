import os
import requests
from urllib.parse import urlparse

def download_file(url):
    filename = os.path.basename(urlparse(url).path) or "index.html"
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"success download：{filename}")

if __name__ == "__main__":
    test_url = "https://raw.githubusercontent.com/python/cpython/main/README.rst"
    download_file(test_url)