from hurl import site_list
import pytest


def test_get_site_list_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "location": "True",
        "bounding_box": "-40.50279,175.09327,-39.71855,175.95490,EPSG:4326",
        "measurement": "Atmospheric Pressure",
        "collection": "AtmosphericPressure",
        "site_parameters": "CatchmentName",
        "target": "HtmlSelect",
        "syn_level": "1",
        "fill_cols": "Yes",
    }

    url = site_list.get_site_list_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteList&Service=Hilltop&Location=True&BBox=-40.50279%2C175.09327%2C-39.71855%2C175.95490%2CEPSG%3A4326&Measurement=Atmospheric%20Pressure&Collection=AtmosphericPressure&SiteParameters=CatchmentName&Target=HtmlSelect&SynLevel=1&FillCols=Yes"""
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_get_site_list_all_params():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "location": "True",
        "bounding_box": "-39.89,175.86,-40.43,175.23,EPSG:4326",
        "measurement": "Atmospheric Pressure [Atmospheric Pressure]",
        "collection": "AtmosphericPressure",
        "site_parameters": "CatchmentName",
        "syn_level": "1",
        "fill_cols": "True",
        "timeout": 5,
    }

    success, site_list_ret, url = site_list.get_site_list(base_url, **params)

    assert success
    assert site_list_ret == [
        "Manawatu at Teachers College",
        "Manawatu at Victoria Ave",
        "Ngahere Park Climate Station",
        "Rangitikei at Onepuhi",
    ]
    assert (
        url
        == "http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteList&Service=Hilltop&Location=True&BBox=-39.89%2C175.86%2C-40.43%2C175.23%2CEPSG%3A4326&Measurement=Atmospheric%20Pressure%20%5BAtmospheric%20Pressure%5D&Collection=AtmosphericPressure&SiteParameters=CatchmentName&SynLevel=1&FillCols=True"
    )
