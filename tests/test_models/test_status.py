from hurl import status
import pytest


def test_status_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {}

    url = status.get_status_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=Status&Service=Hilltop"""
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_status():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"

    success, ret_obj = status.get_status(base_url)

    assert success
    print(ret_obj)
    
