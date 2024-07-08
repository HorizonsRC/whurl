from urllib.parse import urlencode

def get_sample_count_url(
    base_url,
    site=None,
    format=None,
):
    params = {
        "Request": "SampleCount",
        "Service": "Hilltop",
        "Site": site,
        "Format": format,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
