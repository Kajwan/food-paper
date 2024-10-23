# %%
# Import packages
import pandas as pd
import numpy as np
import os
from pathlib import Path
import country_converter as coco
cc = coco.CountryConverter(include_obsolete=True)
from rpy2  import robjects

# %%
# Define variables
data_path = Path("../data")
years = np.arange(1986, 2022)

# %%
# Load fertiliser by crop data from Cameron et al. 
# Map to FABIO commodity
# Find weighted average fertiliser rate (kg fertiliser per ha) for each FABIO commodity
    # By the amount of land?
# Gap fill rates
    # Time series by interpolating and pad filling
    # Countries by UN region, continental, and world averages
# Calculate fertiliser use by FABIO process using land use from FABIO.
# Re-scale national fertiliser use by FAOSTAT national fertiliser use statistics

# %%
# Load in fertiliser use data
# Source: https://www.nature.com/articles/s41597-022-01592-z
Ludemann_df = (
    pd.read_csv(
        data_path / "raw" / "Ludemann et al. 2022" / "FUBC_1_to_9_data.csv",
        index_col=np.arange(0, 8)
    )
    .rename_axis(["variable"], axis=1)
    .rename_axis([
        "FUBC Country",
        "Country",
        "iso3c",
        "region",
        "year",
        "FUBC_report_number",
        "Year_FUBC_publication",
        "crop"
    ], axis=0)
    .droplevel([
        "region",
        "FUBC Country",
        "Country",
        "FUBC_report_number",
        "Year_FUBC_publication"
    ])
    .stack()
)

# %%
# Load landuse data from FABIO
readRDS = robjects.r['readRDS']
# Read RDS file
rds_file = readRDS(str(data_path / "raw" / "FABIO" / "E.rds"))

dfs = []
for year in years:
    # Extract year
    try:
        rds_file_year = rds_file[rds_file.names.index(f"{year}")]
    except ValueError:
        print("No data for year:", year)
        continue
    dfs_tmp = []
    for key in rds_file_year.names:
        if key in ["area"]:  # ! Encoding error when reading area
            continue
        df_tmp = pd.DataFrame.from_dict(
            {key: np.asarray(rds_file_year.rx2(key))}
        )
        dfs_tmp.append(df_tmp)
    df = pd.concat(dfs_tmp, axis=1)
    dfs.append(df)

FABIO_landuse = (
    pd.concat(dfs, axis=0, keys=years, names=["year"])
    .reset_index()
    .loc[:, ["year", "area_code", "item", "comm_group", "group", "landuse"]]
)


# %%
# Load fertiliser use per country from FAOSTAT
# Source: https://www.fao.org/faostat/en/#data/RFN
FAO_fertiliser = (
    pd.read_csv(
        data_path / "raw" / "FAOSTAT" / "inputs" / "fertilizer" / "Inputs_FertilizersNutrient_E_All_Data_NOFLAG.csv",
        encoding="cp1252",
        index_col=np.arange(0, 8)
    )
    .rename(lambda x: int(x.split("Y")[1]), axis=1)
    .rename_axis(["year"], axis=1)
    .droplevel(["Area Code (M49)", "Area", "Item Code", "Element Code"])
    .rename_axis([
        "area_code",
        "fertiliser", 
        "element",
        "unit"
    ])
    .rename({
        "Nutrient nitrogen N (total)": "N",
        "Nutrient phosphate P2O5 (total)": "P2O5",
        "Nutrient potash K2O (total)": "K2O"
    })
    .drop([
        "Production",
        "Import Quantity",
        "Export Quantity",
        "Use per area of cropland",
        "Use per capita",
        "Use per value of agricultural production"
    ], level="element")
    .stack()
    .to_frame("fertiliser_use_total")
    .reset_index()
)

# This gap fill intermediate years, assuming linear relation.
# It fills up 8746 of 10722 missing values (~82 %)
FAO_fertiliser_imputed = (
    FAO_fertiliser
    .pivot(
        index=["area_code", "fertiliser", "element", "unit"],
        columns="year",
        values="fertiliser_use_total"
    )
    .interpolate(
        axis=1,
        method="linear"
    )
)

# %%
# Load in various mappings.
# Maps the products in Ludemann et al. to FABIO
Ludemann_to_FABIO_mapping = (
    pd.read_excel(
        data_path / "auxiliary" / "concordances" / "Ludemann et al. - FABIO mapping.xlsx",
        index_col=[0]
    ).set_index(["Crop"])["FABIO"]
    .to_dict()
)

