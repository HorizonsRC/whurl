from urllib.parse import quote, urlencode


def get_get_comments_url(
    base_url,
    site=None,
    measurement=None,
    from_datetime=None,
    to_datetime=None,
):
    params = {
        "Request": "GetComments",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
        "From": from_datetime,
        "To": to_datetime,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
