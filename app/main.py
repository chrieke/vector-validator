import streamlit as st
from streamlit_lottie import st_lottie

import components
import utils
from validation import Vector

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")


col1_header, col2_header = st.beta_columns([1, 6])
lottie_url = "https://assets10.lottiefiles.com/temp/lf20_YQB3X3.json"
lottie_json = utils.load_lottieurl(lottie_url)
with col1_header:
    st_lottie(lottie_json, height=100, speed=1)

col2_header.write("")
col2_header.title(f"Vector Validator")
st.markdown("**Validates and automatically fixes your geospatial vector data.**")

selected_validations = components.config()
st.write("")
st.write("")

df = components.input()

if df is None:
    st.stop()

components.overview(df)

vector = Vector(df)
vector.run_validation_checks(selected_validations)
components.validation(vector)

if not vector.valid_by_citeria:
    vector = components.fix(vector)
    st.markdown("---")
    vector.run_validation_checks()
    components.validation(vector)

if vector.valid_all:
    st.markdown("---")
    components.results(vector)
