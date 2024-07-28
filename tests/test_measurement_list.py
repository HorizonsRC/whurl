from hurl import measurement_list
import pytest


def test_get_measurement_list_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "collection": "AtmosphericPressure",
        "units": "Yes",
        "target": "HtmlSelect",
    }

    url = measurement_list.get_measurement_list_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=MeasurementList&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Collection=AtmosphericPressure&Units=Yes&Target=HtmlSelect"""
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_get_measurement_list_all_params():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "collection": "AtmosphericPressure",
        "units": "Yes",
        "timeout": 5,
    }
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    success, measurement_list_ret, url = measurement_list.get_measurement_list(
        base_url, **params
    )

    assert success
    assert (
        url
        == "http://hilltopdev.horizons.govt.nz/boo.hts?Request=MeasurementList&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Collection=AtmosphericPressure&Units=Yes"
    )

    assert measurement_list_ret == ['Atmospheric Pressure [Atmospheric Pressure]']
