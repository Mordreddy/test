# Basic run (default retry=3, timeout=10s): python "stage 6.py" https://raw.githubusercontent.com/python/cpython/main/README.rst
#Custom retry + timeout: python "stage 6.py" https://raw.githubusercontent.com/python/cpython/main/README.rst --retry 5 --timeout 15
# All params: python "stage 6.py" https://raw.githubusercontent.com/python/cpython/main/README.rst -o readme.rst --retry 2 --timeout 8

# Test URLs for retry/timeout functionality :
# - http://httpbin.org/delay/20: Triggers Timeout error (delays 20s, exceeds default 10s timeout)
# - http://httpbin.org/status/503: Triggers HTTP 503 error (Service Unavailable)
# - http://192.168.99.99:8080/test.txt: Triggers ConnectionError (non-existent IP/port)
# - http://test.loadimpact.com: Random 5xx errors/timeout (simulates unstable network\

import os
import time
import argparse
import requests
from urllib.parse import urlparse, unquote
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError

def download_file(url, output_filename=None, retries=3, timeout=10, max_redirects=5):
    # Initialize session for retry handling
    session = requests.Session()
    session.max_redirects = max_redirects

    # Retry loop
    for attempt in range(retries + 1):
        try:
            with session.get(url, stream=True, allow_redirects=True, timeout=timeout) as res:
                res.raise_for_status()
                final_url = res.url
                parsed_url = urlparse(final_url)
                default_filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file.html"
                filename = output_filename or default_filename

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

                            # Calculate average speed
                            avg_speed = total_downloaded / total_time_elapsed
                            # Calculate progress
                            if total_size > 0:
                                progress = min((downloaded / total_size) * 100, 100.0)
                                remaining_size = max(total_size - downloaded, 0)
                                eta = remaining_size / avg_speed if avg_speed > 0 else 0
                            else:
                                progress = 0
                                eta = 0

                            # Format speed
                            if avg_speed < 1024:
                                speed_str = f"{avg_speed:.2f} B/s"
                            elif avg_speed < 1024*1024:
                                speed_str = f"{avg_speed/1024:.2f} KB/s"
                            else:
                                speed_str = f"{avg_speed/(1024*1024):.2f} MB/s"
                            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta)) if eta > 0 else "N/A"

                            # Update progress
                            if int(progress) > last_progress:
                                print(
                                    f"\rProgress: {progress:.1f}% | {downloaded}/{total_size if total_size>0 else '?'} B | Speed: {speed_str} | ETA: {eta_str}",
                                    end="",
                                    flush=True
                                )
                                last_progress = int(progress)

                print(f"\nDownload completed: {filename}")
                print(f"Final URL (after redirects): {final_url}")
                return

        except (HTTPError, TooManyRedirects, Timeout, ConnectionError) as e:
            if attempt < retries:
                print(f"\nAttempt {attempt + 1} failed: {str(e)[:100]}")  # Shorten error msg
                print(f"Retrying in 2 seconds (remaining retries: {retries - attempt})...")
                time.sleep(2)
            else:
                # Final failure
                print(f"\nAll {retries + 1} attempts failed.")
                print(f"Last error: {str(e)[:100]}")
                print(f"URL: {url}")
        except Exception as e:
            print(f"\nUnexpected error (attempt {attempt + 1}): {str(e)[:100]}")
            if attempt < retries:
                print(f"Retrying in 2 seconds (remaining retries: {retries - attempt})...")
                time.sleep(2)
            else:
                print(f"\nAll {retries + 1} attempts failed.")
                print(f"URL: {url}")
            return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple wget tool Stage 6")
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="Custom output filename")
    parser.add_argument("--retry", type=int, default=3, help="Number of retries on failure (default: 3)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    args = parser.parse_args()

    download_file(args.url, args.output, args.retry, args.timeout)