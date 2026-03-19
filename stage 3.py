# Basic run (default filename): python "stage 3.py" https://raw.githubusercontent.com/python/cpython/main/README.rst
# Custom filename: python "stage 3.py" https://raw.githubusercontent.com/python/cpython/main/README.rst -o python_readme.rst
import os
import argparse
import requests
from urllib.parse import urlparse, unquote
from tqdm import tqdm

def download_file(url, output_filename=None):
    # determine filename
    parsed_url = urlparse(url)
    default_filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file.html"
    filename = output_filename or default_filename

    # download with progress bar
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        total_size = int(res.headers.get("content-length", 0))

        # initialize progress bar
        progress_bar = tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=filename,
            leave=True
        )

        with open(filename, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)
                progress_bar.update(len(chunk))
        progress_bar.close()

    print(f"download completed: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wget tool (Stage 3)")
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="custom output filename (optional)")
    args = parser.parse_args()

    download_file(args.url, args.output)