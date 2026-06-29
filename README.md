\# Aerial Building Footprint Extractor



A geospatial computer vision pipeline that extracts building footprints from aerial imagery and converts them into vectorised GeoJSON polygons for downstream GIS use.



\## Features



\* Downloads or loads aerial imagery for a selected area

\* Runs zero-shot building segmentation using the Segment Anything Model

\* Generates raster masks for detected building regions

\* Converts segmented regions into vector polygons

\* Calculates per-building geometry and area information

\* Exports building footprints as GeoJSON

\* Produces interactive visualisations for reviewing extracted footprints

\* Supports downstream workflows in QGIS and other GIS platforms



\## Tech Stack



\* Python

\* Segment Anything Model

\* SAMGeo

\* PyTorch

\* Rasterio

\* Shapely

\* GeoPandas

\* NumPy

\* GDAL-compatible geospatial processing

\* GeoJSON

\* HTML visualisation



\## Project Structure



\* `download\_data.py` — downloads or prepares aerial imagery

\* `segment.py` — runs SAM-based building segmentation

\* `vectorize.py` — converts raster masks into vector polygons

\* `visualize.py` — creates interactive footprint visualisations

\* `fix.py` — utility script for geometry or output corrections

\* `requirements.txt` — Python dependencies



\## Installation



Create and activate a virtual environment, then install the required packages:



```

pip install -r requirements.txt

```



\## Workflow



1\. Download or place aerial imagery inside the local `data/` directory.



2\. Run the segmentation pipeline:



&#x20;  python segment.py



3\. Convert the generated masks into GeoJSON polygons:



&#x20;  python vectorize.py



4\. Generate the interactive visualisation:



&#x20;  python visualize.py



\## Output



The pipeline can generate:



\* Building segmentation masks

\* Vectorised building footprint polygons

\* GeoJSON files

\* Interactive HTML maps

\* Per-building area and geometry metadata



\## Applications



\* Urban planning

\* Property and infrastructure analysis

\* GIS automation

\* Disaster assessment

\* Mapping and geospatial intelligence

\* Automated building inventory generation



\## Notes



The `data/` and `outputs/` folders are excluded from version control because they may contain large imagery files and generated results.



Model weights and virtual environments are also excluded from this repository.



