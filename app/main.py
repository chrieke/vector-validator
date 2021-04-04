import streamlit as st
from streamlit_lottie import st_lottie

import components
import utils
from validation import Vector

st.set_page_config(page_title="Vector Validator", layout="centered", page_icon="🔻", initial_sidebar_state="collapsed")

col1_header, col2_header = st.beta_columns([1, 6])
lottie_url = "https://assets10.lottiefiles.com/temp/lf20_YQB3X3.json"
lottie_json = utils.load_lottieurl(lottie_url)
with col1_header:
    st_lottie(lottie_json, height=100, speed=1)

col2_header.write("")
col2_header.title(f"Vector Validator")
st.markdown("[![Star](https://img.shields.io/github/stars/chrieke/vector-validator.svg?logo=github&style=social)](https://gitHub.com/chrieke/vector-validator)"
            "&nbsp&nbsp&nbsp[![Follow](https://img.shields.io/twitter/follow/chrieke?style=social)](https://www.twitter.com/chrieke)")
st.write("")
st.markdown("**Validates and automatically fixes your geospatial vector data.** <br> Select the validation options, "
            "upload/paste your vector data or try one of the examples.", unsafe_allow_html=True
)

validation_criteria = components.config()
st.write("")
st.write("")

df = components.input()

if df is None:
    st.stop()

components.exploration(df)

vector = Vector(df)
vector.run_validation_checks(validation_criteria)
components.validation(vector, validation_criteria)

if not vector.valid_by_citeria:
    vector = components.fix(vector, validation_criteria)
    st.markdown("---")
    vector.run_validation_checks(validation_criteria)
    components.validation(vector, validation_criteria)

if vector.valid_by_citeria:
    st.markdown("---")
    components.results(vector)
