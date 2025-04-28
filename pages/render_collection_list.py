import streamlit as st
from st_pages import add_page_title

from hurl.collection_list import get_collection_list_url
from hurl.status import get_status

add_page_title()

col1, col2 = st.columns(2)

with col1:
    st.text_input(
        "Base URL", key="base_url", value="http://hilltopdev.horizons.govt.nz/"
    )
with col2:
    st.text_input("HTS file", key="hts", value="boo.hts")


success, result = get_status(
    base_url=f"{st.session_state.base_url}{st.session_state.hts}"
)

final_url = st.text_area(
    "Hilltop URL",
    value=get_collection_list_url(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
    ),
    key="final_url",
)

st.link_button(
    "Go!",
    url=st.session_state.final_url,
    type="primary",
    disabled=(not success),
)
