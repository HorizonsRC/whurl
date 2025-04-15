from hurl import get_comments


def test_get_get_comments_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure",
        "from_datetime": "2021-01-01T00:00:00",
        "to_datetime": "2021-01-02T00:00:00",
    }

    url = get_comments.get_get_comments_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetComments&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Measurement=Atmospheric%20Pressure&From=2021-01-01T00%3A00%3A00&To=2021-01-02T00%3A00%3A00"""
    )
