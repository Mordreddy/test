# 1. Python script: python "stage9.py" https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --resume -o linux-6.6.tar.xz
# 2. Binary exe: my_wget.exe https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --resume -o linux-6.6.tar.xz

import os
import time
import argparse
import threading
import requests
from urllib.parse import urlparse, unquote
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError, SSLError
from requests.auth import HTTPBasicAuth

# Global variables for thread-safe progress sharing
progress_data = {
    "total_downloaded": 0,
    "total_size": 0,
    "start_time": None,
    "is_running": False,
    "lock": threading.Lock()
}


def progress_display_thread():
    """Separate thread for real-time progress display """
    while progress_data["is_running"]:
        with progress_data["lock"]:
            total_downloaded = progress_data["total_downloaded"]
            total_size = progress_data["total_size"]
            start_time = progress_data["start_time"]

        if start_time and total_size > 0 and total_downloaded > 0:
            # Calculate speed and progress
            elapsed_time = time.time() - start_time + 1e-6
            avg_speed = total_downloaded / elapsed_time
            progress = min((total_downloaded / total_size) * 100, 100.0)
            remaining_size = max(total_size - total_downloaded, 0)
            eta = remaining_size / avg_speed if avg_speed > 0 else 0

            # Format speed and ETA
            if avg_speed < 1024:
                speed_str = f"{avg_speed:.2f} B/s"
            elif avg_speed < 1024 * 1024:
                speed_str = f"{avg_speed / 1024:.2f} KB/s"
            else:
                speed_str = f"{avg_speed / (1024 * 1024):.2f} MB/s"
            eta_str = time.strftime("%H:%M:%S", time.gmtime(eta)) if eta > 0 else "N/A"

            # Update progress
            print(
                f"\rProgress: {progress:.1f}% | {total_downloaded}/{total_size} B | Speed: {speed_str} | ETA: {eta_str}",
                end="",
                flush=True
            )
        time.sleep(0.1)  # Update progress every 100ms

def download_file(url, output_filename=None, retries=3, timeout=10, max_redirects=5,
                  username=None, password=None, headers=None, resume=True, buf_size=65536):  # 64KB buffer
    # Initialize session
    session = requests.Session()
    session.max_redirects = max_redirects
    if headers:
        session.headers.update(headers)
    auth = HTTPBasicAuth(username, password) if username and password else None

    # Step 1: Determine filename and check existing file for resume
    parsed_url = urlparse(url)
    default_filename = unquote(os.path.basename(parsed_url.path)) or "downloaded_file.bin"
    filename = output_filename or default_filename
    downloaded_size = 0

    if resume and os.path.exists(filename):
        downloaded_size = os.path.getsize(filename)
        print(f"Resuming download: {filename} (already downloaded: {downloaded_size} bytes)")
    else:
        if os.path.exists(filename):
            os.remove(filename)
        print(f"Starting new download: {filename}")

    # Retry loop
    for attempt in range(retries + 1):
        try:
            # Step 2: Build request headers
            req_headers = session.headers.copy()
            if resume and downloaded_size > 0:
                req_headers["Range"] = f"bytes={downloaded_size}-"

            # Send request
            with session.get(url, stream=True, allow_redirects=True, timeout=timeout,
                             auth=auth, headers=req_headers, verify=False) as res:
                res.raise_for_status()
                final_url = res.url

                # Check resume support
                if res.status_code == 206:
                    total_size = downloaded_size + int(res.headers.get("content-length", 0))
                    mode = "ab"
                    print(f"Server supports resume (206 Partial Content). Total size: {total_size} bytes")
                else:
                    total_size = int(res.headers.get("content-length", 0))
                    mode = "wb"
                    if resume and downloaded_size > 0:
                        print(f"Server does not support resume. Re-downloading full file...")
                        downloaded_size = 0

                # Initialize progress data for thread
                with progress_data["lock"]:
                    progress_data["total_downloaded"] = downloaded_size
                    progress_data["total_size"] = total_size
                    progress_data["start_time"] = time.time()
                    progress_data["is_running"] = True

                # Start progress display thread
                progress_thread = threading.Thread(target=progress_display_thread, daemon=True)
                progress_thread.start()

                # Step 3: Download with optimized buffer size (64KB)
                with open(filename, mode) as f:
                    for chunk in res.iter_content(chunk_size=buf_size):  # Use 64KB buffer
                        if chunk:
                            f.write(chunk)
                            # Update progress data
                            with progress_data["lock"]:
                                progress_data["total_downloaded"] += len(chunk)

                # Stop progress thread
                with progress_data["lock"]:
                    progress_data["is_running"] = False
                progress_thread.join()

                print(f"\nDownload completed: {filename}")
                print(f"Final URL: {final_url} | Buffer size: {buf_size / 1024} KB")
                return

        except HTTPError as e:
            if attempt < retries:
                print(f"\nAttempt {attempt + 1} failed: HTTP {e.response.status_code} - {e.response.reason}")
                print(f"Retrying in 2s (remaining: {retries - attempt})...")
                time.sleep(2)
            else:
                print(f"\nAll {retries + 1} attempts failed: HTTP {e.response.status_code}")
        except (TooManyRedirects, Timeout, ConnectionError, SSLError) as e:
            if attempt < retries:
                err_type = type(e).__name__
                print(f"\nAttempt {attempt + 1} failed: {err_type} - {str(e)[:80]}")
                print(f"Retrying in 2s (remaining: {retries - attempt})...")
                time.sleep(2)
            else:
                print(f"\nAll {retries + 1} attempts failed: {type(e).__name__}")
        except Exception as e:
            print(f"\nUnexpected error (attempt {attempt + 1}): {str(e)[:80]}")
            if attempt < retries:
                print(f"Retrying in 2s (remaining: {retries - attempt})...")
                time.sleep(2)
            else:
                print(f"\nAll {retries + 1} attempts failed.")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Wget Tool (Stage 9 - Threaded Progress + Optimized Buffer)")
    # Core params
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="Custom output filename (optional)")
    parser.add_argument("--retry", type=int, default=3, help="Retries on failure (default: 3)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in seconds (default: 10)")
    parser.add_argument("--user", help="Username for Basic auth (optional)")
    parser.add_argument("--password", help="Password for Basic auth (optional)")
    parser.add_argument("--header", action="append", default=[], help="Custom header (Key:Value, multiple allowed)")
    parser.add_argument("--resume", action='store_true', default=True, help="Enable resume (default: True)")
    parser.add_argument("--no-resume", action='store_false', dest='resume', help="Disable resume")
    parser.add_argument("--buf-size", type=int, default=65536, help="Buffer size in bytes (default: 65536 = 64KB)")

    args = parser.parse_args()

    # Parse headers
    headers = {}
    for h in args.header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    download_file(
        url=args.url,
        output_filename=args.output,
        retries=args.retry,
        timeout=args.timeout,
        username=args.user,
        password=args.password,
        headers=headers,
        resume=args.resume,
        buf_size=args.buf_size
    )