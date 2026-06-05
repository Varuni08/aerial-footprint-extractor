import torch
from pathlib import Path
from samgeo import SamGeo

# Paths
DATA_DIR = Path("data/raw")
MASK_DIR = Path("outputs/masks")
MASK_DIR.mkdir(parents=True, exist_ok=True)

SAM_MODEL = "vit_b"
SAM_CHECKPOINT = "sam_vit_b_01ec64.pth"

TILE_NAME = "austin_demo"
INPUT_TILE = DATA_DIR / f"{TILE_NAME}.tif"
OUTPUT_MASK = MASK_DIR / f"{TILE_NAME}_mask.tif"
OUTPUT_GEOJSON = MASK_DIR / f"{TILE_NAME}_segments.geojson"


def get_device():
    if torch.cuda.is_available():
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"[gpu] CUDA available — {vram:.1f}GB VRAM")
        return "cuda"
    print("[cpu] No CUDA detected, falling back to CPU")
    return "cpu"


def run_segmentation(input_path: Path, output_mask: Path, output_geojson: Path):
    print(f"\n=== SAM Segmentation ===")
    print(f"Input:  {input_path}")
    print(f"Output: {output_mask}\n")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Tile not found: {input_path}\n"
            "Run download_data.py first."
        )

    device = get_device()

    sam = SamGeo(
        model_type=SAM_MODEL,
        checkpoint=SAM_CHECKPOINT,
        device=device,
        erosion_kernel=(3, 3),
        mask_multiplier=255,
        sam_kwargs=None,
    )

    print("[sam] Running automatic mask generation...")
    print("      This takes 1-3 minutes\n")

    # Generate segmentation mask
    sam.generate(
        source=str(input_path),
        output=str(output_mask),
        foreground=True,
        erosion_kernel=(3, 3),
        mask_multiplier=255,
    )

    print(f"\n[done] Mask saved: {output_mask}")

    # Convert mask to GeoJSON
    print("[sam] Converting mask to GeoJSON...")
    sam.tiff_to_geojson(
        input=str(output_mask),
        output=str(output_geojson),
    )
    print(f"[done] GeoJSON saved: {output_geojson}")



def main():
    run_segmentation(INPUT_TILE, OUTPUT_MASK, OUTPUT_GEOJSON)


if __name__ == "__main__":
    main()