
from urllib.parse import urlencode


def get_get_capabilities_url(
    base_url,
    service="WFS",
):
    params = {
        "Request": "GetCapabilities",
        "Service": service,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
