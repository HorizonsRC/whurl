from hurl import sample_count


def test_get_sample_count_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "format": "JSON",
    }

    url = sample_count.get_sample_count_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=SampleCount&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Format=JSON"""
    )
