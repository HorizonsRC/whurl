from hurl import collection_list
import pytest


def test_get_collection_list_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {}

    url = collection_list.get_collection_list_url(base_url, **params)
    print(url)

    assert (
        url
        == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=CollectionList&Service=Hilltop"""
    )


@pytest.mark.slow()
@pytest.mark.remote()
def test_get_collection_list():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"

    correct_list = [
        "Air Quality 1.5m Air Temp",
        "Air Quality 10m Air Temp",
        "Air Quality PM10",
        "Air Quality PM2.5",
        "AirTemperature",
        "AtmosphericPressure",
        "Blue Green Algae",
        "CDEM RIVER Heights",
        "Chlorophyll",
        "Conductivity",
        "DissolvedOxygen",
        "FireWeatherIndex",
        "Flow",
        "Flow-DailyVolume",
        "Flow-Distribution",
        "Groundwater-Manual",
        "Groundwater-Telemetered",
        "Humidity",
        "IVR State",
        "Lahar",
        "Moving Total 1 Hour",
        "Solar Flux",
        "Lightning Strikes",
        "Nitrate",
        "Oxidation-Reduction Potential (ORP)",
        "pH",
        "Predicted Flow",
        "Rainfall",
        "RainfallMonthlyDeviation",
        "River Level",
        "SoilMoisture",
        "SoilTemperature",
        "SwimSpotsCyanobacteria",
        "SwimSpotsEcoli",
        "SwimSpotsEnterococci",
        "TDCBiomonitoring",
        "Turbidity",
        "TRC",
        "WaterMatters",
        "WaterMattersDailySummary",
        "WaterMattersSubzoneSummary-TotalAllocated",
        "WaterMattersSubzoneSummary-TotalUsed",
        "WaterMattersZoneSummary-TotalAllocated",
        "WaterMattersZoneSummary-TotalUsed",
        "WaterTemperature",
        "WindDirection",
        "WindSpeed",
        "WindGust",
        "zContactRec",
        "zForecastRiverFlow",
        "zsummary",
        "zdistrictsummary",
        "zTrial Nitrate",
        "zVirtual Rainfall",
    ]

    correct_url = "http://hilltopdev.horizons.govt.nz/boo.hts?Request=CollectionList&Service=Hilltop"
    
    success, collection_list_ret, url = collection_list.get_collection_list(
        base_url
    )

    assert success

    assert collection_list_ret == correct_list
    assert url == correct_url
