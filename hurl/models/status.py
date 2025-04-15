from urllib.parse import urlencode, quote
from hurl.utils import get_hilltop_response


def get_status_url(
    base_url,
):
    params = {
        "Request": "Status",
        "Service": "Hilltop",
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url

def get_status(
    base_url,
    timeout=60
):
    url = get_status_url(base_url)
    
    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    return success, ret_obj
