"""
One-off build script: merges the raw Climate TRACE per-jurisdiction CSVs (68
fine-grained `original_inventory_sector` sub-sectors x 5 gases) into
data/SMAC_ch4_subsectors.csv — CH4 only, monthly, tagged with both the
sub-sector and its parent broad sector (matches SECTOR_ORDER in data_loader.py).

Not run automatically by the app — re-run manually if a new raw data drop
arrives, then commit the resulting CSV.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).parent.parent.parent / "raw-data" / "Raw-Data-Climate-TRACE"
OUT_PATH = Path(__file__).parent.parent / "data" / "SMAC_ch4_subsectors.csv"

FOLDER_TO_ISO = {
    "Argentina-ARG": "ARG", "Bolivia-BOL": "BOL", "Brazil-BRA": "BRA", "Canada-CAN": "CAN",
    "China-CHN": "CHN", "Germany-DEU": "DEU", "India-IND": "IND", "Indonesia-IDN": "IDN",
    "Italy-ITA": "ITA", "Mexico-MEX": "MEX", "Nigeria-NGA": "NGA", "South Africa-ZAF": "ZAF",
    "South Korea-KOR": "KOR", "Spain-ESP": "ESP", "United States-USA": "USA",
}

_NAME_SUFFIXES = [
    " Autonomous Community", " Union Territory", " Urban Area",
    " Province", " Municipality", " Department", " Region", " State",
]


def clean_location_name(raw: str) -> str:
    for suf in sorted(_NAME_SUFFIXES, key=len, reverse=True):
        if raw.endswith(suf):
            return raw[: -len(suf)]
    return raw


_DROP_RAW_NAMES = {"NCT of Delhi Union Territory", "Palembang Urban Area"}

# Maps each of Climate TRACE's 68 `original_inventory_sector` values to one of our
# 8 broad SECTOR_ORDER categories (see utils/data_loader.py).
SUBSECTOR_TO_BROAD = {
    # Agriculture
    "enteric-fermentation-cattle-operation": "Agriculture",
    "enteric-fermentation-cattle-pasture": "Agriculture",
    "enteric-fermentation-other": "Agriculture",
    "manure-applied-to-soils": "Agriculture",
    "manure-left-on-pasture-cattle": "Agriculture",
    "manure-management-cattle-operation": "Agriculture",
    "manure-management-other": "Agriculture",
    "rice-cultivation": "Agriculture",
    "synthetic-fertilizer-application": "Agriculture",
    "other-agricultural-soil-emissions": "Agriculture",
    "crop-residues": "Agriculture",
    "cropland-fires": "Agriculture",
    # Waste
    "solid-waste-disposal": "Waste",
    "biological-treatment-of-solid-waste-and-biogenic": "Waste",
    "incineration-and-open-burning-of-waste": "Waste",
    "domestic-wastewater-treatment-and-discharge": "Waste",
    "industrial-wastewater-treatment-and-discharge": "Waste",
    # Fossil Fuel Extraction & Mining
    "oil-and-gas-production": "Fossil Fuel Extraction & Mining",
    "oil-and-gas-refining": "Fossil Fuel Extraction & Mining",
    "oil-and-gas-transport": "Fossil Fuel Extraction & Mining",
    "coal-mining": "Fossil Fuel Extraction & Mining",
    "other-fossil-fuel-operations": "Fossil Fuel Extraction & Mining",
    "other-solid-fuels": "Fossil Fuel Extraction & Mining",
    "other-energy-use": "Fossil Fuel Extraction & Mining",
    "bauxite-mining": "Fossil Fuel Extraction & Mining",
    "copper-mining": "Fossil Fuel Extraction & Mining",
    "iron-mining": "Fossil Fuel Extraction & Mining",
    "rock-quarrying": "Fossil Fuel Extraction & Mining",
    "sand-quarrying": "Fossil Fuel Extraction & Mining",
    "other-mining-quarrying": "Fossil Fuel Extraction & Mining",
    # Forestry & Land Use
    "forest-land-clearing": "Forestry & Land Use",
    "forest-land-degradation": "Forestry & Land Use",
    "forest-land-fires": "Forestry & Land Use",
    "net-forest-land": "Forestry & Land Use",
    "net-shrubgrass": "Forestry & Land Use",
    "net-wetland": "Forestry & Land Use",
    "shrubgrass-fires": "Forestry & Land Use",
    "wetland-fires": "Forestry & Land Use",
    "removals": "Forestry & Land Use",
    # Manufacturing & Industry
    "aluminum": "Manufacturing & Industry",
    "cement": "Manufacturing & Industry",
    "chemicals": "Manufacturing & Industry",
    "other-chemicals": "Manufacturing & Industry",
    "petrochemical-steam-cracking": "Manufacturing & Industry",
    "food-beverage-tobacco": "Manufacturing & Industry",
    "glass": "Manufacturing & Industry",
    "iron-and-steel": "Manufacturing & Industry",
    "other-metals": "Manufacturing & Industry",
    "lime": "Manufacturing & Industry",
    "pulp-and-paper": "Manufacturing & Industry",
    "textiles-leather-apparel": "Manufacturing & Industry",
    "wood-and-wood-products": "Manufacturing & Industry",
    "other-manufacturing": "Manufacturing & Industry",
    "fluorinated-gases": "Manufacturing & Industry",
    # Power & Heat
    "electricity-generation": "Power & Heat",
    "heat-plants": "Power & Heat",
    "water-reservoirs": "Power & Heat",
    # Transportation
    "road-transportation": "Transportation",
    "railways": "Transportation",
    "domestic-aviation": "Transportation",
    "international-aviation": "Transportation",
    "domestic-shipping": "Transportation",
    "international-shipping": "Transportation",
    "non-broadcasting-vessels": "Transportation",
    "other-transport": "Transportation",
    # Buildings (Onsite Fuel Use)
    "residential-onsite-fuel-usage": "Buildings (Onsite Fuel Use)",
    "non-residential-onsite-fuel-usage": "Buildings (Onsite Fuel Use)",
    "other-onsite-fuel-usage": "Buildings (Onsite Fuel Use)",
}


def main():
    frames = []
    for folder, iso in FOLDER_TO_ISO.items():
        for path in (RAW_DIR / folder).glob("*.csv"):
            df = pd.read_csv(path)
            df = df[df["gas"] == "ch4"].copy()
            df["iso3"] = iso
            frames.append(df[["iso3", "name", "start_time", "original_inventory_sector", "total_emissions"]])

    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df[~all_df["name"].isin(_DROP_RAW_NAMES)].copy()
    all_df["location"] = all_df["name"].map(clean_location_name)
    all_df["date"] = pd.to_datetime(all_df["start_time"])
    all_df["year"] = all_df["date"].dt.year
    all_df["month"] = all_df["date"].dt.month
    all_df["sub_sector"] = all_df["original_inventory_sector"]
    all_df["sector"] = all_df["sub_sector"].map(SUBSECTOR_TO_BROAD)

    unmapped = all_df[all_df["sector"].isna()]["sub_sector"].unique()
    if len(unmapped):
        raise SystemExit(f"Unmapped sub-sectors, add to SUBSECTOR_TO_BROAD: {sorted(unmapped)}")

    out = (
        all_df.groupby(["iso3", "location", "year", "month", "sector", "sub_sector"], as_index=False)
        ["total_emissions"].sum()
        .rename(columns={"total_emissions": "total_emission", "iso3": "iso3_country"})
    )
    out.to_csv(OUT_PATH, index=False)
    print(f"wrote {len(out)} rows, {out.location.nunique()} locations -> {OUT_PATH}")


if __name__ == "__main__":
    main()
