from hurl import data_table


def test_data_table_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure",
        "from_datetime":"1/1/2021",
        "to_datetime":"2/1/2021",
        "time_interval":"2021-01-01T12:00:00/2021-01-02T12:00:00",
        "collection":"AtmosphericPressure",
        "method":"Interpolate",
        "interval":"1day",
        "location":"Yes",
    }

    url = data_table.get_data_table_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=DataTable&Service=Hilltop&Site=Manawatu+at+Teachers+College&Measurement=Atmospheric+Pressure&From=1%2F1%2F2021&To=2%2F1%2F2021&TimeInterval=2021-01-01T12%3A00%3A00%2F2021-01-02T12%3A00%3A00&Collection=AtmosphericPressure&Method=Interpolate&Interval=1day&Location=Yes"""
    )
