"""
Groundwater script for Huma.

The purpose of this script is to crosscheck the WQ entries in the database with the WQ
entries in the GW WQ files.

"""

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
    print("Columns in file:", df.columns)
    print(df.head())
    processed_sites = []

    col_lookup = {
        "Temp": [
            "Field Temperature (HRC)",
            "Temperature (HRC)",
        ],
        "EC": [
            "Field Conductivity (HRC)",
            "Conductivity (HRC)",
        ],
        "TDS": "Total Dissolved Solids (HRC)",
        "pH": [
            "Field pH (HRC)",
            "pH (HRC)",
        ],
        "Eh": "Redox Potential (HRC)",
        "Turbidity": "Turbidity EPA (HRC)",
        "Ca": [
            "Calcium Hardness (HRC)",
            "Dissolved Calcium (HRC)",
        ],
        "Mg": [
            "Acid Soluble Magnesium (HRC)",
            "Dissolved Magnesium (HRC)",
        ],
        "Na": [
            "Acid Soluble Sodium (HRC)",
            "Dissolved Sodium (HRC)",
        ],
        "K": [
            "Acid Soluble Potassium (HRC)",
            "Total Potassium (HRC)",
            "Dissolved Potassium (HRC)",
        ],
        "Fe": [
            "Acid Soluble Iron (HRC)",
            "Total Iron (HRC)",
            "Dissolved Iron (HRC)",
        ],
        "Mn": [
            "Total Manganese (HRC)",
            "Dissolved Manganese (HRC)",
        ],
        "B": [
            "Total Boron (HRC)",
            "Dissolved Boron (HRC)",
        ],
        "HCO3": [
            "Bicarbonate (HRC)",
            "Alkalinity bicarbonate (HRC)",
        ],
        "CO2": "Free Carbon Dioxide (HRC)",
        "SO4": "Sulfate (HRC)",
        "Cl": "Chloride (HRC)",
        "F": "Fluoride (HRC)",
        "Br": "Bromide (HRC)",
        "NH4": "Ammoniacal-N (HRC)",
        "NO2": "Nitrite (HRC)",
        "NO3": "Nitrate (HRC)",
        "PO4": "TDP Phosphate (HRC)",
    }

    with HilltopClient(
        hts_endpoint="Groundwater.hts",
    ) as client:
        # Get the site list
        hilltop_sites = client.get_site_list(location="Yes").to_dataframe()

        for index, row in df.iterrows():
            site_entry = {
                "access_table": filename.replace(".xlsx", ""),
                "name": None,
                "found": False,
                "found_as": None,
                "acc_easting": None,
                "acc_northing": None,
                "htp_easting": None,
                "htp_northing": None,
                "location_match": False,
                "other_names": None,
            }

            # Check the "Well" column
            if str(row["Well"]) in hilltop_sites["@Name"].values:
                site_entry["name"] = str(row["Well"])
                site_entry["found"] = True
                site_entry["found_as"] = "Well"
            elif search_for_bore_number(row["Well"]) in hilltop_sites["@Name"].values:
                site_entry["name"] = search_for_bore_number(row["Well"])
                site_entry["found"] = True
                site_entry["found_as"] = "substring of Well"
                site_entry["other_names"] = row["Well"]
            if site_entry["found"]:
                correct_site = hilltop_sites[
                    hilltop_sites["@Name"] == site_entry["name"]
                ]
                if not correct_site.empty:
                    site_entry["htp_easting"] = correct_site["Easting"].values[0]
                    site_entry["htp_northing"] = correct_site["Northing"].values[0]
            else:
                site_entry["name"] = row["Well"]

            if site_entry["found"]:
                measurement_list = client.get_measurement_list(
                    site=site_entry["name"],
                    units="Yes",
                ).to_dataframe()
                print("Measurement list for site: ", site_entry["name"])

                for col, htp_name in col_lookup.items():
                    if not isinstance(htp_name, list):
                        htp_name = [htp_name]
                    for measurement in htp_name:
                        if measurement in measurement_list["DataSource"].values:
                            found_measurement = measurement_list[
                                measurement_list["DataSource"] == measurement
                            ]["RequestAs"]

                            if not found_measurement.empty:
                                found_measurement = found_measurement.values[0]
                            print(
                                f"Found measurement {measurement} in site "
                                f"{site_entry['name']} as {found_measurement}"
                            )
                            data_value = row[col]
                            data_start_time = row["Date"]
                            data_end_time = row["Date"] + pd.Timedelta(days=1)

                            if not pd.isna(data_value):
                                print(
                                    f"Searching for value: {row[col]} "
                                    f"taken at {row['Date']}"
                                )
                                try:
                                    hts_data = client.get_data(
                                        site=site_entry["name"],
                                        measurement=found_measurement,
                                        from_datetime=str(data_start_time),
                                        to_datetime=str(data_end_time),
                                    ).to_dataframe()
                                    if not hts_data.empty:
                                        print(
                                            "Data found: ",
                                            hts_data[hts_data.columns[0]],
                                        )
                                    else:
                                        print("No data found.")
                                except HilltopResponseError as e:
                                    print(f"No data found in this time range.")
                                    hts_data = pd.DataFrame()
            processed_sites.append(site_entry)

    processed_df = pd.DataFrame(processed_sites).drop_duplicates()
    processed_df.to_csv("crosschecked_lab_measurements.csv", index=False)


if __name__ == "__main__":
    filename_1 = "access_data/GWQuality Data up to end of 2007.xlsx"
    filename_2 = "access_data/Horizons_Water_Quality.xlsx"

    handle_file_1(filename_1)
