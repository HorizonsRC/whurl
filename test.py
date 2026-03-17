from whurl.client import HilltopClient

client = HilltopClient(
    base_url="http://hilltopdev.horizons.govt.nz",
    hts_endpoint="AllDataMerge.hts",
    timeout=60  # Optional, defaults to 60 seconds
)

with client:
    status = client.get_status()
    print(f"Server status: {status}")

    measurements = client.get_measurement_list(site="Manawatu at Teachers College")

    print(measurements.measurements)
