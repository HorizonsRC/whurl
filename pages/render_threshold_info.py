import streamlit as st
from st_pages import add_page_title

from hurl.measurement_list import get_measurement_list
from hurl.site_list import get_site_list
from hurl.status import get_status
from hurl.threshold_info import get_threshold_info_url

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
    if "measurement" not in st.session_state:
        st.session_state.measurement = None
    site_success, site_result, site_url = get_site_list(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        measurement=st.session_state.measurement,
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
    
    
def pull_measurement_list():
    if "site" not in st.session_state:
        st.session_state.site = None
    measurement_success, measurement_result, measurement_url = (
        get_measurement_list(
            base_url=f"{st.session_state.base_url}{st.session_state.hts}",
            site=st.session_state.site,
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

    
if not success:
    st.error("Server connection failed", icon="🚨")
    with st.expander("See details"):
        st.write(result)

        
update_site_list()
update_measurement_list()
        
try:
    if "measurement_default" not in st.session_state:
        st.session_state.measurement_default = None
    with col1:
        st.selectbox(
            "Site",
            st.session_state.site_list,
            index=None,
            key="site",
            disabled=(not success),
            on_change=update_measurement_list(),
        )
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
    st.text_area("Site List URL:", value=st.session_state.site_url)

final_url = st.text_area(
    "Hilltop URL",
    value=get_threshold_info_url(
        base_url=f"{st.session_state.base_url}{st.session_state.hts}",
        site=st.session_state.site,
        measurement=st.session_state.measurement,
    ),
    key="final_url",
)

st.link_button(
    "Go!",
    url=st.session_state.final_url,
    type="primary",
    disabled=(not success),
)
