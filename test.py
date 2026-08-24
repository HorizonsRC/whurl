from whurl.client import HilltopClient
from whurl.schemas.responses import GetDataResponse

client = HilltopClient(
    base_url="http://hilltopdev.horizons.govt.nz",
    hts_endpoint="AllDataMerge.hts",
    timeout=60  # Optional, defaults to 60 seconds
)

with client:
    filepath = "./processed_cond.xml"
    with open(filepath, 'r', encoding="utf-8") as file:
        xml = file.read()
        
        data = GetDataResponse.from_xml(xml)

        for meas in data.measurements:
            df = meas.data.timeseries
            print(df)
            print(df.dtypes)
            if "Comment" in df.columns:
                for i, row in df.iterrows():
                    print(row)
                    print(row["Comment"])
                    print(type(row["Comment"]))
