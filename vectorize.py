import numpy as np
import rasterio
import rasterio.features
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from pathlib import Path

# Paths
MASK_DIR = Path("outputs/masks")
GEOJSON_DIR = Path("outputs/geojson")
GEOJSON_DIR.mkdir(parents=True, exist_ok=True)

TILE_NAME = "austin_demo"
INPUT_MASK = MASK_DIR / f"{TILE_NAME}_mask.tif"
OUTPUT_GEOJSON = GEOJSON_DIR / f"{TILE_NAME}_footprints.geojson"

# Filtering thresholds
MIN_AREA_M2 = 20      
MAX_AREA_M2 = 50000   
SIMPLIFY_TOLERANCE = 0.5


def mask_to_polygons(mask_path: Path) -> gpd.GeoDataFrame:
    print(f"[read] {mask_path}")

    with rasterio.open(mask_path) as src:
        mask = src.read(1).astype(np.uint8)
        transform = src.transform
        crs = src.crs

        print(f"  CRS:        {crs}")
        print(f"  Resolution: {src.res[0]:.2f}m/px")
        print(f"  Shape:      {mask.shape}")
        print(f"  Non-zero px: {np.count_nonzero(mask):,}")

        shapes = list(rasterio.features.shapes(mask, transform=transform))

    print(f"\n[vectorize] {len(shapes):,} raw shapes extracted")

    polygons = []
    for geom, value in shapes:
        if value == 0:
            continue
        poly = shape(geom)
        if not poly.is_valid:
            poly = poly.buffer(0)  
        polygons.append(poly)

    print(f"[filter] {len(polygons):,} foreground polygons before area filter")

    if crs and crs.is_geographic:
        min_area = MIN_AREA_M2 / 1.2e10
        max_area = MAX_AREA_M2 / 1.2e10
    else:
        min_area = MIN_AREA_M2
        max_area = MAX_AREA_M2

    filtered = [
        p.simplify(SIMPLIFY_TOLERANCE if not (crs and crs.is_geographic) else SIMPLIFY_TOLERANCE / 111000)
        for p in polygons
        if min_area <= p.area <= max_area
    ]

    print(f"[filter] {len(filtered):,} polygons after area filter ({MIN_AREA_M2}–{MAX_AREA_M2} m²)")

    gdf = gpd.GeoDataFrame(
        {"building_id": range(len(filtered)), "area_m2": [round(p.area, 2) for p in filtered]},
        geometry=filtered,
        crs=crs,
    )

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        print("[reproject] Converting to EPSG:4326 (WGS84)")
        gdf = gdf.to_crs(epsg=4326)
        gdf["area_m2"] = gdf.geometry.to_crs(epsg=3857).area.round(2)

    return gdf


def save_geojson(gdf: gpd.GeoDataFrame, output_path: Path):
    gdf.to_file(output_path, driver="GeoJSON")
    size_kb = output_path.stat().st_size / 1e3
    print(f"\n[saved] {output_path}")
    print(f"  Features: {len(gdf):,} building footprints")
    print(f"  File size: {size_kb:.1f} KB")
    print(f"  Bounds: {gdf.total_bounds.round(6).tolist()}")


def main():
    print("=== Mask → GeoJSON Vectorization ===\n")

    if not INPUT_MASK.exists():
        raise FileNotFoundError(
            f"Mask not found: {INPUT_MASK}\n"
            "Run src/segment.py first."
        )

    gdf = mask_to_polygons(INPUT_MASK)
    save_geojson(gdf, OUTPUT_GEOJSON)

    print("\nNext step: run src/visualize.py")


if __name__ == "__main__":
    main()