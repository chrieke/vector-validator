"""
Contains the visual elements of the app.
"""

from typing import List, Union
import json

import geojson
import streamlit as st
from shapely.geometry.polygon import orient
from geopandas import GeoDataFrame
import pandas_bokeh

pandas_bokeh.output_notebook()

import utils
from validation import Vector
import SessionState


FILETYPES = ["geojson", "json", "kml", "wkt", "zip"]
FILETYPES_SHAPEFILE = ["shp", "shx", "dbf", "prj"]
VALIDATION_CRITERIA = [
    "No Self-Intersection",
    "No Holes",
    "Counterclockwise",
]


def config() -> List[str]:
    """
    The selection which elements to validate and fix.
    """
    col1, col2 = st.beta_columns([6, 1])
    col2.write("")
    col2.write("")

    session = SessionState.get(run_id=0)
    if col2.button("Reset"):
        session.run_id += 1

    validation_criteria = col1.multiselect(
        "", VALIDATION_CRITERIA, default=VALIDATION_CRITERIA, key=session.run_id
    )
    if not validation_criteria:
        st.error("Please select at least one option to validate!")
        st.stop()
    return validation_criteria


def input() -> Union[GeoDataFrame, None]:
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


def overview(df: GeoDataFrame) -> None:
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
    st.write("")
    st.write("")


def validation(vector: Vector, validation_criteria: List[str]) -> None:
    """
    Validation elements.

    Args:
        vector: The evaluated vector validation object.
        selected_validations: The list of options to validate selected by the user.
    """
    symbol = ["🟥", "✅"]
    st.write("")
    (
        col1,
        col2,
        col3,
    ) = st.beta_columns(3)

    if "No Self-Intersection" in validation_criteria:
        col1.markdown(
            f"{symbol[vector.is_no_selfintersection]} **No Self-Intersection**"
        )
    if "No Holes" in validation_criteria:
        col2.markdown(f"{symbol[vector.is_no_holes]} **No Holes**")
    if "Counterclockwise" in validation_criteria:
        col3.markdown(f"{symbol[vector.is_ccw]} **Counterclockwise**")

    if vector.valid_by_citeria:
        st.success("**VALID!**")
    elif not vector.is_single_ring and vector.is_no_holes:
        st.error(f"**INVALID - FIX MANUALLY!** The Polygon has multiple rings.")
    else:
        st.warning("**INVALID - FIXING AUTOMATICALLY ...**")


def results(aoi: Vector) -> None:
    """
    Controls the results elements.
    """
    st.write("")
    download_geojson = aoi.df.iloc[0].geometry.__geo_interface__
    col1_result, col2_result = st.beta_columns((1, 2))
    utils.download_button(
        json.dumps(download_geojson),
        "aoi.geojson",
        "Download as GeoJSON",
        col1_result,
    )
    expander_result = col2_result.beta_expander("Copy full GeoJSON - Click to expand")
    expander_result.write(download_geojson)


def fix(vector: Vector, validation_criteria: List[str]) -> Vector:
    """
    Controls the vector fix elements.
    """
    if (
        "No Self-Intersection" in validation_criteria
        and not vector.is_no_selfintersection
    ):
        vector.df.geometry = vector.df.geometry.apply(lambda x: x.buffer(0))
        st.info("Removing Self-Intersections by applying buffer(0)...")
    if "No Holes" in validation_criteria and not vector.is_no_holes:
        vector.df.geometry = vector.df.geometry.apply(lambda x: utils.close_holes(x))
        st.info("Closing holes in geometry...")
    if "Counterclockwise" in validation_criteria and not vector.is_ccw:
        vector.df.geometry = vector.df.geometry.apply(
            lambda x: orient(x) if x.geom_type == "Polygon" else x
        )
        st.info("Applying right-hand/ccw rule winding ...")

    return vector
