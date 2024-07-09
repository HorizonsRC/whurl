
from hurl import get_observation


def test_get_observation_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "site_name": "Manawatu at Teachers College",
        "measurement": "AtmosphericPressure",
        "time_range": "TemporalFilter=om:phenomenonTime,2010-01-01T12:00:00/2011-07-01T14:00:00",
        
    }

    url = get_observation.get_get_observation_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetObservation&Service=SOS&FeatureOfInterest=Manawatu+at+Teachers+College&ObservedProperty=AtmosphericPressure&TemporalFilter=TemporalFilter%3Dom%3AphenomenonTime%2C2010-01-01T12%3A00%3A00%2F2011-07-01T14%3A00%3A00"""
    )
