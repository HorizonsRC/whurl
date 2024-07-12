import streamlit as st
from st_pages import add_page_title
from hurl.measurement_list import get_measurement_list, get_measurement_list_url
from hurl.collection_list import get_collection_list
from hurl.site_list import get_site_list_url, get_site_list
from hurl.status import get_status
from hurl.components import bbox_form
from streamlit_tags import st_tags

add_page_title()

col1, col2 = st.columns(2)

with col1:
    
    st.text_input(
        "Base URL", key="base_url", value="http://hilltopdev.horizons.govt.nz/"
    )
with col2:
    st.text_input("HTS file", key="hts", value="boo.hts")


def pull_site_list():
    if "collection" not in st.session_state:
        st.session_state.collection = None
    site_success, site_result, site_url = (
        get_site_list(
            base_url=f"{st.session_state.base_url}{st.session_state.hts}",
            collection=st.session_state.collection,
        )
    )
    if site_success:
        site_list = site_result
    else:
        with st.expander("🚨 Site list retrieval failed!"):
            st.write(site_result)
        site_list = []
    return site_success, site_list, site_url


def update_site_list():
    (
        st.session_state.site_success,
        st.session_state.site_list,
        st.session_state.site_url,
    ) = pull_site_list()


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

if "site_list" not in st.session_state:
    (
        st.session_state.site_success,
        st.session_state.site_list,
        st.session_state.site_url,
    ) = pull_site_list()
else:
    st.session_state.site_success = st.session_state.site_success
    st.session_state.site_list = st.session_state.site_list
    st.session_state.site_url = st.session_state.site_url

if not success:
    st.error("Server connection failed", icon="🚨")
    with st.expander("See details"):
        st.write(result)

try:
    if "site_default" not in st.session_state:
        st.session_state.site_default = None
    with col1:
        st.selectbox(
            "Collection",
            st.session_state.collection_list,
            index=None,
            key="collection",
            disabled=(not success),
            on_change=update_site_list(),
        )
    with col2:
        st.selectbox(
            "Site",
            st.session_state.site_list,
            index=st.session_state.site_default,
            key="site",
            disabled=(not success),
        )
except Exception as e:
    st.error("Failed to get data to populate dropdowns")
    st.write(e)
    st.text_area(
        "Site List URL:", value=st.session_state.site_url
    )
    st.text_area("Collection List URL:", value=st.session_state.collection_url)

col1, col2 = st.columns(2)

with col1:
    units = st.toggle("Units", key="units", value=False, disabled=(not success))
    if units:
        units = "Yes"
    else:
        units = None

with col2:
    target = st.selectbox(
        "Target",
        [None, "HtmlSelect"],
        key="target",
        disabled=(not success),
    )

final_url = st.text_area(
    "Hilltop URL",
    value=get_measurement_list_url(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        site=st.session_state.site,
        collection=st.session_state.collection,
        units=units,
        target=st.session_state.target,
    ),
    key="final_url",
)

st.link_button(
    "Go!",
    url=st.session_state.final_url,
    type="primary",
    disabled=(not success),
)
