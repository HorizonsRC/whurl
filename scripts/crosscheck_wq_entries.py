"""
Groundwater script for Huma.

The purpose of this script is to crosscheck the WQ entries in the database with the WQ
entries in the GW WQ files.

"""

import os

import pandas as pd

from hurl.client import HilltopClient


def handle_file_1(filename):
    """Handle file access_data/GWQuality Data up to end of 2007.xlsx."""
    print("Processing file: ", filename)
    # Read the Excel file into a DataFrame
    df = pd.read_excel(filename)
    print("Columns in file:", df.columns)
    print(df.head())

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


if __name__ == "__main__":
    filename_1 = "access_data/GWQuality Data up to end of 2007.xlsx"
    filename_2 = "access_data/Horizons_Water_Quality.xlsx"

    handle_file_1(filename_1)
