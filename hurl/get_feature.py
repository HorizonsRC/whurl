from urllib.parse import urlencode


def get_get_feature_url(
    base_url,
    type_name,
    bounding_box,
):
    params = {
        "Request": "GetFeature",
        "Service": "WFS",
        "TypeName": type_name,
        "BBox": bounding_box,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
