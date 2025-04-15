"""Validating the Hilltop client fixtures."""

import pytest
from pathlib import Path


@pytest.mark.remote
def test_measurement_list_multi_response_xml_fixture(
    remote_client,
    sample_measurement_list_multi_response_xml,
):
    """Validate the XML response from Hilltop Server."""
    from hurl.models.measurement_list import HilltopMeasurementList

    cached_xml = sample_measurement_list_multi_response_xml

    with remote_client as client:
        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
        )
        print(remote_url)
        remote_xml = client.session.get(remote_url).text

    #################################################################################
    # LEAVE THIS COMMENTED this is a sneaky line to update the cached XML
    # path = Path(__file__).parent / "fixtures" / "measurement_list_multi_response.xml"
    # path.write_text(remote_xml, encoding="utf-8")
    #################################################################################

    # Remove the <To> fields from both XML's for comparison
    # (the <To> field will be different as new data is added)
    # Everything between <To> and </To> is removed

    remote_xml_cleaned = remote_xml.replace(
        remote_xml.split("<To>")[1].split("</To>")[0], "<To></To>"
    )
    cached_xml_cleaned = cached_xml.replace(
        cached_xml.split("<To>")[1].split("</To>")[0], "<To></To>"
    )

    # Also need to remove trailing whitespaces from each line
    remote_xml_cleaned = "\n".join(
        line.rstrip() for line in remote_xml_cleaned.splitlines()
    )

    cached_xml_cleaned = "\n".join(
        line.rstrip() for line in cached_xml_cleaned.splitlines()
    )

    assert remote_xml_cleaned == cached_xml_cleaned
    # assert len(response.measurements) > 0
    # assert all(isinstance(m, HilltopMeasurement) for m in response.measurements)
