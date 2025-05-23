"""
Groundwater script for Huma.

The purpose of this script is to crosscheck the WQ entries in the database with the WQ
entries in the GW WQ files.

"""

import json
import os
import re

import pandas as pd

from hurl.client import HilltopClient
from hurl.exceptions import HilltopResponseError

pd.set_option("display.max_rows", None)  # Show all rows
pd.set_option("display.max_columns", None)  # Show all columns
pd.set_option("display.width", None)  # Auto-detect terminal width
pd.set_option("display.max_colwidth", None)  # Show full column content


def search_for_bore_number(text):
    """Search for a six digit bore number in the text."""
    pattern = r"\b\d{6}\b"

    match = re.search(pattern, str(text))

    return match.group(0) if match else None


def handle_file_1(filename):
    """Handle file access_data/GWQuality Data up to end of 2007.xlsx."""
    print("Processing file: ", filename)
    # Read the Excel file into a DataFrame
    df = pd.read_excel(filename)
    print("columns in file:", df.columns)
    print(df.head())
    processed_sites = []

    # Read in the col lookup from a json file
    with open("param_lookup_DB1.json", "r") as f:
        col_lookup = json.load(f)
    records = df.melt(id_vars=["Well", "Date"], value_vars=col_lookup.keys())
    # Drop all records with value = nan
    records = records.dropna(subset=["value"])

    with HilltopClient(
        hts_endpoint="Groundwater.hts",
    ) as client:
        results = []

        well_param_cache = {}
        hilltop_sites = client.get_site_list(location="Yes").to_dataframe()
        for index, row in records.iterrows():
            print("================================================")
            print(
                f"Processing row {index}: Date={row['Date']}, "
                f"Var={row['variable']}, Value={row['value']}"
            )
            entry = {
                "well": row["Well"],
                "well found": None,
                "parameter": row["variable"],
                "parameter found": None,
                "found under data source": None,
                "found as measurement": None,
                "record date": row["Date"],
                "record value": row["value"],
                "timestamp match": None,
                "value match": None,
                "record value in hts": None,
            }

            # Check if well in sites
            if str(row["Well"]) in hilltop_sites["@Name"].values:
                entry["well found"] = True
                print("Found well: ", row["Well"])
                # Find a measurement_list for this well
                if str(row["Well"]) in well_param_cache:
                    well_params = well_param_cache[str(row["Well"])]
                else:
                    well_params = client.get_measurement_list(
                        site=str(row["Well"]),
                        units="Yes",
                    ).to_dataframe()
                    well_param_cache[str(row["Well"])] = well_params
                # Check if variable in well_params under any name
                poss_names = col_lookup[row["variable"]]
                for name in poss_names:
                    if name in well_params["DataSource"].values:
                        entry["parameter found"] = True
                        entry["found under data source"] = name
                        found_measurement = well_params[
                            well_params["DataSource"] == name
                        ]["RequestAs"]
                        if not found_measurement.empty:
                            print(
                                f"Found variable {row['variable']} "
                                f"as {found_measurement.values[0]}"
                            )
                            entry["found as measurement"] = found_measurement.values[0]
                        else:
                            print(
                                f"Found data source {row['variable']} "
                                f"but no measurement found"
                            )
                            entry["found as measurement"] = None
                        try:
                            hts_data = client.get_data(
                                site=str(row["Well"]),
                                measurement=entry["found as measurement"],
                                from_datetime=str(row["Date"]),
                                to_datetime=str(row["Date"]),
                            ).to_dataframe()
                            if not hts_data.empty:
                                found_data = hts_data[hts_data.columns[0]].values[0]
                                entry["timestamp match"] = True
                                print(
                                    "Timestamp match: ",
                                    hts_data,
                                )
                                if float(found_data) == float(row["value"]):
                                    print(
                                        f"Data matches: {row['value']} == "
                                        f"{found_data}"
                                    )
                                    entry["value match"] = True
                                    entry["record value in hts"] = found_data
                                    break
                                elif (
                                    (float(found_data) * 10 == float(row["value"]))
                                    or (float(found_data) / 10 == float(row["value"]))
                                    or (
                                        (  # data within 10% of each other
                                            float(found_data) * 0.9
                                            <= float(row["value"])
                                        )
                                        and (
                                            float(found_data) * 1.1
                                            >= float(row["value"])
                                        )
                                    )
                                ):
                                    print("Close match:")
                                    entry["value match"] = "close"
                                    entry["record value in hts"] = found_data
                                else:
                                    print(
                                        f"Data does not match: {row['value']} != "
                                        f"{found_data}"
                                    )
                                    entry["value match"] = False
                                    entry["record value in hts"] = found_data
                            else:
                                print("No data found.")
                                entry["timestamp match"] = False
                        except HilltopResponseError:
                            print(f"No data found in this time range.")
                            entry["timestamp match"] = False
                if entry["parameter found"] is None:
                    print(f"Parameter not found: {row['variable']}")
                    entry["parameter found"] = False
            else:
                print(f"Well not found: {row['Well']}")
                entry["well found"] = False
            results.append(entry)

        results_df = pd.DataFrame(results)
        results_df.to_csv("wq_crosscheck_results_db1.csv", index=False)

        post_map = {}
        for index, row in results_df.iterrows():
            if row["parameter"] not in post_map.keys():
                post_map[row["parameter"]] = {}

            if row["found under data source"] is None:
                key = "None"
            else:
                key = row["found under data source"]
            if key in post_map[row["parameter"]].keys():
                post_map[row["parameter"]][key] += 1
            else:
                post_map[row["parameter"]][key] = 1

        # Save the post_map to a json file
        with open("parameter_results_db1.json", "w") as f:
            json.dump(post_map, f, indent=4)


