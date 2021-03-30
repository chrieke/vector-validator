"""
Contains the visual elements of the app.
"""

import json

import geojson
import streamlit as st
from shapely.geometry.polygon import orient
from geopandas import GeoDataFrame
import pandas_bokeh

pandas_bokeh.output_notebook()

import utils
from aoi import Aoi
import SessionState


FILETYPES = ["geojson", "json", "kml", "wkt", "zip"]
FILETYPES_SHAPEFILE = ["shp", "shx", "dbf", "prj"]
VALIDATION_OPTIONS = [
    "No Self-intersection",
    "No Holes",
    "Counterclockwise",
]


def config():
    """
    The selection which elements to validate and fix.
    """
    col1, col2 = st.beta_columns([6, 1])
    col2.write("")
    col2.write("")

    session = SessionState.get(run_id=0)
    if col2.button("Reset"):
        session.run_id += 1

    col1.multiselect(
        "", VALIDATION_OPTIONS, default=VALIDATION_OPTIONS, key=session.run_id
    )


def input():
    """
    The data input elements - text input, file upload and the examples.
    """
    col1_input, col2_input = st.beta_columns([2, 2])
    placeholder_file = col1_input.empty()
    placeholder_text = col2_input.empty()

    filename = placeholder_file.file_uploader(
        "Upload a file - GeoJSON/JSON, KML, WKT or zipped SHAPEFILE",
        type=FILETYPES,
        help="Zipped SHAPEFILE is a zipfile containing the shp,dbf,prj,shx files",
    )

    text_instruction = (
        "Or paste from clipboard - GeoJSON FeatureCollection, Feature, "
        "Geometry, Coordinates, bbox"
    )
    text_help = f"E.g. from https://geojson.io/"
    json_string = placeholder_text.text_area(text_instruction, help=text_help)

    # Examples that set text input widget default
    _, col1_example, col2_example, _ = st.beta_columns([1.4, 1, 1.1, 1.2])
    example_valid = col1_example.button("Valid Example")
    example_invalid = col2_example.button("Invalid Example")
    if example_valid:
        json_string = placeholder_text.text_area(
            text_instruction,
            value=geojson.load(open("app/test-data/fc_simple_valid.json")),
            help=text_help,
        )
    if example_invalid:
        json_string = placeholder_text.text_area(
            text_instruction,
            value=geojson.load(open("app/test-data/fc_holes_coordinates.json")),
            help=text_help,
        )

    if filename:
        df = utils.read_vector_file_to_df(filename)
    elif json_string != "":
        df = utils.read_json_string_to_df(json_string)
    else:
        df = None
    return df


def overview(df: GeoDataFrame):
    """
    Data overview visualization elements - properties and map
    """
    st.markdown("---")
    properties = [p for p in df.columns if p != "geometry"]
    geom_types = df.geometry.geom_type.value_counts().to_dict()
    st.markdown(
        f"** Features:** {df.shape[0]} ｜ **Geometry types**: {geom_types} ｜ **Properties**: {len(properties)}"
    )
    st.write("")
    fig = df.reset_index().plot_bokeh(show_figure=False, figsize=(665, 350))
    st.bokeh_chart(fig)
    with st.beta_expander(f"Show as full GeoJSON - Click to expand"):
        st.write(df.geometry.__geo_interface__)
    st.markdown("---")


def validation(aoi: Aoi):
    """
    Validation elements.
    """
    symbol = ["🟥", "✅"]
    st.write("")
    (
        # col1,
        # col2,
        # col3,
        col4,
        col5,
        col6,
    ) = st.beta_columns(3)
    # col1.markdown(f"{symbol[aoi.is_single_feature]} **Single feature**")
    # col2.markdown(f"{symbol[aoi.is_polygon]} **Is Polygon**")
    # col3.markdown(f"{symbol[aoi.is_4326]} **Is 4326**")
    col4.markdown(f"{symbol[aoi.is_no_selfintersection]} **No Self-intersection**")
    col5.markdown(f"{symbol[aoi.is_no_holes]} **No Holes**")
    col6.markdown(f"{symbol[aoi.is_ccw]} **Counterclockwise**")

    if aoi.all_valid:
        st.success("**VALID!**")
    elif not aoi.fixable_valid:
        st.warning("**INVALID - FIXING AUTOMATICALLY ...**")
    # else:
    #     if not aoi.is_single_feature:
    #         st.error("**INVALID - FIX MANUALLY!** Use only a single Feature.")
    #     if not aoi.is_polygon:
    #         geom_types = aoi.df.geometry.geom_type.value_counts().to_dict()
    #         st.error(
    #             f"**INVALID - FIX MANUALLY!** Use only a Polygon Geometry. Data is {geom_types}."
    #         )
    #     elif not aoi.is_single_ring and aoi.is_no_holes:
    #         st.error(f"**INVALID - FIX MANUALLY!** The Polygon has multiple rings.")
    elif not aoi.is_single_ring and aoi.is_no_holes:
        st.error(f"**INVALID - FIX MANUALLY!** The Polygon has multiple rings.")


def results(aoi: Aoi):
    """
    Controls the results elements.
    """
    st.write("")
    download_geojson = aoi.df.iloc[0].geometry.__geo_interface__
    col1_result, col2_result = st.beta_columns((1, 2))
    utils.download_button(
        json.dumps(download_geojson),
        "aoi.geojson",
        "Download as GeoJson",
        col1_result,
    )
    expander_result = col2_result.beta_expander("Copy full GeoJSON - Click to expand")
    expander_result.write(download_geojson)


def fix(aoi: Aoi) -> Aoi:
    """
    Controls the vector fix elements.
    """
    # if not aoi.is_4326:
    #     aoi.df = aoi.df.to_crs(epsg=4326)
    #     st.info("Adjusted to crs 4326...")
    if not aoi.is_no_selfintersection:
        aoi.df.geometry = aoi.df.geometry.apply(lambda x: x.buffer(0))
        st.info("Removing self-intersections by applying buffer(0)...")
    if not aoi.is_no_holes:
        aoi.df.geometry = aoi.df.geometry.apply(lambda x: utils.close_holes(x))
        st.info("Closing holes in geometry...")
    if not aoi.is_ccw:
        aoi.df.geometry = aoi.df.geometry.apply(
            lambda x: orient(x) if x.geom_type == "Polygon" else x
        )
        st.info("Applying right-hand rule winding ...")

    return aoi
