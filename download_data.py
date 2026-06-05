import os
import urllib.request
from pathlib import Path

DATA_DIR = Path("data/raw")

SOURCES = [
    {
        "name": "austin_demo",
        "url": "https://prd-tnm.s3.amazonaws.com/StagedProducts/NAIP/tx/2020/100cm/rgbir_cog/30097/m_3009741_ne_14_060_20200824.tif",
        "desc": "NAIP 2020 Austin TX (USGS public)"
    },
]

def download_tile(name: str, url: str, desc: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{name}.tif"

    if out_path.exists():
        size_mb = out_path.stat().st_size / 1e6
        print(f"[skip] {name}.tif already exists ({size_mb:.1f} MB)")
        return out_path

    print(f"[download] {desc}")
    print(f"  URL: {url}")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(downloaded / total_size * 100, 100)
            mb = downloaded / 1e6
            print(f"\r  {pct:.1f}% ({mb:.1f} MB)", end="", flush=True)
        else:
            print(f"\r  {downloaded/1e6:.1f} MB downloaded", end="", flush=True)

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(out_path, "wb") as f:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        block = 8192
        while True:
            chunk = response.read(block)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = min(downloaded / total * 100, 100)
                print(f"\r  {pct:.1f}% ({downloaded/1e6:.1f} MB)", end="", flush=True)
            else:
                print(f"\r  {downloaded/1e6:.1f} MB", end="", flush=True)

    print()
    size_mb = out_path.stat().st_size / 1e6
    print(f"[done] {out_path} ({size_mb:.1f} MB)")
    return out_path


def main():
    print("=== Aerial Footprint Extractor — Data Download ===\n")
    for src in SOURCES:
        try:
            path = download_tile(src["name"], src["url"], src["desc"])
            print(f"\nNext step: python segment.py\n")
            return
        except Exception as e:
            print(f"\n[error] {e}")
            print("Trying next source...\n")

    print("\n[fallback] All auto-downloads failed.")
    print("Manual option: download any aerial GeoTIFF and place it at data/raw/austin_demo.tif")
    print("Good sources:")
    print("  https://earthexplorer.usgs.gov  (NAIP tiles, free account)")
    print("  https://openaerialmap.org       (community aerial imagery)")


if __name__ == "__main__":
    main()