def handle_file_2(filename):
    """Handle file access_data/GWQuality Data up to end of 2007.xlsx."""
    print("Processing file: ", filename)
    # Read the Excel file into a DataFrame
    df = pd.read_excel(filename, dtype={"Station_ID": str})
    print("columns in file:", df.columns)
    print(df.head())
    processed_sites = []

    # Read in the col lookup from a json file
    with open("param_lookup_DB2.json", "r") as f:
        col_lookup = json.load(f)

    records = df.dropna(subset=["Value"])

    with HilltopClient(
        hts_endpoint="Groundwater.hts",
    ) as client:
        results = []

        well_param_cache = {}
        hilltop_sites = client.get_site_list(location="Yes").to_dataframe()
        for index, row in records.iterrows():
            print("================================================")
            print(
                f"Processing row {index}: Date={row['Date_Collected']}, "
                f"Var={row['Parameter']}, Value={row['Value']}"
            )
            entry = {
                "well": row["Station_ID"],
                "well found": None,
                "parameter": row["Parameter"],
                "parameter found": None,
                "found under data source": None,
                "found as measurement": None,
                "record date": row["Date_Collected"],
                "record value": row["Value"],
                "timestamp match": None,
                "value match": None,
                "record value in hts": None,
            }

            # Check if well in sites
            if str(row["Station_ID"]) in hilltop_sites["@Name"].values:
                entry["well found"] = True
                print("Found well: ", row["Station_ID"])
                # Find a measurement_list for this well
                if str(row["Station_ID"]) in well_param_cache:
                    well_params = well_param_cache[str(row["Station_ID"])]
                else:
                    well_params = client.get_measurement_list(
                        site=str(row["Station_ID"]),
                        units="Yes",
                    ).to_dataframe()
                    well_param_cache[str(row["Station_ID"])] = well_params
                # Check if Parameter in well_params under any name
                poss_names = col_lookup[row["Parameter"]]
                if poss_names is None:
                    entry["parameter found"] = False
                    continue

                for name in poss_names:
                    if name in well_params["DataSource"].values:
                        entry["parameter found"] = True
                        entry["found under data source"] = name
                        found_measurement = well_params[
                            well_params["DataSource"] == name
                        ]["RequestAs"]
                        if not found_measurement.empty:
                            print(
                                f"Found Parameter {row['Parameter']} "
                                f"as {found_measurement.values[0]}"
                            )
                            entry["found as measurement"] = found_measurement.values[0]
                        else:
                            print(
                                f"Found data source {row['Parameter']} "
                                f"but no measurement found"
                            )
                            entry["found as measurement"] = None
                        try:
                            hts_data = client.get_data(
                                site=str(row["Station_ID"]),
                                measurement=entry["found as measurement"],
                                from_datetime=str(row["Date_Collected"]),
                                to_datetime=str(row["Date_Collected"]),
                            ).to_dataframe()
                            if not hts_data.empty:
                                found_data = hts_data[hts_data.columns[0]].values[0]
                                entry["timestamp match"] = True
                                # handle the case where the value is a string
                                try:
                                    value = float(row["Value"])
                                    found_data = float(found_data)
                                except ValueError:
                                    if str(row["Value"]) == str(found_data):
                                        entry["value match"] = True
                                        entry["record value in hts"] = found_data
                                    break

                                if found_data == value:
                                    print(
                                        f"Data matches: {row['Value']} == "
                                        f"{found_data}"
                                    )
                                    entry["value match"] = True
                                    entry["record value in hts"] = found_data
                                    break
                                elif (
                                    (found_data * 10 == value)
                                    or (found_data / 10 == value)
                                    or (
                                        (  # data within 10% of each other
                                            found_data * 0.9 <= value
                                        )
                                        and (found_data * 1.1 >= value)
                                    )
                                ):
                                    print("Close match:")
                                    entry["value match"] = "close"
                                    entry["record value in hts"] = found_data
                                else:
                                    print(
                                        f"Data does not match: {row['Value']} != "
                                        f"{found_data}"
                                    )
                                    entry["value match"] = False
                                    entry["record value in hts"] = found_data
                            else:
                                print("No data found.")
                                entry["timestamp match"] = False
                        except HilltopResponseError:
                            print(f"No data found in this time range.")
                            entry["timestamp match"] = False
                if entry["parameter found"] is None:
                    print(f"Parameter not found: {row['Parameter']}")
                    entry["parameter found"] = False
            else:
                print(f"Station_ID not found: {row['Station_ID']}")
                entry["well found"] = False
            results.append(entry)

        results_df = pd.DataFrame(results)
        results_df.to_csv("wq_crosscheck_results_db2.csv", index=False)

        print("Results saved to wq_crosscheck_results_db2.csv")

        # Get all the unique parameters

        post_map = {}
        for index, row in results_df.iterrows():
            if row["parameter"] not in post_map.keys():
                post_map[row["parameter"]] = {}

            if row["found under data source"] is None:
                key = "None"
            else:
                key = row["found under data source"]
            if key in post_map[row["parameter"]].keys():
                post_map[row["parameter"]][key] += 1
            else:
                post_map[row["parameter"]][key] = 1

        # Save the post_map to a json file

        with open("parameter_results_db2.json", "w") as f:
            json.dump(post_map, f, indent=4)


if __name__ == "__main__":
    filename_1 = "access_data/GWQuality Data up to end of 2007.xlsx"
    filename_2 = "access_data/Horizons_Water_Quality.xlsx"

    handle_file_1(filename_1)

    handle_file_2(filename_2)
