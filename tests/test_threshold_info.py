from hurl import threshold_info


def test_get_threshold_info_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure"
    }

    url = threshold_info.get_threshold_info_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=ThresholdInfo&Service=Hilltop&Site=Manawatu+at+Teachers+College&Measurement=Atmospheric+Pressure"""
    )
