from hurl.client import HilltopClient
from hurl.models.measurement_list import HilltopMeasurementList
import pytest


@pytest.fixture
def sample_single_measurement_url():
    return (
        "http://hilltopdev.horizons.govt.nz/boo.hts?Service=Hilltop"
        "&Request=MeasurementList"
        "&Site=Manawatu at Teachers College"
        "&Collection=AtmosphericPressure"
    )


def test_measurement_list_from_xml(
    sample_measurement_list_multi_response_xml
):
    """Test that the sample XML can be parsed into a HilltopMeasurementList object."""
    cached_xml = sample_measurement_list_multi_response_xml

    # Parse the XML into a HilltopMeasurementList object
    measurement_list = HilltopMeasurementList.from_xml(cached_xml)

    # Test the top level response object
    assert isinstance(measurement_list, HilltopMeasurementList)
    assert measurement_list.agency == "Horizons"

    # Test a specific data source
    water_level_ds = next(
        (ds for ds in measurement_list.data_sources if ds.name == "Water Level"),
        None,
    )
    assert water_level_ds.site == "Manawatu at Teachers College"
    assert len(water_level_ds.measurements) > 0

    # Test a specific measurement
    stage_measurement = next(
        (m for m in water_level_ds.measurements if m.name == "Stage"), None
    )
    mean_v_measurement = next(
        (m for m in water_level_ds.measurements if m.name == "Mean Velocity"), None
    )

    assert stage_measurement.units == "mm"
    assert stage_measurement.default_measurement is True
    assert mean_v_measurement.default_measurement is False

    ml_df = measurement_list.to_dataframe()
    ml_df.to_csv("measurement_list.csv", index=False)
