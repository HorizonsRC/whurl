"""
Main landing page of the app.
"""

import streamlit as st
from st_pages import Page, Section, show_pages, add_page_title
from hilltoppy.utils import build_url

add_page_title()

show_pages(
    [
        Page("app.py", "HURL", "🤮"),
        Section("Hilltop Calls"),
        Page("pages/render_site_list.py", "Site List"),
        Page("pages/render_measurement_list.py", "Measurement List"),
    ]
)

