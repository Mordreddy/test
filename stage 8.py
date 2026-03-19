# 1. Basic resumable download (large file for testing):
#    python "stage8.py" https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --resume -o linux-6.6.tar.xz
# 2. Test resume with small file (add 0.1s delay in code for manual interrupt):
#    python "stage8.py" http://httpbin.org/range/100000 --resume -o range_test.bin
# 3. Disable resume (force re-download):
#    python "stage8.py" https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz --no-resume -o linux-6.6.tar.xz
# 4. Full params (auth + custom header + resume):
#    python "stage8.py" http://httpbin.org/basic-auth/testuser/testpass --resume -o auth_resume.bin --user testuser --password testpass --header "User-Agent: MyWgetTool/1.0"

# Test URL Notes:
# - https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.tar.xz: 150MB file (supports resume, valid SSL certificate)
# - http://httpbin.org/range/100000: Small test file (100KB, supports Range/206 Partial Content, no SSL issue)
# - Avoid https://speed.hetzner.de/100MB.bin (expired SSL certificate)import os
import time
import argparse
import requests
from urllib.parse import urlparse, unquote
from requests.exceptions import HTTPError, TooManyRedirects, Timeout, ConnectionError
from requests.auth import HTTPBasicAuth


def download_file(url, output_filename=None, retries=3, timeout=10, max_redirects=5, username=None, password=None,
                  headers=None, resume=True):
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

    # Check existing file size if resume is enabled
    if resume and os.path.exists(filename):
        downloaded_size = os.path.getsize(filename)
        print(f"Resuming download: {filename} (already downloaded: {downloaded_size} bytes)")
    else:
        # Overwrite existing file if resume is disabled
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
            with session.get(url, stream=True, allow_redirects=True, timeout=timeout, auth=auth, headers=req_headers,
                             verify=False) as res:
                res.raise_for_status()
                final_url = res.url

                # Check if server supports partial content (206) or full content (200)
                if res.status_code == 206:
                    # Resume mode: server supports range requests
                    total_size = downloaded_size + int(res.headers.get("content-length", 0))
                    mode = "ab"
                    print(f"Server supports resume (206 Partial Content). Total size: {total_size} bytes")
                else:
                    # No resume support: re-download full file
                    total_size = int(res.headers.get("content-length", 0))
                    mode = "wb"  # Overwrite file
                    if resume and downloaded_size > 0:
                        print(f"Server does not support resume (200 OK). Re-downloading full file...")
                        downloaded_size = 0

                # Step 3: Download with progress
                start_time = time.time()
                total_downloaded = downloaded_size  # Include existing bytes
                last_progress = int((downloaded_size / total_size) * 100) if total_size > 0 else 0

                with open(filename, mode) as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_downloaded += len(chunk)
                            current_time = time.time()
                            total_time_elapsed = current_time - start_time + 1e-6

                            # Calculate speed and progress
                            avg_speed = (total_downloaded - downloaded_size) / total_time_elapsed
                            if total_size > 0:
                                progress = min((total_downloaded / total_size) * 100, 100.0)
                                remaining_size = max(total_size - total_downloaded, 0)
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

                            # Update progress only on integer change
                            if int(progress) > last_progress:
                                print(
                                    f"\rProgress: {progress:.1f}% | {total_downloaded}/{total_size if total_size > 0 else '?'} B | Speed: {speed_str} | ETA: {eta_str}",
                                    end="",
                                    flush=True
                                )
                                last_progress = int(progress)

                print(f"\nDownload completed: {filename}")
                print(f"Final URL (after redirects): {final_url}")
                return

        except (HTTPError, TooManyRedirects, Timeout, ConnectionError) as e:
            if attempt < retries:
                print(f"\nAttempt {attempt + 1} failed: {str(e)[:100]}")
                print(f"Retrying in 2 seconds (remaining retries: {retries - attempt})...")
                time.sleep(2)
            else:
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
    parser = argparse.ArgumentParser(description="Simple wget tool (Stage 8 - Full Features)")
    # Core params (from previous stages)
    parser.add_argument("url", help="URL of the file to download")
    parser.add_argument("-o", "--output", help="Custom output filename (optional)")
    parser.add_argument("--retry", type=int, default=3, help="Number of retries on failure (default: 3)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--user", help="Username for Basic HTTP authentication (optional)")
    parser.add_argument("--password", help="Password for Basic HTTP authentication (optional)")
    parser.add_argument("--header", action="append", default=[],
                        help="Custom request header (format: Key:Value, multiple allowed)")
    # Fixed resume params (switch type, no value needed)
    parser.add_argument("--resume", action='store_true', default=True, help="Enable resume download (default: enabled)")
    parser.add_argument("--no-resume", action='store_false', dest='resume',
                        help="Disable resume download (force re-download)")

    args = parser.parse_args()
    # Parse custom headers
    headers = {}
    for h in args.header:
        if ":" in h:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()

    # Run download
    download_file(
        url=args.url,
        output_filename=args.output,
        retries=args.retry,
        timeout=args.timeout,
        username=args.user,
        password=args.password,
        headers=headers,
        resume=args.resume
    )