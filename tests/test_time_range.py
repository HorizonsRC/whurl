from hurl import time_range


def test_get_time_range_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure",
        "format": "JSON",
    }

    url = time_range.get_time_range_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=TimeRange&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Measurement=Atmospheric%20Pressure&Format=JSON"""
    )
