import pandas as pd
import streamlit as st


def proj_lookup(epsg_code):
    desc = {
        None: None,
        "EPSG:4326": "WGS84 lat and long",
        "EPSG:2193": "NZTM 2000",
        "EPSG:27200": "NZMG",
        "EPSG:4167": "NZGD 200",
    }

    return desc[epsg_code]


def bbox_form(render):
    with st.form("bbox_form"):
        col1, col2 = st.columns(2)
        bbox_x1 = col1.number_input("x1", value=175.86)
        bbox_y1 = col1.number_input("y1", value=-39.89)
        bbox_x2 = col2.number_input("x2", value=175.23)
        bbox_y2 = col2.number_input("y2", value=-40.43)

        proj = st.selectbox(
            "Projection",
            [
                "EPSG:4326",
                "EPSG:2193",
                "EPSG:27200",
                "EPSG:4167",
            ],
            index=None,
            format_func=proj_lookup,
            disabled=(not render),
            key="proj",
        )
        if (
            (bbox_x1 is not None)
            and (bbox_y1 is not None)
            and (bbox_x2 is not None)
            and (bbox_y2 is not None)
            and (proj is not None)
        ):
            bbox = f"{bbox_y1},{bbox_x1},{bbox_y2},{bbox_x2},{proj}"
        else:
            bbox = None
        st.code(bbox)
        d = {"lon": [bbox_x1, bbox_x2], "lat": [bbox_y1, bbox_y2]}

        df = pd.DataFrame(data=d)
        bbox_added = st.form_submit_button("Update")
        with st.expander("See Map"):
            st.warning("If the map markers don't appear, try expanding the map to full screen (icon top right). This is a known upstream bug.", icon="⚠️")
            st.map(df, use_container_width=True)
    return bbox_added, bbox


