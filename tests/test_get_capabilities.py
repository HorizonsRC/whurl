
from hurl import get_capabilities


def test_get_capabilities_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "service":"SOS"
    }

    url = get_capabilities.get_get_capabilities_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetCapabilities&Service=SOS"""
    )
