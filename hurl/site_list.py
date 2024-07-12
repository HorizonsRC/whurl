from urllib.parse import urlencode
from hurl.utils import get_hilltop_response
from xml.etree import ElementTree


def get_site_list_url(
    base_url,
    location=None,
    bounding_box=None,
    measurement=None,
    collection=None,
    site_parameters=None,
    target=None,
    syn_level=None,
    fill_cols=None,
):
    params = {
        "Request": "SiteList",
        "Service": "Hilltop",
        "Location": location,
        "BBox": bounding_box,
        "Measurement": measurement,
        "Collection": collection,
        "SiteParameters": site_parameters,
        "Target": target,
        "SynLevel": syn_level,
        "FillCols": fill_cols,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url


def get_site_list(
    base_url,
    location=None,
    bounding_box=None,
    measurement=None,
    collection=None,
    site_parameters=None,
    target=None,
    syn_level=None,
    fill_cols=None,
    timeout=60,
):
    url = get_site_list_url(
        base_url,
        location,
        bounding_box,
        measurement,
        collection,
        site_parameters,
        target,
        syn_level,
        fill_cols,
    )
    print(url)

    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    root = ElementTree.fromstring(ret_obj.decode())
    site_list = []
    for child in root.findall("Site"):
        site_list += [child.get("Name")]

    return success, site_list, url
