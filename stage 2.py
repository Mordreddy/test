import os
import argparse
import requests
from urllib.parse import urlparse, unquote

# 1. Basic run (default filename): python "stage 2.py" https://raw.githubusercontent.com/python/cpython/main/README.rst
# 2. Custom filename: python "stage 2.py" https://raw.githubusercontent.com/python/cpython/main/README.rst -o python_readme.rst
def download_file(url, output_filename=None):
    parsed_url = urlparse(url)
    default_filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file.html"
    filename = output_filename or default_filename

    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"dawnload complet: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wget tool")
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="custom output filename (optional)")
    args = parser.parse_args()

    download_file(args.url, args.output)