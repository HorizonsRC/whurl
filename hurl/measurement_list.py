from urllib.parse import urlencode


def get_measurement_list_url(
    base_url,
    service="Hilltop",
    site=None,
    collection=None,
    units=None,
    target=None,
):
    params = {
        "Request": "MeasurementList",
        "Service": service,
        "Site": site,
        "Collection": collection,
        "Units": units,
        "Target": target
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
