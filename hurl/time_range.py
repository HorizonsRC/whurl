from urllib.parse import urlencode


def get_time_range_url(
    base_url,
    site=None,
    measurement=None,
    format=None,
):
    params = {
        "Request": "TimeRange",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
        "Format": format,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
