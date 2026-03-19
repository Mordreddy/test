# Basic run: python "stage 4.py" https://raw.githubusercontent.com/python/cpython/main/README.rst
#Custom filename: python "stage 4.py" https://raw.githubusercontent.com/python/cpython/main/README.rst -o python_readme.rst
import os
import time
import argparse
import requests
from urllib.parse import urlparse, unquote

def download_file(url, output_filename=None):
    parsed_url = urlparse(url)
    default_filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file.html"
    filename = output_filename or default_filename

    # stream download with speed and ETA
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        total_size = int(res.headers.get("content-length", 0))
        downloaded = 0
        start_time = time.time()
        total_downloaded = 0
        last_progress = 0

        with open(filename, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    total_downloaded += len(chunk)
                    current_time = time.time()
                    total_time_elapsed = current_time - start_time + 1e-6
                    avg_speed = total_downloaded / total_time_elapsed

                    if total_size > 0:
                        progress = min((downloaded / total_size) * 100, 100.0)
                        remaining_size = max(total_size - downloaded, 0)
                        eta = remaining_size / avg_speed if avg_speed > 0 else 0
                    else:
                        progress = 0
                        eta = 0

                    if avg_speed < 1024:
                        speed_str = f"{avg_speed:.2f} B/s"
                    elif avg_speed < 1024 * 1024:
                        speed_str = f"{avg_speed / 1024:.2f} KB/s"
                    else:
                        speed_str = f"{avg_speed / (1024 * 1024):.2f} MB/s"

                    eta_str = time.strftime("%H:%M:%S", time.gmtime(eta)) if eta > 0 else "N/A"

                    if int(progress) > last_progress:
                        print(
                            f"\rprogross: {progress:.1f}% / {downloaded}/{total_size if total_size > 0 else '?'} B / speed: {speed_str} / ETA: {eta_str}",
                            end="",
                            flush=True
                        )
                        last_progress = int(progress)

    print(f"\ndownlaod complet: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="wget tool (Stage 4)")
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="custom output filename")
    args = parser.parse_args()

    download_file(args.url, args.output)