import base64
import re
import uuid
from typing import Union, Dict
from pathlib import Path

import requests
import streamlit as st
import geojson
from geojson import Feature, FeatureCollection
import geopandas as gpd
from geopandas import GeoDataFrame
import pandas as pd
import shapely
from shapely.geometry import Polygon, box, mapping
from fiona.io import ZipMemoryFile


GITHUB_RIBBON = (
    '<a href="https://github.com/chrieke/vector-validator" class="github-corner" aria-label="View source '
    'on GitHub"><svg width="70" height="70" viewBox="0 0 250 250" style="fill:#151513; color:#fff; position: '
    'absolute; top: 0; border: 0; right: 0;" aria-hidden="true"><path d="M0,0 L115,115 L130,115 L142,142 '
    'L250,250 L250,0 Z"></path><path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 '
    "120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,"
    '103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path><path d="M115.0,115.0 '
    "C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 "
    "C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 "
    "187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,"
    "96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,"
    '136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path></svg></a><style>.github-corner:'
    "hover .octo-arm{animation:octocat-wave 560ms ease-in-out}@keyframes octocat-wave{0%,100%{transform:rotate(0)}20%,60%"
    "{transform:rotate(-25deg)}40%,80%{transform:rotate(10deg)}}@media (max-width:500px){.github-corner:hover "
    ".octo-arm{animation:none}.github-corner .octo-arm{animation:octocat-wave 560ms ease-in-out}}</style>"
)


def read_vector_file_to_df(
    uploaded_file: st.uploaded_file_manager.UploadedFile,
) -> Union[GeoDataFrame, None]:
    """

    Args:
        uploaded_file: A single bytesIO like object

    Returns:
        Geopandas dataframe
    """
    filename = uploaded_file.name
    suffix = Path(filename).suffix
    if suffix == ".kml":
        # st.info("Reading KML file ...")
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        df = gpd.read_file(uploaded_file, driver="KML")
    elif suffix == ".wkt":
        # st.info("Reading WKT file ...")
        wkt_string = uploaded_file.read().decode("utf-8")
        df = pd.DataFrame({"geometry": [wkt_string]})
        df["geometry"] = df["geometry"].apply(shapely.wkt.loads)
        df = gpd.GeoDataFrame(df, geometry="geometry", crs=4326)
    elif suffix == ".zip":
        # st.info("Reading zipped Shapefile ...")
        with (ZipMemoryFile(uploaded_file)) as memfile:
            with memfile.open() as src:
                crs = src.crs
                df = gpd.GeoDataFrame.from_features(src, crs=crs)
                if df.crs is None:
                    st.error("The provided shapefile has no crs!")
                    st.stop()
    elif suffix == ".gpkg":
        # st.info("Reading GeoPackage file ...")
        df = gpd.read_file(uploaded_file)
    else:
        # st.info("Reading GeoJSON/JSON file ...")
        df = gpd.read_file(uploaded_file)

    return df


def read_json_string_to_df(json_string: str) -> GeoDataFrame:
    geom_json = geojson.loads(json_string.replace("'", '"'))
    if isinstance(geom_json, dict):
        if geom_json["type"] == "FeatureCollection":
            # st.info("Reading FeatureCollection ...")
            fc = geom_json
        if geom_json["type"] == "Feature":
            # st.info("Reading Feature ...")
            fc = FeatureCollection(features=[geom_json])
        elif geom_json["type"] in [
            "Polygon",
            "MultiPolygon",
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "LinearRing",
        ]:
            # st.info("Reading Geometry ...")
            fc = FeatureCollection([Feature(geometry=geom_json)])
    elif isinstance(geom_json, list):
        if len(geom_json) == 4 and isinstance(geom_json[0], float):
            # st.info("Reading bbox (Polygon) ...")
            geometry = mapping(box(*geom_json))
            fc = FeatureCollection([Feature(geometry=geometry)])
        elif isinstance(geom_json[0], list) and isinstance(geom_json[0][0], list):
            # st.info("Reading Coordinates (Polygon)...")
            geometry = {"type": "Polygon", "coordinates": geom_json}
            fc = FeatureCollection([Feature(geometry=geometry)])
    else:
        st.error(
            "Could not read json string! Check missing brackets! Only FeatureCollection, "
            "Feature, Geometry, Coordinates, or bbox are allowed!"
        )
        st.stop()
    df = gpd.GeoDataFrame.from_features(fc, crs="EPSG:4326")
    return df


def close_holes(poly: Polygon) -> Polygon:
    """
    Close polygon holes by limitation to the exterior ring.
    Args:
        poly: Input shapely Polygon
    Example:
        df.geometry.apply(lambda p: close_holes(p))
    """
    if poly.interiors:
        return Polygon(list(poly.exterior.coords))
    else:
        return poly


def download_button(
    object_to_download,
    download_filename,
    button_text,
    st_element=None,  # , pickle_it=False
) -> None:
    """
    Generates a link to download the given object_to_download.

    From: https://discuss.streamlit.io/t/a-download-button-with-custom-css/4220
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """
    # if pickle_it:
    #     try:
    #         object_to_download = pickle.dumps(object_to_download)
    #     except pickle.PicklingError as e:
    #         st.write(e)
    #         return None

    # else:
    #     if isinstance(object_to_download, bytes):
    #         pass

    #     elif isinstance(object_to_download, pd.DataFrame):
    #         object_to_download = object_to_download.to_csv(index=False)

    #     # Try JSON encode for everything else
    #     else:
    #         object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace("-", "")
    button_id = re.sub("\d+", "", button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = (
        custom_css
        + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br><br>'
    )
    # dl_link = f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}"><input type="button" kind="primary" value="{button_text}"></a><br></br>'

    if st_element is not None:
        st_element.markdown(dl_link, unsafe_allow_html=True)
    else:
        st.markdown(dl_link, unsafe_allow_html=True)


def load_lottieurl(url: str) -> Dict:
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
