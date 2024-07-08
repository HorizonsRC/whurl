from urllib.parse import urlencode

def get_recent_data_table_url(
    base_url,
    collection=None,
    scoll=None,
    mcoll=None,
    
):
    params = {
        "Request": "RecentDataTable",
        "Service": "Hilltop",
        "Collection": collection,
        "SColl": scoll,
        "MColl": mcoll,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params)}"
    return url
