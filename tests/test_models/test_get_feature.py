from hurl import get_feature


def test_get_feature_url():
    base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
    params = {
        "type_name": "SiteList",
        "bounding_box": "2100000,5400000,2180000,5600000,urn:ogc:def:crs:EPSG::27200",
    }

    url = get_feature.get_get_feature_url(base_url, **params)
    print(url)

    assert (
        url == 
        """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetFeature&Service=WFS&TypeName=SiteList&BBox=2100000%2C5400000%2C2180000%2C5600000%2Curn%3Aogc%3Adef%3Acrs%3AEPSG%3A%3A27200"""
    )

