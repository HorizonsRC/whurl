from urllib.parse import quote, urlencode


def get_get_sample_url(
    base_url,
    site=None,
    format=None,
):
    params = {
        "Request": "GetSample",
        "Service": "Hilltop",
        "Site": site,
        "Format": format,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
