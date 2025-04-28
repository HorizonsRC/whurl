from urllib.parse import quote, urlencode


def get_data_table_url(
    base_url,
    site=None,
    measurement=None,
    from_datetime=None,
    to_datetime=None,
    time_interval=None,
    collection=None,
    method=None,
    interval=None,
    location=None,
):
    params = {
        "Request": "DataTable",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
        "From": from_datetime,
        "To": to_datetime,
        "TimeInterval": time_interval,
        "Collection": collection,
        "Method": method,
        "Interval": interval,
        "Location": location,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
