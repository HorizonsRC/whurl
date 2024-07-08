from hurl import get_bore


def test_get_get_bore_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "bounding_box": "-40.50279,175.09327,-39.71855,175.95490,EPSG:4326",
    }

    url = get_bore.get_get_bore_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetBore&Service=Hilltop&Site=Manawatu+at+Teachers+College&BBox=-40.50279%2C175.09327%2C-39.71855%2C175.95490%2CEPSG%3A4326"""
    )
