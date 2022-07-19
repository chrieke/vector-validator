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


FILETYPES = ["geojson", "json", "kml", "wkt", "zip"]
FILETYPES_SHAPEFILE = ["shp", "shx", "dbf", "prj"]
VALIDATION_CRITERIA = [
    "No Self-Intersection",
    "No Holes",
    "Counterclockwise",
]
ADDITIONAL_VALIDATION_CRITERIA = ["No Duplicated Vertices"]


def config() -> List[str]:
    """
    The selection which elements to validate and fix.
    """
    col1, col2 = st.columns([6, 1])

    col2.write("")
    col2.write("")
    if 'run_id' not in st.session_state:
        st.session_state['run_id'] = 0
    if col2.button("Reset"):
        st.session_state.run_id += 1

    validation_criteria = col1.multiselect(
        "",
        VALIDATION_CRITERIA + ADDITIONAL_VALIDATION_CRITERIA,
        default=VALIDATION_CRITERIA,
        key=st.session_state.run_id,
    )
    if not validation_criteria:
        st.error("Please select at least one option to validate!")
        st.stop()
    return validation_criteria


def input() -> Union[GeoDataFrame, None]:
    """
    The data input elements - text input, file upload and the examples.
    """
    col1_input, col2_input = st.columns([2, 2])
    placeholder_file = col1_input.empty()
    placeholder_text = col2_input.empty()

    filename = placeholder_file.file_uploader(
        "Upload a vector file - GeoJSON/JSON, KML, WKT or zipped SHAPEFILE",
        type=FILETYPES,
        help="Zipped SHAPEFILE is a zipfile containing the shp,dbf,prj,shx files",
    )

    text_instruction = (
        "Or paste from clipboard - GeoJSON FeatureCollection, Feature, "
        "Geometry, Coordinates, bbox"
    )
    text_help = f"E.g. from https://geojson.io/"
    json_string = placeholder_text.text_area(
        text_instruction, height=102, help=text_help
    )

    # Examples that set text input widget default
    _, col1_example, col2_example, _ = st.columns([1.12, 1.0, 1.1, 1.0])
    example_valid = col1_example.button("Try valid example")
    example_invalid = col2_example.button("Try invalid example")
    if example_valid:
        json_string = placeholder_text.text_area(
            text_instruction,
            height=102,
            value=geojson.load(open("app/test-data/fc_simple_valid.json")),
            help=text_help,
        )
    if example_invalid:
        json_string = placeholder_text.text_area(
            text_instruction,
            height=102,
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


def exploration(df: GeoDataFrame) -> None:
    """
    Data overview visualization elements - properties and map
    """
    st.markdown("---")
    properties = [p for p in df.columns if p != "geometry"]
    geom_types = df.geometry.geom_type.value_counts().to_dict()

    col1, _, col2 = st.columns([2.2, 0.15, 3])
    col1.markdown(f"** Features:** {df.shape[0]}")
    col1.markdown(f"**Geometries**: {geom_types}")
    col1.markdown(
        f"**Properties**: {len(properties)} - {properties if len(properties) < 10 else f'{properties[:10]}, ...'}"
    )
    col1.write("")
    col1.write("")
    with col1.expander("Click to expand - see full GeoJSON"):
        st.write(df.__geo_interface__)
    col1.write("")

    fig = df.reset_index().plot_bokeh(
        show_figure=False,
        figsize=(400, 250),
    )
    fig.xaxis.axis_label = ""
    fig.yaxis.axis_label = ""
    col2.bokeh_chart(fig)

    st.write("---")


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
        col4,
    ) = st.columns(4)

    if "No Self-Intersection" in validation_criteria:
        col1.markdown(
            f"{symbol[vector.is_no_selfintersection]} **No Self-Intersection**"
        )
    if "No Holes" in validation_criteria:
        col2.markdown(f"{symbol[vector.is_no_holes]} **No Holes**")
    if "Counterclockwise" in validation_criteria:
        col3.markdown(f"{symbol[vector.is_ccw]} **Counterclockwise**")
    if "No Duplicated Vertices" in validation_criteria:
        col4.markdown(
            f"{symbol[vector.is_no_duplicated_vertices]} **No Duplicated Vertices**"
        )
    if vector.valid_by_citeria:
        st.success("**VALID! Download or copy below.**")
    elif not vector.is_single_ring and vector.is_no_holes:
        st.error(f"**INVALID - FIX MANUALLY!** The Polygon has multiple rings.")
    else:
        st.error("**INVALID - FIXING AUTOMATICALLY ...**")


def results(aoi: Vector) -> None:
    """
    Controls the results elements.
    """
    st.write("")
    _, col1, col2, _ = st.columns((0.1, 1, 2, 0.1))
    download_geojson = aoi.df.__geo_interface__
    utils.download_button(
        json.dumps(download_geojson),
        "aoi.geojson",
        "Download as GeoJSON",
        col1,
    )
    expander_result = col2.expander("Click to expand - see full GeoJSON")
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
        st.info("Applying right-hand/ccw winding ...")
    if (
        "No Duplicated Vertices" in validation_criteria
        and not vector.is_no_duplicated_vertices
    ):
        vector.df.geometry = vector.df.geometry.simplify(0)
        st.info("Removing duplicated vertices ...")

    return vector
