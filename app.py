"""
Main landing page of the app.
"""

from st_pages import Page, Section, show_pages, add_page_title

add_page_title()

show_pages(
    [
        Page("app.py", "HURL", "🤮"),
        Section("Hilltop Calls"),
        Page("pages/render_site_list.py", "Site List"),
        Page("pages/render_measurement_list.py", "Measurement List"),
        Page("pages/render_collection_list.py", "Collection List"),
        Page("pages/render_site_info.py", "Site Info"),
    ]
)

