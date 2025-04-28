from urllib.parse import quote, urlencode
from xml.etree import ElementTree

from hurl.utils import get_hilltop_response


def get_collection_list_url(
    base_url,
):
    params = {
        "Request": "CollectionList",
        "Service": "Hilltop",
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url

def get_collection_list(
    base_url, timeout=60
):
    url = get_collection_list_url(base_url)
    
    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    root = ElementTree.fromstring(ret_obj.decode())
    collection_list = []
    for child in root.findall("Collection"):
        collection_list += [child.get("Name")]
    return success, collection_list, url
