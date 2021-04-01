# vector-validator

Validates and automatically fixes your geospatial vector data. 

Build with streamlit. [Live >here<](https://share.streamlit.io/chrieke/aoi-validator/main/app/aoi_validator.py).

Validates and attempts to fix:
- No Self-Intersection
- No Holes
- Counterclockwise winding

Accepted data formats:
- File Upload:
    - GeoJSON
    - JSON
    - KML
    - WKT
    - Shapefile (Zipfile containing shp,dbf,prj,shx files)
- Copy-paste:
    - GeoJSON FeatureCollection 
    - Feature
    - Geometry
    - Coordinates
    - bbox

