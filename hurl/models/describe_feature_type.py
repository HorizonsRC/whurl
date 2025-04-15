from urllib.parse import urlencode


def get_describe_feature_type_url(
    base_url,
):
    params = {
        "Request": "DescribeFeatureType",
        "Service": "WFS",
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
