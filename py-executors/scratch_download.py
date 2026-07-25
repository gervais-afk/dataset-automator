import urllib.request
import time
import sys

url = "https://files.pythonhosted.org/packages/69/71/a9e9a06418832fbea9d7cefda585d53395358d498537b6bdd3cf7364cd29/catboost-1.2.10-cp313-cp313-win_amd64.whl"
filename = "catboost-1.2.10-cp313-cp313-win_amd64.whl"

def report(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    if duration > 0:
        speed = int(progress_size / (1024 * duration))
    else:
        speed = 0
    percent = min(int(count*block_size*100/total_size), 100)
    sys.stdout.write(f"\rDownloading: {percent}% | {progress_size / (1024 * 1024):.2f} MB / {total_size / (1024 * 1024):.2f} MB | Speed: {speed} KB/s | Time: {duration:.1f}s")
    sys.stdout.flush()

print("Starting download...")
start_time = time.time()
try:
    urllib.request.urlretrieve(url, filename, report)
    print("\nDownload finished successfully!")
except Exception as e:
    print(f"\nError: {e}")
