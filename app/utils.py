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
    else:
        # st.info("Reading GeoJSON/JSON file ...")
        df = gpd.read_file(uploaded_file)  # Geojson etc.

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
