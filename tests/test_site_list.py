from hurl import site_list


def test_get_site_list_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "location": "Manawatu at Teachers College",
        "bounding_box": "-40.50279,175.09327,-39.71855,175.95490,EPSG:4326",
        "measurement": "Atmospheric Pressure",
        "collection": "AtmosphericPressure",
        "site_parameters": "CatchmentName",
        "target": "HtmlSelect",
        "syn_level": "1",
        "fill_cols": "Yes"
    }

    url = site_list.get_site_list_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteList&Service=Hilltop&Location=Manawatu+at+Teachers+College&BBox=-40.50279%2C175.09327%2C-39.71855%2C175.95490%2CEPSG%3A4326&Measurement=Atmospheric+Pressure&Collection=AtmosphericPressure&SiteParameters=CatchmentName&Target=HtmlSelect&SynLevel=1&FillCols=Yes"""
    )
