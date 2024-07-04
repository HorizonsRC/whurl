from urllib.parse import urlencode


def get_site_list_url(
    base_url,
    service="Hilltop",
    location=None,
    bounding_box=None,
    measurement=None,
    collection=None,
    site_parameters=None,
    target=None,
    syn_level=None,
):
    params = {
        "Request": "SiteList",
        "Service": service,
        "Location": location,
        "BBox": bounding_box,
        "Measurement": measurement,
        "Collection": collection,
        "SiteParameters": site_parameters,
        "Target": target,
        "SynLevel": syn_level,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
