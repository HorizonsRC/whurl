from urllib.parse import urlencode, quote


def get_threshold_info_url(
    base_url,
    site=None,
    measurement=None,
):
    params = {
        "Request": "ThresholdInfo",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
