"""
Sos calls for the flood server project.

This is a simple script for stringing up a bunch of server calls to be used in the flood server project.

"""

import pandas as pd
import yaml

from hurl.get_observation import get_get_observation_url
from hurl.measurement_list import get_measurement_list
from hurl.site_list import get_site_list

# Read in all the hts file file aliases a file.
with open("data_files.txt") as f:
    # The data file name is everything before the '=' on each line.
    data_file_names = [line.split("=")[0] for line in f]

print(data_file_names)

# Read in the config yaml file.
with open("config.yaml") as f:
    config = yaml.safe_load(f)
    print(config)

# The base url for the sos server.
base_url = config["base_url"]
# The measurement list.
measurements = config["measurements"]
print(measurements)

# For the full site list, we need to use the SiteList request on each of the hts files.
compiled_url_data = []
for hts_alias in data_file_names:
    full_base_url = f"https://{base_url}/{hts_alias}.hts"
    site_list = get_site_list(full_base_url)

    # Now we can construct a sos call for each measurement/site combo.
    for site in site_list[1]:
        measurement_df = get_measurement_list(full_base_url, site)[1]

        if not measurement_df.empty:
            # Create a column with the name in the 'Measurement [DataSource]' format
            measurement_df["FullName"] = (
                measurement_df["Measurement"] + " [" + measurement_df["DataSource"] + "]"
            )
        for measurement in measurements:
            if measurement in ["RL Section"]:
                # RL Sections don't show up in MeasurementList, so I'm just going to hope that it's available.
                print(
                    f"Measurement is a '{measurement}'. Going for it."
                )
                correct_name = "RL Section"
            elif measurement_df.empty:
                print(f"No measurements at {site}, so probably no {measurement}.")
                continue
            elif measurement in list(measurement_df["RequestAs"].values):
                # Measurement is found with its request name
                correct_name = measurement_df[
                    measurement_df["RequestAs"] == measurement
                ]["Measurement"].values[0]
                print(
                    f"Found measurement '{measurement}' under RequestAs of {correct_name}"
                )
            elif measurement in list(measurement_df["Measurement"].values):
                # Measurement is found with its measurement name
                correct_name = measurement
                print(f"Found measurement {measurement}.")
            elif measurement in list(measurement_df["FullName"].values):
                correct_name = measurement_df[
                    measurement_df["FullName"] == measurement
                ]["Measurement"].values[0]
                print(
                    f"Found measurement '{measurement}' under FullName of {correct_name}"
                )
            else:
                print(f"Measurement {measurement} not available for site {site}.")
                continue

            if correct_name == "RL Section":
                from_date = None
                request_name = "RL Section"
            else:
                from_date = measurement_df[measurement_df["Measurement"] == correct_name][
                    "From"
                ].values[0]
                request_name = measurement_df[measurement_df["Measurement"] == correct_name][
                    "RequestAs"
                ].values[0]
            print(f"From date: {from_date}")

            if from_date is not None:
                from_date = f"om:phenomenonTime,{from_date}"

            url = get_get_observation_url(
                full_base_url,
                site_name=site,
                measurement=request_name,
                time_range=from_date,
            )
            compiled_row = {
                "DataFile": hts_alias,
                "BaseURL": full_base_url,
                "Site": site,
                "Measurement": correct_name,
                "RequestAs": request_name,
                "StartDate": from_date,
                "URL": url,
            }
            compiled_url_data.append(compiled_row)
        print("-------------------------------------")
    print("=====================================")

url_df = pd.DataFrame(compiled_url_data)

url_df.to_csv("urls.csv", index=False)
