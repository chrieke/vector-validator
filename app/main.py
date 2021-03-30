import streamlit as st
from streamlit_lottie import st_lottie

import components
import utils
from vector import Vector

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")


col1_header, col2_header = st.beta_columns([1, 6])
lottie_url = "https://assets10.lottiefiles.com/temp/lf20_YQB3X3.json"
lottie_json = utils.load_lottieurl(lottie_url)
with col1_header:
    st_lottie(lottie_json, height=100, speed=1)

col2_header.write("")
col2_header.title(f"Vector Validator")
st.markdown("**Validates and automatically fixes your geospatial vector data.**")

valiation_selection = components.config()
st.write("")
st.write("")

df = components.input()

if df is None:
    st.stop()

components.overview(df)

aoi = Vector(df)
aoi.run_validity_checks(valiation_selection)
components.validation(aoi)

if not aoi.fixable_valid:
    aoi = components.fix(aoi)
    st.markdown("---")
    aoi.run_validity_checks()
    components.validation(aoi)

if aoi.all_valid:
    st.markdown("---")
    components.results(aoi)
