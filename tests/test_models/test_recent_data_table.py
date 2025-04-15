from hurl import recent_data_table


def test_get_recent_data_table_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "collection": "AtmosphericPressure",
        "scoll": "Northern",
        "mcoll": "Nutrients",
    }

    url = recent_data_table.get_recent_data_table_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=RecentDataTable&Service=Hilltop&Collection=AtmosphericPressure&SColl=Northern&MColl=Nutrients"""
    )
