import streamlit as st
from st_pages import add_page_title
from hurl.measurement_list import get_measurement_list
from hurl.collection_list import get_collection_list
from hurl.site_list import get_site_list_url
from hurl.status import get_status
from hurl.components import bbox_form
from streamlit_tags import st_tags
import pandas as pd

add_page_title()

col1, col2 = st.columns(2)

with col1:
    
    st.text_input(
        "Base URL", key="base_url", value="http://hilltopdev.horizons.govt.nz/"
    )
with col2:
    st.text_input("HTS file", key="hts", value="boo.hts")


def pull_measurement_list():
    if "collection" not in st.session_state:
        st.session_state.collection = None
    measurement_success, measurement_result, measurement_url = (
        get_measurement_list(
            base_url=f"{st.session_state.base_url}{st.session_state.hts}",
            collection=st.session_state.collection,
            units=False,
        )
    )
    if measurement_success:
        measurement_list = measurement_result
    else:
        with st.expander("🚨 Measurement list retrieval failed!"):
            st.write(measurement_result)
        measurement_list = []
    return measurement_success, measurement_list, measurement_url


def update_measurement_list():
    (
        st.session_state.measurement_success,
        st.session_state.measurement_list,
        st.session_state.measurement_url,
    ) = pull_measurement_list()


def pull_collection_list():
    collection_success, collection_result, collection_url = (
        get_collection_list(
            base_url=f"{st.session_state.base_url}{st.session_state.hts}"
        )
    )
    if collection_success:
        collection_list = collection_result
    else:
        with st.expander("🚨 collection list retrieval failed!"):
            st.write(collection_result)
        collection_list = []
    return collection_success, collection_list, collection_url


if "collection_list" not in st.session_state:
    (
        st.session_state.collection_success,
        st.session_state.collection_list,
        st.session_state.collection_url,
    ) = pull_collection_list()
else:
    st.session_state.collection_success = st.session_state.collection_success
    st.session_state.collection_list = st.session_state.collection_list
    st.session_state.collection_url = st.session_state.collection_url

success, result = get_status(
    base_url=f"{st.session_state.base_url}{st.session_state.hts}"
)

if "measurement_list" not in st.session_state:
    (
        st.session_state.measurement_success,
        st.session_state.measurement_list,
        st.session_state.measurement_url,
    ) = pull_measurement_list()
else:
    st.session_state.measurement_success = st.session_state.measurement_success
    st.session_state.measurement_list = st.session_state.measurement_list
    st.session_state.measurement_url = st.session_state.measurement_url

if not success:
    st.error("Server connection failed", icon="🚨")
    with st.expander("See details"):
        st.write(result)

try:
    if "measurement_default" not in st.session_state:
        st.session_state.measurement_default = None
    with col1:
        st.selectbox(
            "Collection",
            st.session_state.collection_list,
            index=None,
            key="collection",
            disabled=(not success),
            on_change=update_measurement_list(),
        )
    # if st.button("Refresh"):
    #     st.session_state.measurement_default = None
    #     st.session_state.measurement_list = pull_measurement_list()
    with col2:
        st.selectbox(
            "Measurement",
            st.session_state.measurement_list,
            index=st.session_state.measurement_default,
            key="measurement",
            disabled=(not success),
        )
except Exception as e:
    st.error("Failed to get data to populate dropdowns")
    st.write(e)
    st.text_area(
        "Measurement List URL:", value=st.session_state.measurement_url
    )
    st.text_area("Collection List URL:", value=st.session_state.collection_url)

location = st.toggle("Location", key="location", value=False)

if location:
    location = "Yes"
else:
    location = None

bbox_added, bbox = bbox_form(success)
    
site_parameters = st_tags(
    label="Site Parameters",
    text="Press Enter to Add",
    suggestions=[
        "CatchmentArea",
        "Altitude",
        "CatchmentName",
        "Location",
    ],
    key="site_parameters",
)


if len(site_parameters) == 0:
    site_parameters = None
else:
    site_parameters = f"{','.join(site_parameters)}"

col1, col2 = st.columns(2)

with col1:
    target = st.selectbox(
        "Target",
        [None, "HtmlSelect"],
        key="target",
        disabled=(not success),
    )

with col2:
    syn_levels = st.selectbox(
        "Synonym Levels",
        [None, "1", "2"],
        disabled=(not success),
        key="syn_levels",
    )

fill_cols = st.toggle("Fill Columns", key="fill_cols", value=False)

if not fill_cols:
    fill_cols = None

final_url = st.text_area(
    "Hilltop URL",
    value=get_site_list_url(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        location=location,
        bounding_box=bbox,
        measurement=st.session_state.measurement,
        collection=st.session_state.collection,
        site_parameters=site_parameters,
        target=st.session_state.target,
        syn_level=st.session_state.syn_levels,
        fill_cols=fill_cols,
    ),
    key="final_url",
)

st.link_button(
    "Go!",
    url=st.session_state.final_url,
    type="primary",
    disabled=(not success),
)
