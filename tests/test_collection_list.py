from hurl import collection_list


def test_get_time_range_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "service": "Hilltop",
    }

    url = collection_list.get_collection_list_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=CollectionList&Service=Hilltop"""
    )
