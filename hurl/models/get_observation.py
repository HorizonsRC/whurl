from urllib.parse import quote, urlencode


def get_get_observation_url(
    base_url,
    site_name=None,
    measurement=None,
    time_range=None,
):
    params = {
        "Request": "GetObservation",
        "Service": "SOS",
        "FeatureOfInterest": site_name,
        "ObservedProperty": measurement,
        "TemporalFilter": time_range,
    }

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