# List of all FABIO regions.
FABIO_regions = (
    pd.read_csv(
        data_path / "auxiliary" / "classifications" / "regions_fabio.csv",
        encoding="cp1252"
    )
)

# %%
# Make a mapper to UN subregions for countries in FABIO but not in country converter.
UNregion_mapper = cc.data.loc[:, ["FAOcode", "UNregion"]].dropna()
UNregion_mapper["FAOcode"] = UNregion_mapper["FAOcode"].astype("int")
UNregion_mapper = UNregion_mapper.set_index("FAOcode")["UNregion"].to_dict()
UNregion_mapper.update({
    15: "Western Europe",
    41: "Eastern Asia",
    51: "Eastern Europe",
    151: "Caribbean",
    186: "Southern Europe",
    228: "Eastern Europe",
    248: "Southern Europe",
    276: "Eastern Africa",
    999: "RoW"
})
# %%
# Start from the Ludemann et al. dataset
# Add a column where product names are mapped to FABIO.
t1 = (
    Ludemann_df
    .to_frame("values")
    .reset_index()
)
t1["FABIO_commodities"] = t1.crop.map(Ludemann_to_FABIO_mapping)

# Pivot the data with years as columns.
t1 = (
    t1
    .pivot_table(
        index=[
            "iso3c",
            "FABIO_commodities",
            "crop",
            "variable"
        ],
        columns=[
            "year"
        ],
        values="values"
    )
)
# Get a list of missing years
missing_years = list(set(years.astype(str))-set(t1.columns.values))

# Create empty columns for all missing years.
t1[missing_years] = np.nan


# %%
# Gap fill along the years
# Linear interpolation inbetween existing data points.
# Constant fill at the edges.
# Turn back into long format.
t2 = (
    t1
    .loc[:, ~t1.columns.str.contains("/|-")]
    .rename(lambda x: int(x), axis=1)
    .sort_index(axis=1)
    .interpolate(method="linear", axis=1)
    .bfill(axis=1)
    .ffill(axis=1)
    .stack()
)


# %%
# Merge with iso3c and continent columns in the FABIO regions dataset 
t3 = (
    t2.to_frame("values").reset_index()
    .merge(
        FABIO_regions.drop(["area_code", "area"], axis=1),
        on="iso3c",
        how="right"
    )
)

# %%
# Pivot along the variables columns
t4 = (
    t3
    .pivot_table(
        index=[
            "continent",
            "iso3c",
            "FABIO_commodities",
            "crop",
            "year"
        ],
        columns=[
            "variable"
        ],
        values="values"
    )
)

# %%
# Get the aggregate crop area per FABIO commodity (as opposed to Cameron et al. "crop").
t4["Crop_area_k_ha_agg"] = (
    t4
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            #"crop",
            "year"
        ]
    )["Crop_area_k_ha"].transform(sum)
)

# %%
# Calculate the crop area share per FABIO commodity.
t4["Crop_area_k_ha_share"] = (
    t4["Crop_area_k_ha"]
    .div(t4["Crop_area_k_ha_agg"])
    .replace([np.inf, np.nan, -np.inf], 0)
)


