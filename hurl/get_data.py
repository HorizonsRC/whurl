from urllib.parse import urlencode

def get_get_data_url(
    base_url,
    site=None,
    measurement=None,
    from_datetime=None,
    to_datetime=None,
    time_interval=None,
    alignment=None,
    collection=None,
    method=None,
    interval=None,
    gap_tolerance=None,
    show_final=None,
    date_only=None,
    send_as=None,
    agency=None,
    format=None,
    ts_type=None,
    show_quality=None,
):
    params = {
        "Request": "GetData",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
        "From": from_datetime,
        "To": to_datetime,
        "TimeInterval": time_interval,
        "Alignment": alignment,
        "Collection": collection,
        "Method": method,
        "Interval": interval,
        "GapTolerance": gap_tolerance,
        "ShowFinal": show_final,
        "DateOnly": date_only,
        "SendAs": send_as,
        "Agency": agency,
        "Format": format,
        "tsType": ts_type,
        "ShowQuality": show_quality,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
