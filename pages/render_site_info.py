import streamlit as st
from st_pages import add_page_title
from streamlit_tags import st_tags

from hurl.collection_list import get_collection_list
from hurl.site_info import get_field_list, get_site_info_url
from hurl.site_list import get_site_list
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


def pull_site_list():
    if "collection" not in st.session_state:
        st.session_state.collection = None
    site_success, site_result, site_url = get_site_list(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        collection=st.session_state.collection,
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


def pull_field_list():
    if "site" not in st.session_state:
        st.session_state.site = None
    if "collection" not in st.session_state:
        st.session_state.collection = None
    field_success, field_result, field_url = get_field_list(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        site=st.session_state.site,
        collection=st.session_state.collection,
    )
    if field_success:
        field_list = field_result
    else:
        field_list = ["You must provide a site name"]
    return field_success, field_list, field_url


def update_field_list():
    (
        st.session_state.field_success,
        st.session_state.field_list,
        st.session_state.field_url,
    ) = pull_field_list()


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

if "field_list" not in st.session_state:
    (
        st.session_state.field_success,
        st.session_state.field_list,
        st.session_state.field_url,
    ) = pull_field_list()
else:
    st.session_state.field_success = st.session_state.field_success
    st.session_state.field_list = st.session_state.field_list
    st.session_state.field_url = st.session_state.field_url

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
            on_change=update_field_list(),
        )
    if st.session_state.field_success:
        field_text = "Press Enter to Add"
    else:
        field_text = "Failed to retrieve site parameters."
    site_parameters = st_tags(
        label="Site Parameters",
        text=field_text,
        suggestions=st.session_state.field_list,
        key="site_parameters",
    )
except Exception as e:
    st.error("Failed to get data to populate dropdowns")
    st.write(e)
    st.text_area("Site List URL:", value=st.session_state.site_url)
    st.text_area("Collection List URL:", value=st.session_state.collection_url)

if (
    st.session_state.site_parameters is not None
    and len(st.session_state.site_parameters) == 0
):
    field_selections = None
else:
    field_selections = f"{','.join(st.session_state.site_parameters)}"

final_url = st.text_area(
    "Hilltop URL",
    value=get_site_info_url(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        site=st.session_state.site,
        field_list=field_selections,
        collection=st.session_state.collection,
    ),
    key="final_url",
)

st.link_button(
    "Go!",
    url=st.session_state.final_url,
    type="primary",
    disabled=(not success),
)
