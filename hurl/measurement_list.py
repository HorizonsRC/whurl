from urllib.parse import urlencode, quote
from hurl.utils import get_hilltop_response
from xml.etree import ElementTree
import pandas as pd

def get_measurement_list_url(
    base_url,
    site=None,
    collection=None,
    units=None,
    target=None,
):
    params = {
        "Request": "MeasurementList",
        "Service": "Hilltop",
        "Site": site,
        "Collection": collection,
        "Units": units,
        "Target": target,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url


def get_measurement_list(
    base_url, site=None, collection=None, units=None, target=None, timeout=60
):
    if target is not None:
        raise ValueError("HtmlSelect (JSON) not supported.")
    
    url = get_measurement_list_url(base_url, site, collection, units)
    
    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    root = ElementTree.fromstring(ret_obj.decode())
    measurement_list = []
    for data_source in root.findall("DataSource"):
        for measurement in data_source.findall("Measurement"):
            payload = {"Site": data_source.get("Site")}
            payload["DataSource"] = data_source.get("Name")
            payload["TSType"] = data_source.find("TSType").text
            payload["DataType"] = data_source.find("DataType").text
            payload["From"] = data_source.find("From").text
            payload["To"] = data_source.find("To").text
            payload["Measurement"] = measurement.get("Name")
            print(payload["Measurement"])
            for child in measurement:
                payload[child.tag] = child.text
            measurement_list += [payload]

    # Convert the list of dictionaries to a dictionary of lists.

    payload_df = pd.DataFrame(measurement_list)
    
    return success, payload_df, url
