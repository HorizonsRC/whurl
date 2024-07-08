from hurl import site_info


def test_get_site_info_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "field_list": "FirstSynonym,MedianFlow",
        "collection": "AtmosphericPressure"
    }

    url = site_info.get_site_info_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteInfo&Service=Hilltop&Site=Manawatu+at+Teachers+College&FieldList=FirstSynonym%2CMedianFlow&Collection=AtmosphericPressure"""
    )
