from hurl import measurement_list


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
