# vector-validator

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/chrieke/vector-validator/main/app/main.py)

Validates and automatically fixes your geospatial vector data. App build with [Streamlit](https://streamlit.io/). 
Select the validation options, upload/paste your vector data or try one of the examples.

<br>

---

<h3 align="center">
    🔺 <a href="https://share.streamlit.io/chrieke/vector-validator/main/app/main.py">Use the vector-validator app here!</a> 🔻
</h3>

---

<p align="center">
    <a href="https://share.streamlit.io/chrieke/vector-validator/main/app/main.py"><img src="images/screenshot.png" width=700></a>
</p>

## Functionality

**Validates and attempts to fix**:
- No Self-Intersection
- No Holes
- Counterclockwise winding

**Accepted data formats**:
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

## Development

**These steps are only required to work on the app.**

Install with:

```bash
git clone git@github.com:chrieke/vector-validator.git
cd vector-validator
pip install -r requirements.txt
```

And then start the Streamlit preview with:

```bash
streamlit run app/main.py
```