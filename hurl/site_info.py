from urllib.parse import urlencode, quote
from hurl.utils import get_hilltop_response
from xml.etree import ElementTree


def get_site_info_url(
    base_url,
    site=None,
    field_list=None,
    collection=None,
):
    params = {
        "Request": "SiteInfo",
        "Service": "Hilltop",
        "Site": site,
        "FieldList": field_list,
        "Collection": collection,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url

def get_field_list(
    base_url, site=None, collection=None, timeout=60
):
    url = get_site_info_url(base_url, site, collection)
    
    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    root = ElementTree.fromstring(ret_obj.decode())
    field_list = []
    for child in root.findall("Site"):
        for field in child.iter():
            field_list += [field.tag]
    return success, field_list, url
    
