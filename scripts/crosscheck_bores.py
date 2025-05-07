"""
Groundwater script for Huma.

The purpose of this script is to cross check the access data dump with the sites
contained in '//ares/Environmental Archive/Groundwater Archive WQ.hts'.

The access data was dumped into .xlsx files in the /access_data directory.

"""

import os
import re

import pandas as pd

from hurl.client import HilltopClient


def search_for_bore_number(text):
    """Search for a six digit bore number in the text."""
    pattern = r"\b\d{6}\b"

    match = re.search(pattern, str(text))

    return match.group(0) if match else None


if __name__ == "__main__":

    # Create a HurlClient instance with default settings (from .env)
    # The HurlClient can be used as a context manager for automatic cleanup
    with HilltopClient(hts_endpoint="Groundwater.hts") as client:
        # Get the list of sites from the HurlClient
        hilltop_sites = client.get_site_list(location="Yes").to_dataframe()

    # Convert the list of sites to a DataFrame

    print("Hilltop sites:", hilltop_sites)

    # Handling each file separately.

    processed_sites = []
    ###################################################################################
    # GW Qual data from Qualarc-ALL bore IDs - Oct 2012 (CAUTION no__).xlsx
    ###################################################################################
    filename_1 = "GW Qual data from Qualarc-ALL bore IDs - Oct 2012 (CAUTION no__).xlsx"
    print("Processing file:", filename_1)
    # Read the Excel file into a DataFrame
    df_1 = pd.read_excel(os.path.join("access_data/", filename_1))
    print("Columns in file:", df_1.columns)
    print(df_1.head())
    # Check if the site ids are in the hilltop_sites

    for index, row in df_1.iterrows():
        site_entry = {
            "access_table": filename_1.replace(".xlsx", ""),
            "name": None,
            "found": False,
            "found_as": None,
            "acc_easting": row["easting"],
            "acc_northing": row["northing"],
            "htp_easting": None,
            "htp_northing": None,
            "location_match": False,
        }

        # Check the "site_id" column
        if row["site_id"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_id"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["source_name"]),
                    str(row["site_name"]),
                ]
            )
        elif search_for_bore_number(row["site_id"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_id"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                ]
            )
        # Check the "source_name" column
        elif row["source_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["source_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["site_name"]),
                ]
            )
        elif (
            search_for_bore_number(row["source_name"]) in hilltop_sites["@Name"].values
        ):
            site_entry["name"] = search_for_bore_number(row["source_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                ]
            )
        # Check the "site_name" column
        elif row["site_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                ]
            )
        elif search_for_bore_number(row["site_name"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                ]
            )
        if not site_entry["found"]:
            loc_match = hilltop_sites[
                (hilltop_sites["Easting"] == row["easting"])
                & (hilltop_sites["Northing"] == row["northing"])
            ]
            if not loc_match.empty:
                site_entry["name"] = loc_match["@Name"].values[0]
                site_entry["found"] = True
                site_entry["found_as"] = "location_match"
                site_entry["other_names"] = ",".join(
                    loc_match["@Name"].unique().tolist()
                )
                site_entry["location_match"] = True
                site_entry["htp_easting"] = loc_match["Easting"].values[0]
                site_entry["htp_northing"] = loc_match["Northing"].values[0]
            else:
                site_entry["name"] = row["site_id"]
                site_entry["found"] = False
                site_entry["found_as"] = None
                site_entry["other_names"] = ",".join(
                    [
                        str(row["site_name"]),
                        str(row["source_name"]),
                        search_for_bore_number(
                            ",".join(
                                [
                                    str(row["site_id"]),
                                    str(row["source_name"]),
                                    str(row["site_name"]),
                                ]
                            )
                        ),
                    ]
                )
        else:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["location_match"] = (
                    correct_site["Easting"].values[0] == row["easting"]
                ) and (correct_site["Northing"].values[0] == row["northing"])
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]

        processed_sites.append(site_entry)

    ###################################################################################
    # GW Qual data from Qualarc-Bore ID missing-Oct2012 (CAUTION no__).xlsx
    ###################################################################################
    filename_2 = "GW Qual data from Qualarc-Bore ID missing-Oct2012 (CAUTION no__).xlsx"
    print("Processing file:", filename_2)
    # Read the Excel file into a DataFrame
    df_2 = pd.read_excel(os.path.join("access_data", filename_2))
    print("Columns in file:", df_2.columns)
    print(df_2.head())

    for index, row in df_2.iterrows():
        site_entry = {
            "access_table": filename_2.replace(".xlsx", ""),
            "name": None,
            "found": False,
            "found_as": None,
            "acc_easting": row["easting"],
            "acc_northing": row["northing"],
            "htp_easting": None,
            "htp_northing": None,
            "location_match": False,
        }

        # Check the "site_id" column
        if row["site_id"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_id"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        elif search_for_bore_number(row["site_id"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_id"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        # Check the "source_name" column
        elif row["source_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["source_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        elif (
            search_for_bore_number(row["source_name"]) in hilltop_sites["@Name"].values
        ):
            site_entry["name"] = search_for_bore_number(row["source_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        # Check the "site_name" column
        elif row["site_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        elif search_for_bore_number(row["site_name"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        # Check the "Bore number (estimated)" column
        elif row["Bore number (estimated)"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["Bore number (estimated)"]
            site_entry["found"] = True
            site_entry["found_as"] = "Bore number (estimated)"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                ]
            )
        elif (
            search_for_bore_number(row["Bore number (estimated)"])
            in hilltop_sites["@Name"].values
        ):
            site_entry["name"] = search_for_bore_number(row["Bore number (estimated)"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of Bore number (estimated)"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["Bore number (estimated)"]),
                ]
            )
        if not site_entry["found"]:
            loc_match = hilltop_sites[
                (hilltop_sites["Easting"] == row["easting"])
                & (hilltop_sites["Northing"] == row["northing"])
            ]
            if not loc_match.empty:
                site_entry["name"] = loc_match["@Name"].values[0]
                site_entry["found"] = True
                site_entry["found_as"] = "location match"
                site_entry["other_names"] = ",".join(
                    loc_match["@Name"].unique().tolist()
                )
                site_entry["location_match"] = True
                site_entry["htp_easting"] = loc_match["Easting"].values[0]
                site_entry["htp_northing"] = loc_match["Northing"].values[0]
            else:
                site_entry["name"] = row["site_id"]
                site_entry["found"] = False
                site_entry["found_as"] = None
                site_entry["other_names"] = ",".join(
                    [
                        str(row["site_name"]),
                        str(row["source_name"]),
                        str(row["Bore number (estimated)"]),
                    ]
                )
        else:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["location_match"] = (
                    correct_site["Easting"].values[0] == row["easting"]
                ) and (correct_site["Northing"].values[0] == row["northing"])
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]

        processed_sites.append(site_entry)

    ###################################################################################
    # GW Quality SOE Sites 19072016.xlsx
    ###################################################################################
    filename_3 = "GW Quality SOE Sites 19072016.xlsx"
    print("Processing file:", filename_3)
    # Read the Excel file into a DataFrame
    df_3 = pd.read_excel(os.path.join("access_data", filename_3))
    print("Columns in file:", df_3.columns)
    print(df_3.head())

    for index, row in df_3.iterrows():
        site_entry = {
            "access_table": filename_3.replace(".xlsx", ""),
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

        # Check the "Well ID" column
        if str(row["Well ID"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = str(row["Well ID"])
            site_entry["found"] = True
            site_entry["found_as"] = "Well ID"
        elif search_for_bore_number(row["Well ID"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["Well ID"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of Well ID"
            site_entry["other_names"] = row["Well ID"]
        if site_entry["found"]:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]
        else:
            site_entry["name"] = row["Well ID"]

        processed_sites.append(site_entry)

    ###################################################################################
    # GWQuality Data up to end of 2007.xlsx
    ###################################################################################
    filename_4 = "GWQuality Data up to end of 2007.xlsx"
    print("Processing file:", filename_4)
    # Read the Excel file into a DataFrame
    df_4 = pd.read_excel(os.path.join("access_data", filename_4))
    print("Columns in file:", df_4.columns)
    print(df_4.head())

    for index, row in df_4.iterrows():
        site_entry = {
            "access_table": filename_4.replace(".xlsx", ""),
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
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]
        else:
            site_entry["name"] = row["Well"]

        processed_sites.append(site_entry)

    ###################################################################################
    # GW_Quality_All_bores_Oct2012_stationID_appended (CAUTION no __).xlsx
    ###################################################################################
    filename_5 = "GW_Quality_All_bores_Oct2012_stationID_appended (CAUTION no __).xlsx"
    print("Processing file:", filename_5)
    # Read the Excel file into a DataFrame
    df_5 = pd.read_excel(os.path.join("access_data", filename_5))
    print("Columns in file:", df_5.columns)
    print(df_5.head())

    for index, row in df_5.iterrows():
        site_entry = {
            "access_table": filename_5.replace(".xlsx", ""),
            "name": None,
            "found": False,
            "found_as": None,
            "acc_easting": row["easting"],
            "acc_northing": row["northing"],
            "htp_easting": None,
            "htp_northing": None,
            "location_match": False,
        }

        # Check the "site_id" column
        if row["site_id"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_id"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        elif search_for_bore_number(row["site_id"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_id"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        # Check the "source_name" column
        elif row["source_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["source_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        elif (
            search_for_bore_number(row["source_name"]) in hilltop_sites["@Name"].values
        ):
            site_entry["name"] = search_for_bore_number(row["source_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of source_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        # Check the "site_name" column
        elif row["site_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["site_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        elif search_for_bore_number(row["site_name"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["site_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of site_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        # Check the "station_id" column
        elif row["station_id"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["station_id"]
            site_entry["found"] = True
            site_entry["found_as"] = "station_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_name"]),
                ]
            )
        elif search_for_bore_number(row["station_id"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = search_for_bore_number(row["station_id"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of station_id"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        # Check the "station_name" column
        elif row["station_name"] in hilltop_sites["@Name"].values:
            site_entry["name"] = row["station_name"]
            site_entry["found"] = True
            site_entry["found_as"] = "station_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                ]
            )
        elif (
            search_for_bore_number(row["station_name"]) in hilltop_sites["@Name"].values
        ):
            site_entry["name"] = search_for_bore_number(row["station_name"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of station_name"
            site_entry["other_names"] = ",".join(
                [
                    str(row["site_id"]),
                    str(row["source_name"]),
                    str(row["site_name"]),
                    str(row["station_id"]),
                    str(row["station_name"]),
                ]
            )
        if not site_entry["found"]:
            loc_match = hilltop_sites[
                (hilltop_sites["Easting"] == row["easting"])
                & (hilltop_sites["Northing"] == row["northing"])
            ]
            if not loc_match.empty:
                site_entry["name"] = loc_match["@Name"].values[0]
                site_entry["found"] = True
                site_entry["found_as"] = "location match"
                site_entry["other_names"] = ",".join(
                    loc_match["@Name"].unique().tolist()
                )
                site_entry["location_match"] = True
                site_entry["htp_easting"] = loc_match["Easting"].values[0]
                site_entry["htp_northing"] = loc_match["Northing"].values[0]
            else:
                site_entry["name"] = row["site_id"]
                site_entry["found"] = False
                site_entry["found_as"] = None
                site_entry["other_names"] = ",".join(
                    [
                        str(row["site_name"]),
                        str(row["source_name"]),
                        str(row["station_id"]),
                        str(row["station_name"]),
                    ]
                )
        else:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["location_match"] = (
                    correct_site["Easting"].values[0] == row["easting"]
                ) and (correct_site["Northing"].values[0] == row["northing"])
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]

        processed_sites.append(site_entry)

    ###################################################################################
    # Horizons regions bore list Oct 2012.xlsx
    ###################################################################################
    filename_6 = "Horizons regions bore list Oct 2012.xlsx"
    print("Processing file:", filename_6)
    # Read the Excel file into a DataFrame
    df_6 = pd.read_excel(os.path.join("access_data", filename_6))
    print("Columns in file:", df_6.columns)
    print(df_6.head())

    for index, row in df_6.iterrows():
        site_entry = {
            "access_table": filename_6.replace(".xlsx", ""),
            "name": None,
            "found": False,
            "found_as": None,
            "acc_easting": row["Easting"],
            "acc_northing": row["Northing"],
            "htp_easting": None,
            "htp_northing": None,
            "location_match": False,
            "other_names": None
        }

        # Check the "site_id" column
        if str(row["BoreID"]) in hilltop_sites["@Name"].values:
            site_entry["name"] = row["BoreID"]
            site_entry["found"] = True
            site_entry["found_as"] = "BoreID"
        if not site_entry["found"]:
            loc_match = hilltop_sites[
                (hilltop_sites["Easting"] == row["Easting"])
                & (hilltop_sites["Northing"] == row["Northing"])
            ]
            if not loc_match.empty:
                site_entry["name"] = loc_match["@Name"].values[0]
                site_entry["found"] = True
                site_entry["found_as"] = "location_match"
                site_entry["other_names"] = row["BoreID"]
                site_entry["location_match"] = True
                site_entry["htp_easting"] = loc_match["Easting"].values[0]
                site_entry["htp_northing"] = loc_match["Northing"].values[0]
            else:
                site_entry["name"] = row["BoreID"]
                site_entry["found"] = False
                site_entry["found_as"] = None
        else:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]
            if not correct_site.empty:
                site_entry["location_match"] = (
                    correct_site["Easting"].values[0] == row["Easting"]
                ) and (correct_site["Northing"].values[0] == row["Northing"])
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]

        processed_sites.append(site_entry)

    ###################################################################################
    # Horizons_Water_Quality.xlsx
    ###################################################################################
    filename_7 = "Horizons_Water_Quality.xlsx"
    print("Processing file:", filename_7)
    # Read the Excel file into a DataFrame
    df_7 = pd.read_excel(os.path.join("access_data", filename_7))
    print("Columns in file:", df_7.columns)
    print(df_7.head())

    for index, row in df_7.iterrows():
        site_entry = {
            "access_table": filename_7.replace(".xlsx", ""),
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
        if (
            row["Station_ID"] is not None
            and str(int(row["Station_ID"])) in hilltop_sites["@Name"].astype(str).values
        ):
            site_entry["name"] = str(int(row["Station_ID"]))
            site_entry["found"] = True
            site_entry["found_as"] = "Station_ID"
        elif (
            search_for_bore_number(row["Station_ID"])
            in hilltop_sites["@Name"].astype(str).values
        ):
            site_entry["name"] = search_for_bore_number(row["Station_ID"])
            site_entry["found"] = True
            site_entry["found_as"] = "substring of Station_ID"
            site_entry["other_names"] = row["Station_ID"]
        if site_entry["found"]:
            correct_site = hilltop_sites[hilltop_sites["@Name"] == site_entry["name"]]

            if not correct_site.empty:
                site_entry["htp_easting"] = correct_site["Easting"].values[0]
                site_entry["htp_northing"] = correct_site["Northing"].values[0]
        else:
            site_entry["name"] = row["Station_ID"]

        processed_sites.append(site_entry)

    # Create a DataFrame from the processed sites
    processed_df = pd.DataFrame(processed_sites).drop_duplicates()
    processed_df.to_csv("processed_sites.csv", index=False)
