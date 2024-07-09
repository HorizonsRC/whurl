from hurl import describe_feature_type


def test_describe_feature_type_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {}

    url = describe_feature_type.get_describe_feature_type_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=DescribeFeatureType&Service=WFS"""
    )
