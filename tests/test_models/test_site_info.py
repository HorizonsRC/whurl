import pytest

from hurl import site_info


def test_get_site_info_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "field_list": "FirstSynonym,MedianFlow",
        "collection": "AtmosphericPressure",
    }

    url = site_info.get_site_info_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteInfo&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&FieldList=FirstSynonym%2CMedianFlow&Collection=AtmosphericPressure"""
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_get_field_list_empty():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"

    success, field_list, url = site_info.get_field_list(base_url)

    assert success

    assert field_list == []

    assert (
        url
        == "http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteInfo&Service=Hilltop"
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_get_field_list_with_site():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"

    success, field_list, url = site_info.get_field_list(
        base_url, site="Manawatu at Teachers College"
    )

    field_list_correct = [
        "Site",
        "AEP0.01",
        "AirQNES",
        "AirQuality",
        "AirSiteCurrent",
        "Altitude",
        "BARO_CLOSEST",
        "BARO_CLOSEST_RL",
        "BARO_REF_DIST",
        "BARO_RL",
        "Catchment",
        "CatchmentArea",
        "Comment",
        "ConsentCompliance",
        "DataLicense",
        "District",
        "Easting",
        "FirstSynonym",
        "Flood2004",
        "FloodFlow10",
        "FloodFlow20",
        "FloodFlow5",
        "FloodFlow50",
        "GISTag",
        "GWQuality",
        "HIRDS",
        "Inactive",
        "LWQuality",
        "LawaFlowMeasurement",
        "LawaSiteID",
        "LawaSiteName",
        "LawaSurfaceWaterQualityMeasurement",
        "MALF7Day",
        "Macro",
        "MacroStart",
        "MaxFlow",
        "MaxFlowAt",
        "MeanAnnualFloodFlow",
        "MeanFlow",
        "MedianFlow",
        "MetNumber",
        "MinFlow",
        "MinFlowAt",
        "NZReach",
        "NZReachVersion",
        "NZSegment",
        "Northing",
        "RL0",
        "RLZero",
        "RecordingAuthority1",
        "RecordingAuthority2",
        "RiverNumber",
        "SWQAltitude",
        "SWQFrequencyAll",
        "SWQFrequencyLast5",
        "SWQLanduse",
        "Scheme",
        "SecondSynonym",
        "ShortName",
        "SiteID",
        "StatsPeriod",
        "SurfaceWaterZone",
        "UrlPhotograph",
        "XSection",
        "eQualCode",
    ]

    url_correct = "http://hilltopdev.horizons.govt.nz/boo.hts?Request=SiteInfo&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College"

    assert success
    assert field_list == field_list_correct

    assert url==url_correct
    
    
