from hurl import ensemble_stats


def test_get_ensemble_stats_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site": "Manawatu at Teachers College",
        "measurement": "Atmospheric Pressure",
        "statistic": "MeanDailyExtrema",
        "collection": "AtmosphericPressure"
    }

    url = ensemble_stats.get_ensemble_stats_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=EnsembleStats&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Measurement=Atmospheric%20Pressure&Statistic=MeanDailyExtrema&Collection=AtmosphericPressure"""
    )