# %%
# Calculate fertiliser rates (kg/ha) using the 
# Mean application rate of fertilizer across total crop area,
# and the per FABIO commodity crop area share.
FABIO_aver_K2O_rate = (
    t4["Aver_K2O_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)

FABIO_aver_N_rate = (
    t4["Aver_N_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)

FABIO_aver_P2O5_rate = (
    t4["Aver_P2O5_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)

# %%
# Calculate fertiliser rates (kg/ha) using the 
# Mean application rate of fertilizer to area of crop that actually received fertilizer,
# and the per FABIO commodity crop area share.
FABIO_K2O_rate = (
    t4["K2O_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)

FABIO_N_rate = (
    t4["N_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)

FABIO_P2O5_rate = (
    t4["P2O5_rate_kg_ha"]
    .mul(t4["Crop_area_k_ha_share"])
    .groupby(
        [
            "continent",
            "iso3c",
            "FABIO_commodities",
            "year"
        ]
    ).sum()
)


# %%
# Gap fill the former with the latter.
FABIO_aver_K2O_rate_filled = (
    FABIO_aver_K2O_rate
    .replace(0, np.nan)
    .combine_first(FABIO_K2O_rate)
)

FABIO_aver_N_rate_filled = (
    FABIO_aver_N_rate
    .replace(0, np.nan)
    .combine_first(FABIO_N_rate)
)

FABIO_aver_P2O5_rate_filled = (
    FABIO_aver_P2O5_rate
    .replace(0, np.nan)
    .combine_first(FABIO_P2O5_rate)
)

# %%
# Combine the data
fertiliser_rates = pd.concat(
    [FABIO_K2O_rate, FABIO_N_rate, FABIO_P2O5_rate],
    keys=["K2O", "N", "P2O5"],
    names=["fertiliser"],
    axis=1
)

# %%
# Get area codes from FABIO_regions.
t5 = (
    FABIO_regions
    .drop(["area"], axis=1)
    .merge(
        (    
            fertiliser_rates
            .stack()
            .to_frame("rates")
            .reset_index()
        ),
        how="left",
        on=["continent", "iso3c"]
    )
)
# Map to UN subregion.
t5["UNregion"] = t5["area_code"].map(UNregion_mapper)


# %%
# Pivot the table and replace zero with nan values for gap filling.
t6 = (
    t5
    .pivot(
        index=["year", "FABIO_commodities", "fertiliser"],
        columns=["continent", "UNregion", "area_code", "iso3c"],
        values="rates"
    )
    .replace(0, np.nan)
)

# %%
# Get UN subregion means.
UNregion_means = (
    t6
    .groupby("UNregion", axis=1)
    .transform(np.mean)
)

# %%
# Get continent means.
continent_means = (
    t6
    .groupby("continent", axis=1)
    .transform(np.mean)
)

# %%
# Get global means.
global_means = (
    pd.concat(
        [t6.mean(axis=1)]*len(t6.columns), 
        keys=t6.columns,
        axis=1
    )
)

# %%
# Gap fill the fertilizer rates with UN subregions, continent, and global means in that order if available.
t7 = (
    t6
    .combine_first(UNregion_means)
    .combine_first(continent_means)
    .combine_first(global_means)
    .unstack("year")
    .dropna(how="all", axis=0)
    .dropna(how="all", axis=1)
    .droplevel("continent", axis=1)
    .unstack(["FABIO_commodities", "fertiliser"])
    .unstack("year")
)

# %%
# Gap fill missing years as before.
missing_years = list(set(years.astype(float))-set(t7.columns.values))
t7[missing_years] = np.nan

t8 = (
    t7
    .rename(lambda x: int(x), axis=1)
    .sort_index(axis=1)
    .interpolate(method="linear", axis=1)
    .bfill(axis=1)
    .ffill(axis=1)
)

# %%
# Restructure the series.
t9 = (
    t8
    .stack()
    .to_frame("rate")
    .reset_index()
) 
t9["year"] = t9["year"].astype(int)

# Merge with FABIO landuse data
t10 = (
    t9[t9["year"] >= 1986]
    .rename({"FABIO_commodities": "item"}, axis=1)
    .merge(
        FABIO_landuse,
        how="left",
        on=["year", "area_code", "item"]
    )
)

# %%
# Calculate fertiliser use
t10["fertiliser_use"] = (
    t10["rate"]
    .mul(t10["landuse"])
)


# %%
# Calculate total fertiliser use share per FABIO region, fertiliser, and year.
t10["fertiliser_use_share"] = (
    t10["fertiliser_use"]
    .div(
        t10
        .groupby(["area_code", "fertiliser", "year"])["fertiliser_use"]
        .transform("sum")
    )
    .replace([np.nan, np.inf, -np.inf], 0)
)

# %%
FAO_fertiliser.loc[
    (FAO_fertiliser.area_code == 195)
    & (FAO_fertiliser.year == 2015)
    #& (FAO_fertiliser.item == "Sugar cane")
    , :
]

# %%
# Combine with FAO fertiliser statistics
t11 = (
    t10
    .merge(
        FAO_fertiliser.drop(["element", "unit"], axis=1),
        how="left",
        on=["area_code", "fertiliser", "year"]
    )
)

# %%
# Use the shares to rescale to FAO fertiliser statistics
t11["fertiliser_use_corrected"] = (
    t11["fertiliser_use_share"]
    .mul(t11["fertiliser_use_total"])
)


# %%
# Remove zeros and missing values
t12 = t11[(~t11["fertiliser_use_corrected"].isna()) & (t11["fertiliser_use_corrected"] != 0)]

# %%
save_path = (
    data_path
    / "results"
    / "fertiliser"
    / "use"
)
os.makedirs(save_path, exist_ok=True)
# %%
t12.to_csv(
    save_path / "fertiliser_use_reduced.csv",
    sep="\t"
)

# %%
t11.to_csv(
    save_path / "fertiliser_use_full.csv",
    sep="\t"
)
