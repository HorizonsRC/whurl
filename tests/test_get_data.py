from hurl import get_data


def test_get_data_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure",
        "from_datetime":"1/1/2021",
        "to_datetime":"2/1/2021",
        "time_interval":"2021-01-01T12:00:00/2021-01-02T12:00:00",
        "alignment":"Alignment=00:00", # Align to the start of the day.
        "collection":"AtmosphericPressure",
        "method":"Interpolate",
        "interval":"1day", # ??
        "gap_tolerance":"1week",
        "show_final":"Yes",
        "date_only":"Yes",
        "send_as":"NewMeasurementName",
        "agency":"LAWA",
        "format":"Native",
        "ts_type":"StdQualSeries",
        "show_quality":"Yes",
    }

    url = get_data.get_get_data_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetData&Service=Hilltop&Site=Manawatu+at+Teachers+College&Measurement=Atmospheric+Pressure&From=1%2F1%2F2021&To=2%2F1%2F2021&TimeInterval=2021-01-01T12%3A00%3A00%2F2021-01-02T12%3A00%3A00&Alignment=Alignment%3D00%3A00&Collection=AtmosphericPressure&Method=Interpolate&Interval=1day&GapTolerance=1week&ShowFinal=Yes&DateOnly=Yes&SendAs=NewMeasurementName&Agency=LAWA&Format=Native&tsType=StdQualSeries&ShowQuality=Yes"""
    )

