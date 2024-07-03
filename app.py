"""
# My first app
Here's out first attempt at using data to create a table.
"""

import streamlit as st
from hilltoppy.utils import build_url

st.header("HURL")
st.subheader("Hilltop URL Generator")

col1, col2 = st.columns(2)
col1.text_input("Base URL", key="base_url", value="http://hilltopdev.horizons.govt.nz/")
col2.text_input("HTS file", key="hts", value="boo.hts")

st.empty()
col1, col2 = st.columns(2)
col1.selectbox("Request", 
             ["SiteList", "MeasurementList", "CollectionList", "GetData", "SiteInfo"],
             key="request")
col2.text_input("Site", key="site", value="Manawatu at Teachers College")
col1.text_input("Measurement", key="measurement", value="Water level statistics: Point Sample")
col2.text_input("Collection", key="collection", value=None)

st.empty()
col1, col2 = st.columns(2)
col1.date_input("From date", key="from_date", value=None, disabled=(st.session_state.request!="GetData"))
col2.time_input("From time", key="from_time", value=None, disabled=(st.session_state.request!="GetData"))
col1.date_input("To date", key="to_date", value=None, disabled=(st.session_state.request!="GetData"))
col2.time_input("To time", key="to_time", value=None, disabled=(st.session_state.request!="GetData"))

st.empty()
col1, col2 = st.columns(2)
col1.selectbox("Location",
             [False, True, "LatLong"],
             key="location", disabled=(st.session_state.request!="SiteList"))
col2.text_input("Site Parameters", key="site_parameters", disabled=(st.session_state.request!="SiteList"))
col1.selectbox("Aggregation Method",
             [None, "Average", "Total", "Moving Average", "Extrema"],
             key="agg_method", disabled=(st.session_state.request!="GetData"))
col2.selectbox("Aggregation Interval",
             [None, "1 day", "1 week", "1 month"],
             key="agg_interval", disabled=(st.session_state.request!="GetData"))
st.empty()
col1, col2 = st.columns(2)
col1.selectbox("Timeseries Type",
             ["Standard", "Check", "Quality"],
             key="tstype", disabled=(st.session_state.request!="GetData"))
col2.toggle("Quality Codes", key="quality_codes", value=False, disabled=(st.session_state.request!="GetData"))
st.empty()
col1, col2 = st.columns(2)
col1.text_input("Alignment", key="alignment", value=None, disabled=(st.session_state.request!="GetData"))
col2.selectbox("Response Format",
             [None, "Native", "WML2"],
             key="response_format", disabled=(st.session_state.request!="GetData"))
if st.session_state.from_date is not None and st.session_state.from_date is not None:
    from_datetime = f"{str(st.session_state.from_date)} {str(st.session_state.from_time)}"
else:
    from_datetime = None
    
if st.session_state.to_date is not None and st.session_state.to_date is not None:
    to_datetime = f"{str(st.session_state.to_date)} {str(st.session_state.to_time)}"
else:
    to_datetime = None

response = build_url(
    base_url=st.session_state.base_url,
    hts=st.session_state.hts,
    request=st.session_state.request,
    site=st.session_state.site,
    measurement=st.session_state.measurement,
    collection=st.session_state.collection,
    from_date=from_datetime,
    to_date=to_datetime,
    location=st.session_state.location,
    site_parameters=st.session_state.site_parameters,
    agg_method=st.session_state.agg_method,
    agg_interval=st.session_state.agg_interval,
    alignment=st.session_state.alignment,
    quality_codes=st.session_state.quality_codes,
    tstype=st.session_state.tstype,
    response_format=st.session_state.response_format,
)

hilltop_url = st.text_area("Hilltop URL", value=response)

st.link_button("Go!", hilltop_url)
