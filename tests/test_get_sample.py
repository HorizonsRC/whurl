from hurl import get_sample


def test_get_get_sample_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "format": "JSON",
    }

    url = get_sample.get_get_sample_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetSample&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Format=JSON"""
    )
