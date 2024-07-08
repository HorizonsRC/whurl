from urllib.parse import urlencode


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

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
