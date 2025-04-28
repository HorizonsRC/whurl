from urllib.parse import quote, urlencode


def get_get_bore_url(
    base_url,
    site=None,
    bounding_box=None,
):
    params = {
        "Request": "GetBore",
        "Service": "Hilltop",
        "Site": site,
        "BBox": bounding_box,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
