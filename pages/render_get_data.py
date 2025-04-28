import datetime

import streamlit as st
from st_pages import add_page_title

from hurl.collection_list import get_collection_list
from hurl.measurement_list import (get_measurement_list,
                                   get_measurement_list_url)
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
    
### Collection
# Drop down

### Site
# Deps:
# - Measurement
# - Collection
# Drop down

### Measurement
# Deps:
# - Collection
# - Site
# Drop down

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

# Selection between:
# time and date range:
# ISO8601

### From Datetime
# Time Range
# Deps: 
# - Site
# - Measurement
# datetime picker
if "min_date" not in st.session_state:
    st.session_state.min_date = None
if "max_date" not in st.session_state:
    st.session_state.max_date = datetime.datetime.now()
    
from_datetime = st.date_input(
    "From date",
    None,
    st.session_state.min_date,
    st.session_state.max_date,
    format="YYYY-MM-DD",
)

### To Datetime
# Time Range
# Deps: 
# - Site
# - Measurement
# datetime picker
to_datetime = st.date_input(
    "To date",
    None,
    st.session_state.min_date,
    st.session_state.max_date,
    format="YYYY-MM-DD",
)

### Time Interval
# Just a string for now (eventually ISO8601 time interval picker)


### Alignment
# Just a string for now

### Method
# Aggregation method.
# Drop down with options:
# - Interpolate
# - Average
# - Total
# - Moving Average
# - EP
# - Extrema

### Interval
# Just a string for now
# Deps:
# - Method
# Required if methd set to Average, Total, Moving Average or Extrema

### Gap Tolerance
# Just a string for now

### Show final
# Bool.
# if the final interval is incomplete, should we return the value of the incomplete interval?

### Date Only
# No time included

### Send As
# Text field

### Agency
# Leave a text field here.

### Format
# drop down
# - Native
# - WML2
# - JSON

### TS Type
# Drop Down:
# - StdQualSeries
# ???

### Show quality
# Bool


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
