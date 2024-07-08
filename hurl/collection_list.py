from urllib.parse import urlencode


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

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
