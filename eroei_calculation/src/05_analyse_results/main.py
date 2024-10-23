# -*- coding: utf-8 -*-
# %%
# %% [markdown]
# Copyright (C) 2024 Kajwan Rasul
# 
#
# Written by
#
# - Kajwan Rasul
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# %%
import os
import docx
import pandas as pd
import numpy as np
import fabio_functions
from pathlib import Path
import country_converter as coco
from tqdm import tqdm
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
# %%
from rpy2 import robjects

cm = sns.light_palette("green", as_cmap=True)
cc = coco.CountryConverter(include_obsolete=True)
years = np.arange(1995, 2021)

# %%
pd.set_option('display.float_format', lambda x: '%.3e' % x)

# %%
final_demand_categories = [
    "balancing",
    "food",
    "losses",
    "other",
    "stock_addition",
    "tourist",
    "unspecified"
]

final_demand_categories_cal = [
    "balancing",
    "food",
    #"losses",
    #"other",
    "stock_addition",
    "tourist",
    "unspecified"
]

# %%
data_path = Path("../../data")
fabio_path = (
    data_path
    / "raw"
    / "FABIO"
    / "biomass"
)

fabio_calories_path = (
    data_path
    / "raw"
    / "FABIO"
    / "calories"
)

results_path = (
    data_path
    / "results"
)

sna_mainagg_path = (
    data_path
    / "raw"
    / "UN SNA"
)

# %%
nutrient_coefficients_path = (
    data_path
    / "auxiliary"
)

# %%
nutrient_coefficients = (
    pd.read_csv(
        nutrient_coefficients_path / "nutrient_coefficients.csv"
    )
    .set_index(["item"])
    .loc[:, "kcal_per_kg"]
    .rename_axis(["item_output"])
)

# %%
reader = fabio_functions.read(
    fabio_path,
    year=2005,
    version=1.2
)
regions = reader.regions.copy()
regions.loc[regions.iso3c == "CIV", "area"] = "Côte d'Ivoire"

regions = regions.rename({"iso3c": "area_ISO3"}, axis=1)

regions["UNregions"] = regions["area_ISO3"].apply(lambda x: cc.convert(x, src="ISO3", to="UNregion", not_found=None))
regions["region"] = regions["area_ISO3"].apply(lambda x: cc.convert(x, src="ISO3", to="EXIO3", not_found=None))

regions.loc[regions["area"] == "Belgium-Luxembourg", ["UNregions", "region"]] = ["Western Europe", "BE"]
regions.loc[regions["area"] == "Czechoslovakia", ["UNregions", "region"]] = ["Southern Europe", "HR"]
regions.loc[regions["area"] == "Yugoslav SFR", ["UNregions", "region"]] = ["Southern Europe", "HR"]
regions.loc[regions["area"] == "Serbia and Montenegro", ["UNregions", "region"]] = ["Southern Europe", "WE"]
regions.loc[regions["area"] == "RoW", ["UNregions", "region"]] = ["ROW", "WA"]
regions.loc[regions["area"] == "Netherlands Antilles", ["UNregions", "region"]] = ["Western Europe", "NL"]
regions.loc[regions.UNregions.isin(["Polynesia", "Micronesia", "Melanesia", "ROW"]), "UNregions"] = "ROW"
code_to_area_mapper = regions.set_index(["area_code"])["area"].to_dict()
UN_regions_mapper = regions.groupby("UNregions")["area_ISO3"].agg(list).to_dict()
UN_regions_area_mapper = regions.groupby("UNregions")["area"].agg(list).to_dict()
EXIOBASE_region_mapper = regions.set_index(["area"])["region"].to_dict()
area_to_UN = (
    regions
    .set_index("area")
    ["UNregions"]
    .to_dict()
)
iso3_mapper = regions.set_index(["area_ISO3"])["area"].to_dict()

# %%
area_to_agg = {
    'Armenia': 'Armenia',
    'Afghanistan': 'Other Southern Asia',
    'Albania': 'Albania',
    'Algeria': 'Other Northern Africa',
    'Angola': 'Other Middle Africa',
    'Antigua and Barbuda': 'Other Caribbean',
    'Argentina': 'Argentina',
    'Australia': 'Australia',
    'Austria': 'Austria',
    'Bahamas': 'Other Caribbean',
    'Bahrain': 'Other Middle East',
    'Barbados': 'Other Caribbean',
    'Belgium-Luxembourg': 'Belgium',
    'Bangladesh': 'Bangladesh',
    'Bolivia (Plurinational State of)': 'Other South America',
    'Botswana': 'Other Southern Africa',
    'Brazil': 'Brazil',
    'Belize': 'Other Central America',
    'Solomon Islands': 'ROW',
    'Brunei Darussalam': 'Other South-eastern Asia',
    'Bulgaria': 'Bulgaria',
    'Myanmar': 'Other South-eastern Asia',
    'Burundi': 'Other Eastern Africa',
    'Cameroon': 'Other Middle Africa',
    'Canada': 'Canada',
    'Cabo Verde': 'Other Western Africa',
    'Central African Republic': 'Central African Republic',
    'Sri Lanka': 'Sri Lanka',
    'Chad': 'Other Middle Africa',
    'Chile': 'Other South America',
    'China, mainland': 'China',
    'Colombia': 'Colombia',
    'Congo': 'Other Middle Africa',
    'Costa Rica': 'Other Central America',
    'Cuba': 'Cuba',
    'Cyprus': 'Cyprus',
    'Czechoslovakia': 'Czechoslovakia',
    'Azerbaijan': 'Other Western Asia',
    'Benin': 'Other Western Africa',
    'Denmark': 'Denmark',
    'Dominica': 'Other Caribbean',
    'Dominican Republic': 'Other Caribbean',
    'Belarus': 'Belarus',
    'Ecuador': 'Other South America',
    'Egypt': 'Egypt',
    'El Salvador': 'Other Central America',
    'Estonia': 'Estonia',
    'Fiji': 'ROW',
    'Finland': 'Finland',
    'France': 'France',
    'French Polynesia': 'ROW',
    'Djibouti': 'Other Eastern Africa',
    'Georgia': 'Other Western Asia',
    'Gabon': 'Other Middle Africa',
    'Gambia': 'Other Western Africa',
    'Germany': 'Germany',
    'Bosnia and Herzegovina': 'Bosnia and Herzegovina',
    'Ghana': 'Other Western Africa',
    'Kiribati': 'ROW',
    'Greece': 'Greece',
    'Grenada': 'Other Caribbean',
    'Guatemala': 'Guatemala',
    'Guinea': 'Other Western Africa',
    'Guyana': 'Other South America',
    'Haiti': 'Other Caribbean',
    'Honduras': 'Other Central America',
    'China, Hong Kong SAR': 'China',
    'Hungary': 'Hungary',
    'Croatia': 'Croatia',
    'Iceland': 'Iceland',
    'India': 'India',
    'Indonesia': 'Indonesia',
    'Iran (Islamic Republic of)': 'Iran (Islamic Republic of)',
    'Iraq': 'Iraq',
    'Ireland': 'Ireland',
    'Israel': 'Israel',
    'Italy': 'Italy',
    "Côte d'Ivoire": "Côte d'Ivoire",
    'Kazakhstan': 'Other Central Asia',
    'Jamaica': 'Jamaica',
    'Japan': 'Japan',
    'Jordan': 'Other Middle East',
    'Kyrgyzstan': 'Other Central Asia',
    'Kenya': 'Other Eastern Africa',
    'Cambodia': 'Other South-eastern Asia',
    "Democratic People's Republic of Korea": "Other Eastern Asia",
    'Republic of Korea': 'Republic of Korea',
    'Kuwait': 'Other Middle East',
    'Latvia': 'Latvia',
    "Lao People's Democratic Republic": 'Other South-eastern Asia',
    'Lebanon': 'Other Middle East',
    'Lesotho': 'Other Southern Africa',
    'Liberia': 'Other Western Africa',
    'Libya': 'Other Northern Africa',
    'Lithuania': 'Lithuania',
    'China, Macao SAR': 'China',
    'Madagascar': 'Other Eastern Africa',
    'Malawi': 'Other Eastern Africa',
    'Malaysia': 'Malaysia',
    'Maldives': 'Other Southern Asia',
    'Mali': 'Other Western Africa',
    'Malta': 'Malta',
    'Mauritania': 'Other Western Africa',
    'Mauritius': 'Other Eastern Africa',
    'Mexico': 'Mexico',
    'Mongolia': 'Other Eastern Asia',
    'Morocco': 'Morocco',
    'Mozambique': 'Other Eastern Africa',
    'Republic of Moldova': 'Other Eastern Europe',
    'Namibia': 'Other Southern Africa',
    'Nepal': 'Other Southern Asia',
    'Netherlands': 'Netherlands',
    'Netherlands Antilles': 'ROW',
    'New Caledonia': 'ROW',
    'North Macedonia': 'Other Southern Europe',
    'Vanuatu': 'ROW',
    'New Zealand': 'New Zealand',
    'Nicaragua': 'Other Central America',
    'Niger': 'Other Western Africa',
    'Nigeria': 'Other Western Africa',
    'Norway': 'Norway',
    'Pakistan': 'Pakistan',
    'Panama': 'Other Central America',
    'Czech Republic': 'Czech Republic',
    'Papua New Guinea': 'ROW',
    'Paraguay': 'Other South America',
    'Peru': 'Other South America',
    'Philippines': 'Philippines',
    'Poland': 'Poland',
    'Portugal': 'Portugal',
    'Guinea-Bissau': 'Other Western Africa',
    'Timor-Leste': 'Other South-eastern Asia',
    'Puerto Rico': 'Puerto Rico',
    'Eritrea': 'Other Eastern Africa',
    'Qatar': 'Other Middle East',
    'Zimbabwe': 'Other Eastern Africa',
    'Romania': 'Romania',
    'Rwanda': 'Other Eastern Africa',
    'Russian Federation': 'Russian Federation',
    'Serbia and Montenegro': 'Other Southern Europe',
    'Saint Kitts and Nevis': 'Other Caribbean',
    'Saint Lucia': 'Other Caribbean',
    'Saint Vincent and the Grenadines': 'Other Caribbean',
    'Sao Tome and Principe': 'Other Middle Africa',
    'Saudi Arabia': 'Saudi Arabia',
    'Senegal': 'Other Western Africa',
    'Sierra Leone': 'Other Western Africa',
    'Slovenia': 'Slovenia',
    'Slovakia': 'Slovakia',
    'Singapore': 'Other South-eastern Asia',
    'Somalia': 'Other Eastern Africa',
    'South Africa': 'South Africa',
    'Spain': 'Spain',
    'Suriname': 'Other South America',
    'Tajikistan': 'Other Central Asia',
    'Eswatini': 'Other Southern Africa',
    'Sweden': 'Sweden',
    'Switzerland': 'Switzerland',
    'Syrian Arab Republic': 'Other Middle East',
    'Turkmenistan': 'Other Central Asia',
    'China, Taiwan Province of': 'Taiwan',
    'United Republic of Tanzania': 'Other Eastern Africa',
    'Thailand': 'Thailand',
    'Togo': 'Other Western Africa',
    'Trinidad and Tobago': 'Other Caribbean',
    'Oman': 'Other Middle East',
    'Tunisia': 'Other Northern Africa',
    'Turkey': 'Turkey',
    'United Arab Emirates': 'Other Middle East',
    'Uganda': 'Other Eastern Africa',
    'USSR': 'USSR',
    'United Kingdom': 'United Kingdom',
    'Ukraine': 'Ukraine',
    'United States of America': 'United States of America',
    'Burkina Faso': 'Other Western Africa',
    'Uruguay': 'Other South America',
    'Uzbekistan': 'Other Central Asia',
    'Venezuela (Bolivarian Republic of)': 'Other South America',
    'Viet Nam': 'Viet Nam',
    'Ethiopia': 'Other Eastern Africa',
    'Samoa': 'ROW',
    'Yugoslav SFR': 'Other Southern Europe',
    'Yemen': 'Other Middle East',
    'Democratic Republic of the Congo': 'Other Middle Africa',
    'Zambia': 'Other Eastern Africa',
    'Belgium': 'Belgium',
    'Luxembourg': 'Luxembourg',
    'Serbia': 'Serbia',
    'Montenegro': 'Other Southern Europe',
    'Sudan': 'Other Northern Africa',
    'South Sudan': 'Other Eastern Africa',
    'RoW': 'ROW'
}

# %%
IEA_product_grouping = {
    'Additives/blending components': "Non-renewable",
    'Anthracite': "Non-renewable",
    'Aviation gasoline': "Non-renewable",
    'BKB': "Non-renewable",
    'Biodiesels': "Bio",
    'Biogases': "Bio",
    'Biogasoline': "Bio",
    'Bitumen': "Non-renewable",
    'Blast furnace gas': "Non-renewable",
    'Charcoal': "Non-renewable",
    'Coal tar': "Non-renewable",
    'Coke oven coke': "Non-renewable",
    'Coke oven gas': "Non-renewable",
    'Coking coal': "Non-renewable",
    'Crude oil': "Non-renewable",
    'Ethane': "Non-renewable",
    'Fuel oil': "Non-renewable",
    'Gas coke': "Non-renewable",
    'Gas works gas': "Non-renewable",
    'Gas/diesel oil excl. biofuels': "Non-renewable",
    'Gasoline type jet fuel': "Non-renewable",
    'Geothermal': "Renewable",
    'Hydro': "Renewable",
    'Industrial waste': "Non-renewable",
    'K2O': "Fertiliser",
    'Kerosene type jet fuel excl. biofuels': "Non-renewable",
    'Lignite': "Non-renewable",
    'Liquefied petroleum gases (LPG)': "Non-renewable",
    'Lubricants': "Non-renewable",
    'Motor gasoline excl. biofuels': "Non-renewable",
    'Municipal waste (non-renewable)': "Non-renewable",
    'Municipal waste (renewable)': "Renewable",
    'N': "Fertiliser",
    'Naphtha': "Non-renewable",
    'Natural gas': "Non-renewable",
    'Natural gas liquids': "Non-renewable",
    'Nuclear': "Renewable",
    'Oil shale and oil sands': "Non-renewable",
    'Other bituminous coal': "Non-renewable",
    'Other hydrocarbons': "Non-renewable",
    'Other kerosene': "Non-renewable",
    'Other liquid biofuels': "Bio",
    'Other oil products': "Non-renewable",
    'Other recovered gases': "Non-renewable",
    'Other sources': "Non-renewable",
    'P2O5': "Fertiliser",
    'Paraffin waxes': "Non-renewable",
    'Patent fuel': "Non-renewable",
    'Peat': "Non-renewable",
    'Peat products': "Non-renewable",
    'Petroleum coke': "Non-renewable",
    'Primary solid biofuels': "Bio",
    'Refinery gas': "Non-renewable",
    'Solar photovoltaics': "Renewable",
    'Solar thermal': "Renewable",
    'Sub-bituminous coal': "Non-renewable",
    'Tide, wave and ocean': "Renewable",
    'White spirit & SBP': "Non-renewable",
    'Wind': "Renewable"
}

# %%
five_year_agg = {
    1995: '1995-1999',
    1996: '1995-1999',
    1997: '1995-1999',
    1998: '1995-1999',
    1999: '1995-1999',
    2000: np.nan,
    2001: np.nan,
    2002: np.nan,
    2003: np.nan,
    2004: np.nan,
    2005: np.nan,
    2006: np.nan,
    2007: np.nan,
    2008: np.nan,
    2009: np.nan,
    2010: np.nan,
    2011: np.nan,
    2012: np.nan,
    2013: np.nan,
    2014: np.nan,
    2015: '2015-2019',
    2016: '2015-2019',
    2017: '2015-2019',
    2018: '2015-2019',
    2019: '2015-2019',
}
# %%
faostat_path = (
    data_path
    / "raw"
    / "FAOSTAT"
)

# %%
# Old
pop_df = (
    pd.read_excel(
        sna_mainagg_path / "Download-Xpop.xlsx", 
        sheet_name="Download-XPop", 
        index_col=[0, 1, 2, 3]
    ).rename_axis(["Year"], axis=1)
)
pop_df = (
    pop_df
    .loc[
        pop_df.index.isin(["Population"], level="Measure"),
        pop_df.columns.isin(years, level="Year")
    ]
    .droplevel(["CountryID", "Currency", "Measure"])
    .rename_axis(["Area"], axis=0)
    .stack()
)

un_pop_df = pop_df.copy().rename({"D.R. of the Congo": "Democratic Republic of the Congo"})
un_pop_df.index = un_pop_df.index.map(lambda x: (cc.convert(x[0], to="UNregion"), x[1]))

un_pop_df = (
    un_pop_df
    .rename(area_to_UN, level="Area")
    .groupby(["Area", "Year"]).sum()
)

global_pop_df = (
    un_pop_df
    .groupby(["Year"]).sum()
)

# %%
def domestic_split(df):
    regions = df.columns.get_level_values("area").unique()
    dfs = []
    for region in tqdm(regions):
        df_dom = pd.concat(
            [
                pd.concat(
                    [df.loc[region, region]],
                    keys=[region], names=["area"], axis=1
                )
            ], keys=["Domestic"], names=["area_output"]
        )

        df_non_dom = (
            df
            .loc[
                ~df.index.isin([region], level="area_output"),
                region
            ].groupby(["item_output", "comm_group_output", "group_output"])
            .sum()
        )
        df_non_dom = pd.concat(
            [
                pd.concat(
                    [df_non_dom],
                    keys=[region], names=["area"], axis=1
                )
            ], keys=["Non-domestic"], names=["area_output"]
        )

        df_region = pd.concat([
            df_dom,
            df_non_dom
        ])
        dfs.append(df_region)
    df_domestic_split = (
        pd.concat(
            dfs, axis=1
        )
    )
    return df_domestic_split

# %%
def number_to_text(x):
    if x > 1000:
        return f"{x:.2e}"
    else:
        return f"{x:.2f}"


# %%
product_groups = {
    'Rice and products': 'Cereals',
    'Wheat and products': 'Cereals',
    'Barley and products': 'Cereals',
    'Maize and products': 'Cereals',
    'Rye and products': 'Cereals',
    'Oats': 'Cereals',
    'Millet and products': 'Cereals',
    'Sorghum and products': 'Cereals',
    'Cereals, Other': 'Cereals',
    'Potatoes and products': 'Roots, tubers & nuts',
    'Cassava and products': 'Roots, tubers & nuts',
    'Sweet potatoes': 'Roots, tubers & nuts',
    'Roots, Other': 'Roots, tubers & nuts',
    'Yams': 'Roots, tubers & nuts',
    'Sugar cane': 'Sugars & similar',
    'Sugar beet': 'Sugars & similar',
    'Beans': 'Pulses & other',
    'Peas': 'Pulses & other',
    'Pulses, Other and products': 'Pulses & other',
    'Nuts and products': 'Roots, tubers & nuts',
    'Soyabeans': 'Oil crops, veg. oils & cakes',
    'Groundnuts': 'Oil crops, veg. oils & cakes',
    'Sunflower seed': 'Oil crops, veg. oils & cakes',
    'Rape and Mustardseed': 'Oil crops, veg. oils & cakes',
    'Seed cotton': 'Oil crops, veg. oils & cakes',
    'Coconuts - Incl Copra': 'Oil crops, veg. oils & cakes',
    'Sesame seed': 'Oil crops, veg. oils & cakes',
    'Oil, palm fruit': 'Oil crops, veg. oils & cakes',
    'Olives (including preserved)': 'Oil crops, veg. oils & cakes',
    'Oilcrops, Other': 'Oil crops, veg. oils & cakes',
    'Tomatoes and products': 'Vegetables & fruits',
    'Onions': 'Vegetables & fruits',
    'Vegetables, Other': 'Vegetables & fruits',
    'Oranges, Mandarines': 'Vegetables & fruits',
    'Lemons, Limes and products': 'Vegetables & fruits',
    'Grapefruit and products': 'Vegetables & fruits',
    'Citrus, Other': 'Vegetables & fruits',
    'Bananas': 'Vegetables & fruits',
    'Plantains': 'Vegetables & fruits',
    'Apples and products': 'Vegetables & fruits',
    'Pineapples and products': 'Vegetables & fruits',
    'Dates': 'Vegetables & fruits',
    'Grapes and products (excl wine)': 'Vegetables & fruits',
    'Fruits, Other': 'Vegetables & fruits',
    'Coffee and products': 'Coffee, tea & cocoa',
    'Cocoa Beans and products': 'Coffee, tea & cocoa',
    'Tea (including mate)': 'Coffee, tea & cocoa',
    'Hops': 'Pulses & other',
    'Pepper': 'Pulses & other',
    'Pimento': 'Pulses & other',
    'Cloves': 'Pulses & other',
    'Spices, Other': 'Pulses & other',
    'Jute': 'Fibre crops',
    'Jute-Like Fibres': 'Fibre crops',
    'Soft-Fibres, Other': 'Fibre crops',
    'Sisal': 'Fibre crops',
    'Abaca': 'Fibre crops',
    'Hard Fibres, Other': 'Fibre crops',
    'Tobacco': 'Tobacco, rubber',
    'Rubber': 'Tobacco, rubber',
    'Fodder crops': 'Fodder crops',
    'Grazing': 'Grazing',
    'Cottonseed': 'Fibre crops',
    'Palm kernels': 'Oil crops, veg. oils & cakes',
    'Sugar non-centrifugal': 'Sugars & similar',
    'Sugar (Raw Equivalent)': 'Sugars & similar',
    'Sweeteners, Other': 'Sugars & similar',
    'Soyabean Oil': 'Oil crops, veg. oils & cakes',
    'Groundnut Oil': 'Oil crops, veg. oils & cakes',
    'Sunflowerseed Oil': 'Oil crops, veg. oils & cakes',
    'Rape and Mustard Oil': 'Oil crops, veg. oils & cakes',
    'Cottonseed Oil': 'Oil crops, veg. oils & cakes',
    'Palmkernel Oil': 'Oil crops, veg. oils & cakes',
    'Palm Oil': 'Oil crops, veg. oils & cakes',
    'Coconut Oil': 'Oil crops, veg. oils & cakes',
    'Sesameseed Oil': 'Oil crops, veg. oils & cakes',
    'Olive Oil': 'Oil crops, veg. oils & cakes',
    'Ricebran Oil': 'Oil crops, veg. oils & cakes',
    'Maize Germ Oil': 'Oil crops, veg. oils & cakes',
    'Oilcrops Oil, Other': 'Oil crops, veg. oils & cakes',
    'Soyabean Cake': 'Oil crops, veg. oils & cakes',
    'Groundnut Cake': 'Oil crops, veg. oils & cakes',
    'Sunflowerseed Cake': 'Oil crops, veg. oils & cakes',
    'Rape and Mustard Cake': 'Oil crops, veg. oils & cakes',
    'Cottonseed Cake': 'Oil crops, veg. oils & cakes',
    'Palmkernel Cake': 'Oil crops, veg. oils & cakes',
    'Copra Cake': 'Oil crops, veg. oils & cakes',
    'Sesameseed Cake': 'Oil crops, veg. oils & cakes',
    'Oilseed Cakes, Other': 'Oil crops, veg. oils & cakes',
    'Wine': 'Alcohol',
    'Beer': 'Alcohol',
    'Beverages, Fermented': 'Alcohol',
    'Beverages, Alcoholic': 'Alcohol',
    'Alcohol, Non-Food': 'Ethanol',
    'Cotton lint': 'Fibre crops',
    'Cattle': 'Live animals',
    'Buffaloes': 'Live animals',
    'Sheep': 'Live animals',
    'Goats': 'Live animals',
    'Pigs': 'Live animals',
    'Poultry Birds': 'Live animals',
    'Horses': 'Live animals',
    'Asses': 'Live animals',
    'Mules': 'Live animals',
    'Camels': 'Live animals',
    'Camelids, other': 'Live animals',
    'Rabbits and hares': 'Live animals',
    'Rodents, other': 'Live animals',
    'Milk - Excluding Butter': 'Eggs, milk & milk products',
    'Butter, Ghee': 'Eggs, milk & milk products',
    'Eggs': 'Eggs, milk & milk products',
    'Wool (Clean Eq.)': 'Hides, skins, wool',
    'Bovine Meat': 'Meat, fish & animal fats',
    'Mutton & Goat Meat': 'Meat, fish & animal fats',
    'Pigmeat': 'Meat, fish & animal fats',
    'Poultry Meat': 'Meat, fish & animal fats',
    'Meat, Other': 'Meat, fish & animal fats',
    'Offals, Edible': 'Meat, fish & animal fats',
    'Fats, Animals, Raw': 'Meat, fish & animal fats',
    'Hides and skins': 'Hides, skins, wool',
    'Honey': 'Sugars & similar',
    'Silk': 'Hides, skins, wool',
    'Fish, Seafood': 'Meat, fish & animal fats'
}


# %%
reader_cal = fabio_functions.read(
    fabio_calories_path,
    year=2020,
    version=1.2
)

Y_cal = reader_cal.Y()

# %%
reader = fabio_functions.read(
    fabio_path,
    year=2020,
    version=1.2
)

Y = reader.Y()

# %%
exclude_negatives = True

# %%
Y_cal_list = []
for year in tqdm(years):
    # Calorie data
    reader_cal = fabio_functions.read(
        fabio_calories_path,
        year=year,
        version=1.2
    )

    Y_cal = reader_cal.Y()
    y_regions_cal = (
        Y_cal
        .loc[
            :,
            Y_cal.columns.isin(final_demand_categories_cal, level="final demand")
        ]
        .groupby(["iso3c"], axis=1).sum()
        .droplevel(["area_code", "item_code", "comm_code"])
    ) * 4.1858e-6  # TJ / Mcal

    if exclude_negatives:
        y_regions_cal[y_regions_cal < 0] = 0
    Y_cal_list.append(y_regions_cal)

# %%
Y_cal = pd.concat(Y_cal_list, keys=years, names=["year"], axis=0).rename(iso3_mapper, level="iso3c", axis=1)

# %%
Y_cal_losses_list = []
for year in tqdm(years):
    # Calorie data
    reader_cal = fabio_functions.read(
        fabio_calories_path,
        year=year,
        version=1.2
    )

    Y_cal = reader_cal.Y()
    y_regions_cal = (
        Y_cal
        .loc[
            :,
            Y_cal.columns.isin(["losses"], level="final demand")
        ]
        .groupby(["iso3c"], axis=1).sum()
        .droplevel(["area_code", "item_code", "comm_code"])
    ) * 4.1858e-6  # TJ / Mcal
    Y_cal_losses_list.append(y_regions_cal)

# %%
Y_cal_losses = pd.concat(Y_cal_losses_list, keys=years, names=["year"], axis=0).rename(iso3_mapper, level="iso3c", axis=1)

# %%
t1 = (
    Y_cal_losses
    .rename_axis(["consuming_country"], axis=1)
    .droplevel(["comm_group", "group"])
    .rename_axis(["year", "producing_country", "item"], axis=0)
)

# %%
t1 = (
    pd.concat(Y_cal_list, keys=years, names=["year"], axis=1)
    .rename(iso3_mapper, level="iso3c", axis=1)
    .reorder_levels([1, 0], axis=1)
    .rename_axis(["area", "year"], axis=1)
    .rename_axis(["area_output", "item_output", "comm_group_output", "group_output"], axis=0)
)
Y_cal_domestic = domestic_split(t1)


# %%
# Use mappings from repository
auxiliary_path = (
    data_path
    / "auxiliary"
    / "auxiliary"
)

product_mapping = (
    pd.read_csv(
        auxiliary_path / "fabio-exio_sup_v1.2.csv",
        header=[0],
        index_col=[0, 1, 2, 3]
    )
    .replace(0, np.nan)
    .rename_axis(["sector"], axis=1)
    .droplevel([0, 2, 3])
    .rename_axis(["item_output"], axis=0)
    .stack()
    .reset_index()
    .drop([0], axis=1)
)




# %%
readRDS = robjects.r['readRDS']
# Read RDS file
rds_file = readRDS(str(fabio_path / "E.rds"))

dfs_landuse = []
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
    df_landuse = pd.concat(dfs_tmp, axis=1)
    dfs_landuse.append(df_landuse)

FABIO_landuse = pd.concat(dfs_landuse, axis=0, keys=years, names=["year"])

# %%
crop_landuse = FABIO_landuse[~(FABIO_landuse["item"] == "Grazing")].groupby(["year"])["landuse"].sum()

grazing_landuse = FABIO_landuse[(FABIO_landuse["item"] == "Grazing")].groupby(["year"])["landuse"].sum()


# %%
primary_list = []
processed_list = []
biomass_production_mapped_shares_list = []
primary_upstream_energy_allocated_list = []
processed_upstream_energy_allocated_list = []
exclude_negatives = True
for year in years:
    reader = fabio_functions.read(
        fabio_path,
        year=year,
        version=1.2
    )

    Z = reader.Z(version="mass")

    # TODO: read Y from file instead
    Y = reader.Y()
    Y = (
        Y
        .loc[
            :,
            Y.columns.isin(final_demand_categories, level="final demand")
        ]
        .groupby(["iso3c"], axis=1).sum()
    )
    if exclude_negatives:
        Y[Y < 0] = 0

    x = Y.sum(axis=1) + Z.sum(axis=1)
    biomass_production = (
        x
        .droplevel(["area_code", "item_code", "comm_code"])
        .rename_axis([
            "area_output",
            "item_output",
            "comm_group_output",
            "group_output"
        ])
    )

    # Upstream energy
    upstream_energy_path = (
        server_path
        / "DATA"
        / "eroi_of_food"
        / "upstream_energy_use"
        / "unallocated"
        / f"{year}"
        / "target_perspective"
    )

    primary_upstream_energy = pd.read_csv(
        upstream_energy_path / "primary_crops.tsv",
        sep="\t",
        index_col= [0],
        header=[0, 1]
    ).replace([np.inf, np.nan, -np.inf], 0).sum(axis=0)
    primary_list.append(
        primary_upstream_energy
    )
    processed_upstream_energy = pd.read_csv(
        upstream_energy_path / "processed_food.tsv",
        sep="\t",
        index_col= [0],
        header=[0, 1]
    ).replace([np.inf, np.nan, -np.inf], 0).sum(axis=0)
    processed_list.append(
        processed_upstream_energy
    )

    ## Allocate upstream energy using biomass production
    biomass_production_mapped = (
        biomass_production[
            biomass_production
            .index
            .get_level_values("item_output")
            .isin(product_mapping.item_output)
        ]
        .to_frame("biomass_output")
        .reset_index()
        .merge(
            product_mapping,
            on="item_output",
            how="left"
        )
        .merge(
            regions[["area", "region"]],
            left_on="area_output",
            right_on="area"
        ).drop("area", axis=1)
        .pivot(
            columns=biomass_production.index.names,
            index=["region", "sector"],
            values="biomass_output"
        )
    )

    biomass_production_mapped_shares = (
        biomass_production_mapped
        .div(
            biomass_production_mapped.sum(axis=1),
            axis=0
        ).replace([np.nan, np.inf, -np.inf], 0)
    )
    biomass_production_mapped_shares_list.append(
        biomass_production_mapped_shares
    )

    primary_upstream_energy_allocated = (
        biomass_production_mapped_shares
        .loc[primary_upstream_energy.index, :]
        .T
        .dot(primary_upstream_energy)
    )
    primary_upstream_energy_allocated_list.append(
        primary_upstream_energy_allocated
    )

    processed_upstream_energy_allocated = (
        biomass_production_mapped_shares
        .loc[processed_upstream_energy.index, :]
        .T
        .dot(processed_upstream_energy)
    )
    processed_upstream_energy_allocated_list.append(
        processed_upstream_energy_allocated
    )


# %%
biomass_production_mapped_shares = pd.concat(biomass_production_mapped_shares_list, keys=years, names=["year"])
primary_upstream_energy_allocated = pd.concat(primary_upstream_energy_allocated_list, keys=years, names=["year"])
processed_upstream_energy_allocated = pd.concat(processed_upstream_energy_allocated_list, keys=years, names=["year"])

# %% [markdown]
# ### IEA Product level results

# %%
result_prod_list = []
for year in tqdm(years):
    result_prod_list.append(
        pd.read_csv(
            results_path / "excl_negatives" / f"{year}" / "results_product.tsv",
            sep="\t",
            index_col=[0, 1, 2],
            header=[0, 1, 2, 3]
        )
    )

# %%
df_prod = pd.concat(result_prod_list, keys=years, names=["year"], axis=0)
df_prod.loc[df_prod.index.isin(["fertiliser"], level="source")] = df_prod.loc[df_prod.index.isin(["fertiliser"], level="source")] * 0.91

# %%
df_prod_filter = (
    df_prod
    .drop([
        'Alcohol', 
        #'Animal fats', 
        #'Cereals', 
        #'Coffee, tea, cocoa', 
        #'Eggs',
        'Ethanol', 
        'Fibre crops', 
        #'Fish', 
        'Fodder crops', 
        'Grazing',
        'Hides, skins, wool', 
        #'Honey', 
        'Live animals', 
        #'Meat', 
        #'Milk',
        #'Oil cakes', 
        #'Oil crops', 
        #'Roots and tubers', 
        #'Sugar crops',
        #'Sugar, sweeteners', 
        'Tobacco, rubber', 
        #'Vegetable oils',
        #'Vegetables, fruit, nuts, pulses, spices'
    ], axis=1, level="comm_group")
    .drop([
        "Oilcrops Oil, Other",
        "Oilseed Cakes, Other",
        "Beverages, Alcoholic",
        "Beer",
        "Beverages, Fermented",
        "Offals, Edible",
        "Meat, Other"
    ], axis=1, level="item")
    .drop(2020)
)

# %%
t1 = (
    df_prod_filter
    .rename(IEA_product_grouping, level="other", axis=0)
    .rename({"Fertiliser": "Non-renewable"}, level="other", axis=0)
    .groupby(["year", "direction", "source", "other"])
    .sum()
    .rename(five_year_agg, level="year", axis=0)
    .groupby(["year", "direction", "source", "other"])
    .mean()
    .rename(area_to_UN, axis=1, level="area")
    .rename(product_groups, axis=1, level="item")
    .groupby(["area", "item"], axis=1).sum()
)


# %% [markdown]
# ### IEA Flow level results
# %%
result_list_source = []
for year in tqdm(years):
    result_list_source.append(
        pd.read_csv(
            results_path / "excl_negatives" / f"{year}" / "results_source_flow.tsv",
            sep="\t",
            index_col=[0, 1, 2, 3, 4],
            header=[0, 1, 2, 3],
        )
    )

# %%
df_source = (
    pd.concat(result_list_source, keys=years, names=["year"], axis=0)
    .rename_axis(["area", "item", "comm_group", "group"], axis=1)
)
df_source.loc[df_source.index.isin(["fertiliser_energy"], level="variable")] = df_source.loc[df_source.index.isin(["fertiliser_energy"], level="variable")] * 0.91

# %%
df_source_filter = (
    df_source
    .drop([
        'Alcohol', 
        #'Animal fats', 
        #'Cereals', 
        #'Coffee, tea, cocoa', 
        #'Eggs',
        'Ethanol', 
        'Fibre crops', 
        #'Fish', 
        'Fodder crops', 
        'Grazing',
        'Hides, skins, wool', 
        #'Honey', 
        'Live animals', 
        #'Meat', 
        #'Milk',
        #'Oil cakes', 
        #'Oil crops', 
        #'Roots and tubers', 
        #'Sugar crops',
        #'Sugar, sweeteners', 
        'Tobacco, rubber', 
        #'Vegetable oils',
        #'Vegetables, fruit, nuts, pulses, spices'
    ], axis=1, level="comm_group")
    .drop([
        "Oilcrops Oil, Other",
        "Oilseed Cakes, Other",
        "Beverages, Alcoholic",
        "Beer",
        "Beverages, Fermented",
        "Offals, Edible",
        "Meat, Other"
    ], axis=1, level="item")
)

# %%
result_list = []
for year in tqdm(years):
    result_list.append(
        pd.read_csv(
            results_path / "excl_negatives" / f"{year}" / "results_flow.tsv",
            sep="\t",
            index_col=[0, 1, 2],
            header=[0, 1, 2, 3]
        )
    )

# %%
df = pd.concat(result_list, keys=years, names=["year"], axis=0)
df.loc[df.index.isin(["fertiliser"], level="source")] = df.loc[df.index.isin(["fertiliser"], level="source")] * 0.91

# %%
df1 = (
    df
    .unstack("year")
    .rename({"CÃ´te d'Ivoire": "Côte d'Ivoire"}, axis=1, level="area")
    .rename(area_to_agg, axis=1, level="area")
    .rename(IEA_product_grouping, level="other", axis=0)    
)

df2 = (
    df1.loc[
        df1.index.isin(["energy_output", "energy_input"], level="direction"),
        :
    ]
    .groupby(["direction", "other"]).sum()
    .groupby(
        level=[
            "year",
            "area",
            #"year",
            "group",
            "comm_group",
            "item"
        ],
        axis=1
    ).sum()
)
inputs = df2.loc["energy_input"]
outputs = df2.loc["energy_output"].loc["consumption"]
EROI = outputs.div(inputs.sum(axis=0)).replace([np.nan, np.inf, -np.inf], 0)

# %%
EROI = df2.loc["energy_output"].loc["consumption"].sum() / inputs.sum().sum() 

# %%
EROI_incl_losses = df2.loc["energy_output"].sum().sum() / inputs.sum().sum() 


# %%
df_filter = (
    df
    .drop([
        'Alcohol', 
        #'Animal fats', 
        #'Cereals', 
        #'Coffee, tea, cocoa', 
        #'Eggs',
        'Ethanol', 
        'Fibre crops', 
        #'Fish', 
        'Fodder crops', 
        'Grazing',
        'Hides, skins, wool', 
        #'Honey', 
        'Live animals', 
        #'Meat', 
        #'Milk',
        #'Oil cakes', 
        #'Oil crops', 
        #'Roots and tubers', 
        #'Sugar crops',
        #'Sugar, sweeteners', 
        'Tobacco, rubber', 
        #'Vegetable oils',
        #'Vegetables, fruit, nuts, pulses, spices'
    ], axis=1, level="comm_group")
    .drop([
        "Oilcrops Oil, Other",
        "Oilseed Cakes, Other",
        "Beverages, Alcoholic",
        "Beer",
        "Beverages, Fermented",
        "Offals, Edible",
        "Meat, Other"
    ], axis=1, level="item")
    .drop(2020)
)

# %% [markdown]
# # Comparing numbers

# %% [markdown]
# ### Krausmann et al. (2003) - Austria

# %%
t_region = "Austria"
t_years = np.arange(1995, 1998)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Hamilton et al. (2013) - Canada

# %%
t_region = "Canada"
t_years = np.arange(2008, 2011)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Adetona & Layzell (2019) - Canada

# %%
t_region = "Canada"
t_years = np.arange(2010, 2014)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2_1 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "Total final consumption; Agriculture/forestry",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t2_2 = t2[
    (t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3 = pd.concat([t2_1, t2_2])
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2_1 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "Total final consumption; Agriculture/forestry",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t2_2 = t2[
    (t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3 = pd.concat([t2_1, t2_2])
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2_1 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "Total final consumption; Agriculture/forestry",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t2_2 = t2[
    (t2.index.isin(["processed"], level="source"))
]
t3 = pd.concat([t2_1, t2_2])
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Cao et al. (2010) - China

# %%
t_region = ['China, Hong Kong SAR', 'China, Macao SAR', 'China, mainland']
t_years = np.arange(2003, 2006)

# %%
(
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
    .groupby(["direction", "source"]).sum()
)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Greslova et al. (2019) - Czech Republic

# %%
t_region = "Czech Republic"
t_years = np.arange(2011, 2014)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Cunfer et al. (2017) - USA

# %%
t_region = "United States of America"
t_years = np.arange(1996, 1999)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Markussen and Østergård (2013) - Denmark

# %%
t_region = "Denmark"
t_years = np.arange(2004, 2008)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    #& (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Perez-Soba et al. (2015) - EU27

# %%
t_region = [
    "Denmark",
    "Finland",
    "Sweden",
    "Cyprus",
    "Estonia",
    "Latvia",
    "Lithuania",
    "Poland",
    "Czech Republic",
    "Slovakia",
    "Slovenia",
    "Portugal",
    "Spain",
    "Greece",
    "Hungary",
    "Italy",
    "Ireland",
    "France",
    "Germany",
    "Austria",
    "Belgium",
    "Netherlands",
    "Luxembourg",
    "United Kingdom",
    "Malta",
    "Bulgaria",
    "Romania"
]
t_years = np.arange(2003, 2006)

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Harchaoui & Chatzimpiros (2018b) - France

# %%
t_region = "France"
t_years = np.arange(2016, 2019)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Gingrich et al. (2018) - Grunburg, Austria

# %%
t_region = "Austria"
t_years = np.arange(1999, 2002)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Frankova and Cattaneo (2018) - Holubi Zhor, Czech Republic

# %%
# Same as Greslova et al. (2019)

# %% [markdown]
# ### Behesti Tabar et al. (2010) - Iran

# %%
t_region = "Iran (Islamic Republic of)"
t_years = np.arange(2005, 2008)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Gasparatos (2011) - Japan

# %%
t_region = "Japan"
t_years = np.arange(2004, 2007)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Diez et al. (2018) - Catalonia (Spain)

# %%
t_region = "Spain"
t_years = np.arange(1998, 2001)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Greslova et al. (2019) - Poland

# %%
t_region = "Poland"
t_years = np.arange(2011, 2014)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### MacFadyen and Watson (2018) - Canada

# %%
t_region = "Canada"
t_years = np.arange(2009, 2012)

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Parcerisas and Dupras (2018) - Canada

# %%
t_region = "Canada"
t_years = np.arange(2010, 2013)

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Gingrich et al. (2018) - Sankt Florian, Austria

# %%
# Same as other Gingrich

# %% [markdown]
# ### Guzman et al. (2018) - Spain

# %%
t_region = "Spain"
t_years = np.arange(2007, 2010)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Infante Amate & de Molina (2013) - Spain

# %%
t_region = "Spain"
t_years = np.arange(1999, 2002)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        "Total final consumption; Industry; Manufacturing; Food and tobacco",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    #& (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Ozkan et al. (2004) - Turkey

# %%
t_region = "Turkey"
t_years = np.arange(1999, 2002)

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %% [markdown]
# ### Hamilton et al. (2013) - USA

# %%
t_region = "United States of America"
t_years = np.arange(2008, 2011)

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        #"Total final consumption; Fishing",
        "consumption",
        "Transformation processes; Autoproducer heat plants",
        "Transformation processes; Main activity producer CHP plants",
        "Transformation processes; Main activity producer electricity plants",
        "Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[:, df_filter.columns.isin(["Primary crops"], level="group")]
    .loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
    & (~t1.index.isin(["processed"], level="source"))
]
t3 = t2.copy()
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = df_filter.loc[
    (df_filter.index.isin(["energy_output", "energy_input"], level="direction"))
    & (df_filter.index.isin(["consumption", "primary", "processed", "fertilizer"], level="source"))
     ,
    (df_filter.columns.isin(["Vegetable oils"], level="comm_group"))
].loc[2019, "United States of America"].groupby("direction").sum().sum(axis=1)
t1.loc["energy_output"] / (t1.loc["energy_input"])

# %%
t1 = df_filter.loc[
    (df_filter.index.isin(["energy_output", "energy_input"], level="direction"))
    & (df_filter.index.isin(["consumption", "primary", "processed", "fertilizer"], level="source"))
     ,
    (df_filter.columns.isin(["Vegetable oils"], level="comm_group"))
].loc[2019, "Brazil"].groupby("direction").sum().sum(axis=1)
t1.loc["energy_output"] / (t1.loc["energy_input"])

# %%
t1 = df_filter.loc[
    (df_filter.index.isin(["energy_output", "energy_input"], level="direction"))
    & (df_filter.index.isin(["consumption", "primary", "processed", "fertilizer"], level="source"))
     ,
    (df_filter.columns.isin(["Cereals"], level="comm_group"))
].loc[2019, "United States of America"].groupby("direction").sum().sum(axis=1)
t1.loc["energy_output"] / (t1.loc["energy_input"])

# %%
t1 = df_filter.loc[
    (df_filter.index.isin(["energy_output", "energy_input"], level="direction"))
    & (df_filter.index.isin(["consumption", "primary", "processed", "fertilizer"], level="source"))
     ,
    (df_filter.columns.isin(["Cereals"], level="comm_group"))
].loc[2019, "Brazil"].groupby("direction").sum().sum(axis=1)
t1.loc["energy_output"] / (t1.loc["energy_input"])

# %%
set(df_filter.columns.get_level_values("area"))

# %% [markdown]
# ### Hamilton et al. (2013) - USA

# %%
t_region = "United States of America"
t_years = np.arange(2008, 2011)

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t3 = t2[
    (~t2.index.isin(["processed"], level="source"))
    & (t2.index.isin([
        "K2O",
        "N",
        "P2O5",
        "Total final consumption; Agriculture/forestry",
        "consumption",
        #"Transformation processes; Autoproducer heat plants",
        #"Transformation processes; Main activity producer CHP plants",
        #"Transformation processes; Main activity producer electricity plants",
        #"Transformation processes; Main activity producer heat plants"
    ], level="other"))
]
t3.loc["energy_output"].div(t3.loc["energy_input"].sum())

# %%
t1 = (
    df_filter.loc[t_years, t_region].sum(axis=1).groupby(["direction", "source", "other"]).mean()
    .loc[["energy_input", "energy_output"]]
)
t2 = t1[
    (~t1.index.isin(["other_losses"], level="source"))
]
t2.loc["energy_output"].div(t2.loc["energy_input"].sum())

# %% [markdown]
# # Other uses and losses

# %%
other_uses_and_losses = (
    df_prod_filter
    .replace([np.inf, -np.inf, np.nan], 0)
    .rename(area_to_UN, level="area", axis=1)
    .rename(product_groups, level="item", axis=1)
    .rename(five_year_agg, level="year", axis=0)
    .groupby(["source", "direction", "year"]).sum()
    .T.groupby(["area", "item"]).sum().T
    .loc[("other_losses", "energy_output"), :]
    .stack(["area", "item"])
)

# %% [markdown]
# # LBF

# %%
t1 = df_source_filter.loc[np.arange(1995, 2000), :].groupby(["variable", "item_output", "group_output"]).mean()

t2 = (
    t1
    .loc[
        (t1.index.isin(["Primary crops"], level="group_output"))
        & (t1.index.isin(["biomass"], level="variable")),
        t1.columns.isin(["Livestock products"], level="group")
    ]
    .groupby("item_output").sum()
    .sum(axis=1)
    .sort_values()
    .rename("inputs")
)

t3 = pd.merge(left=t2, right=nutrient_coefficients, how="left", left_index=True, right_index=True)

LBFs = t3["inputs"] * t3["kcal_per_kg"] * 4.1858e-6

LBF_human_edibles = LBFs.drop(["Fodder crops", "Grazing"]).sum() /1e6

LBF_fodder_cropss = LBFs.loc["Fodder crops"].sum() /1e6

LBF_grazings = LBFs.loc["Grazing"] /1e6

# %%
t1 = df_source_filter.loc[np.arange(2015, 2020), :].groupby(["variable", "item_output", "group_output"]).mean()

t2 = (
    t1
    .loc[
        (t1.index.isin(["Primary crops"], level="group_output"))
        & (t1.index.isin(["biomass"], level="variable")),
        t1.columns.isin(["Livestock products"], level="group")
    ]
    .groupby("item_output").sum()
    .sum(axis=1)
    .sort_values()
    .rename("inputs")
)

t3 = pd.merge(left=t2, right=nutrient_coefficients, how="left", left_index=True, right_index=True)

LBF = t3["inputs"] * t3["kcal_per_kg"] * 4.1858e-6

LBF_human_edible = LBF.drop(["Fodder crops", "Grazing"]).sum() /1e6

LBF_fodder_crops = LBF.loc["Fodder crops"].sum() /1e6

LBF_grazing = LBF.loc["Grazing"] /1e6

# %% [markdown]
# # Energy output 

# %%
t1 = df_filter.loc[np.arange(1995, 2000)].groupby(["direction", "source", "other"]).mean().groupby(["direction", "source"]).sum()
#t1 = t1.loc[:, ~t1.columns.isin(["Livestock products"], level="group")]
v1 = (
    (
        t1.loc[(
            "energy_output",
            #"consumption"
            #"other_losses"
        ), :].sum().sum() / 1e6 
    )
)
print(v1)

# %%
t1 = df_filter.loc[np.arange(2015, 2020)].groupby(["direction", "source", "other"]).mean().groupby(["direction", "source"]).sum()
#t1 = t1.loc[:, ~t1.columns.isin(["Livestock products"], level="group")]
v2 = (
        t1.loc[(
            "energy_output",
            #"consumption"
            #"other_losses"
        ), :].sum().sum() / 1e6
    )
print(v2)



# %% [markdown]
# # Energy input

# %%
(
    + LBF_human_edible
    + LBF_fodder_crops
    + LBF_grazing
)

# %%
t1 = df_filter.loc[np.arange(1995, 2000)].groupby(["direction", "source", "other"]).mean()
v1 = t1.groupby("source").sum().sum(axis=1).drop(["biomass_footprint", "biomass_production"])/1e6

v1

# %%
w1 = v1.loc[["fertiliser", "primary", "processed"]].sum() + (
    + LBF_human_edibles
    + LBF_fodder_cropss
    + LBF_grazings
)

# %%
t1 = df_filter.loc[np.arange(2015, 2020)].groupby(["direction", "source", "other"]).mean()
v2 = t1.groupby("source").sum().sum(axis=1).drop(["biomass_footprint", "biomass_production"])/1e6
v2

# %%
w2 = v2.loc[["fertiliser", "primary", "processed"]].sum() + (
    + LBF_human_edible
    + LBF_fodder_crops
    + LBF_grazing
)


# %% [markdown]
# # Energy input fertilizer

# %%
t1 = (
    df_filter
    .loc[np.arange(1995, 2000)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["other"]
    .loc["fertiliser_input"]
    .sum(axis=1)
    .sum()
)
t2 = (
    df_filter
    .loc[np.arange(2015, 2019)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["other"]
    .loc["fertiliser_input"]
    .sum(axis=1)
    .sum()
)


# %% [markdown]
# # Energy input food processing

# %%
t1 = (
    df_filter
    .loc[np.arange(1995, 2000)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["energy_input"]
    .loc["processed"]
    .sum(axis=1)
)

v1 = t1.sort_values()/1e6

v1_direct_filter = v1.index.str.contains("Manufacturing; Food")
v1_road_filter = v1.index.str.contains("Transport; Road")
v1_elec_heat_filter = (v1.index.str.contains("electricity") | v1.index.str.contains("CHP") | v1.index.str.contains("heat"))


# %%
t1 = (
    df_filter
    .loc[np.arange(2015, 2020)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["energy_input"]
    .loc["processed"]
    .sum(axis=1)
)
v2 = t1.sort_values()/1e6
direct_filter = v2.index.str.contains("Manufacturing; Food")
road_filter = v2.index.str.contains("Transport; Road")
elec_heat_filter = (v2.index.str.contains("electricity") | v2.index.str.contains("CHP") | v2.index.str.contains("heat"))

# %%
print(v2.sum())
print(((v2.sum() / v1.sum())-1)*100)

# %%
cur_filter = direct_filter
v1_cur_filter = v1_direct_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = elec_heat_filter
v1_cur_filter = v1_elec_heat_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = road_filter
v1_cur_filter = v1_road_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = ~(direct_filter | elec_heat_filter | road_filter)
v1_cur_filter = ~(v1_direct_filter | v1_elec_heat_filter | v1_road_filter)
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %% [markdown]
# # Energy input agriculture

# %%
t1 = (
    df_filter
    .loc[np.arange(1995, 2000)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["energy_input"]
    .loc["primary"]
    .sum(axis=1)
)
v1 = t1.sort_values()/1e6

v1_direct_filter = v1.index.str.contains("Agriculture/forestry")
v1_road_filter = v1.index.str.contains("Transport; Road")
v1_elec_heat_filter = (v1.index.str.contains("electricity") | v1.index.str.contains("CHP") | v1.index.str.contains("heat"))


# %%
t1 = (
    df_filter
    .loc[np.arange(2015, 2020)]
    .groupby(["direction", "source", "other"])
    .mean()
    .loc["energy_input"]
    .loc["primary"]
    .sum(axis=1)
)
v2 = t1.sort_values()/1e6
direct_filter = v2.index.str.contains("Agriculture/forestry")
road_filter = v2.index.str.contains("Transport; Road")
elec_heat_filter = (v2.index.str.contains("electricity") | v2.index.str.contains("CHP") | v2.index.str.contains("heat"))


# %%
cur_filter = direct_filter
v1_cur_filter = v1_direct_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = elec_heat_filter
v1_cur_filter = v1_elec_heat_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = road_filter
v1_cur_filter = v1_road_filter
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)

# %%
cur_filter = ~(direct_filter | elec_heat_filter | road_filter)
v1_cur_filter = ~(v1_direct_filter | v1_elec_heat_filter | v1_road_filter)
print(v2[cur_filter].sum())
print(((v2[cur_filter].sum() / v1[v1_cur_filter].sum())-1 )*100)
print((v2[cur_filter].sum() / v2.sum())*100)


# %%
t1 = df_filter.loc[np.arange(1995, 2000)].groupby(["direction", "source", "other"]).mean().groupby(["direction", "source"]).sum()
v1 = (
    (
        t1.loc[(
            "energy_output",
            #"consumption"
        ), :].sum().sum() / 1e6 
    ) 
    / (
        t1.loc[("energy_input"), :].sum().sum() / 1e6
        + LBF_human_edibles
        + LBF_fodder_cropss
        + LBF_grazings
    )
)


# %%
t1 = df_filter.loc[np.arange(2015, 2020)].groupby(["direction", "source", "other"]).mean().groupby(["direction", "source"]).sum()
v2 = (
    (
        t1.loc[(
            "energy_output",
            #"consumption"
        ), :].sum().sum() / 1e6
    ) 
    / (
        t1.loc[("energy_input"), :].sum().sum() / 1e6
        + LBF_human_edible
        + LBF_fodder_crops
        + LBF_grazing
    )
)


# %% [markdown]
# # Other FAO Statistics

# %%
for faostat_folder in os.listdir(faostat_path):
    if faostat_folder == "Population_E_All_Data":
        population_raw = (
            pd.read_csv(
                faostat_path / faostat_folder / f"{faostat_folder}_NOFLAG.csv",
                encoding="cp1252",
                index_col=np.arange(0, 8),
                header=[0]
            )
            .rename(lambda x: int(x.split("Y")[1]), axis=1)
            .rename_axis(["Year"], axis=1)
            .droplevel(["Area Code (M49)", "Area", "Item Code", "Element Code"])
            .rename(code_to_area_mapper, level="Area Code")
            .stack()
        )
    elif faostat_folder == "Employment_Indicators_Agriculture_E_All_Data":
        employment_indicators_raw = (
            pd.read_csv(
                faostat_path / faostat_folder / f"{faostat_folder}_NOFLAG.csv",
                encoding="cp1252",
                index_col=np.arange(0, 12),
                header=[0],
            )
            .rename(lambda x: int(x.split("Y")[1]), axis=1)
            .rename_axis(["Year"], axis=1)
            .droplevel(["Area Code (M49)", "Area", "Indicator Code", "Element Code", "Sex Code", "Source Code"])
            .rename(code_to_area_mapper, level="Area Code")
            .stack()
        )
    elif faostat_folder == "Investment_CapitalStock_E_All_Data":
        investment_capitalstock_raw = (
            pd.read_csv(
                faostat_path / faostat_folder / f"{faostat_folder}_NOFLAG.csv",
                encoding="cp1252",
                index_col=np.arange(0, 8),
                header=[0],
            )
            .rename(lambda x: int(x.split("Y")[1]), axis=1)
            .rename_axis(["Year"], axis=1)
            .droplevel(["Area Code (M49)", "Area", "Item Code", "Element Code"])
            .rename(code_to_area_mapper, level="Area Code")
            .stack()
        )

    elif faostat_folder == "Macro-Statistics_Key_Indicators_E_All_Data":
        macro_statistics_raw = (
            pd.read_csv(
                faostat_path / faostat_folder / f"{faostat_folder}_NOFLAG.csv",
                encoding="cp1252",
                index_col=np.arange(0, 8),
                header=[0],
            )
            .rename(lambda x: int(x.split("Y")[1]), axis=1)
            .rename_axis(["Year"], axis=1)
            .droplevel(["Area Code (M49)", "Area", "Item Code", "Element Code"])
            .rename(code_to_area_mapper, level="Area Code")
            .stack()
        )
    else:
        break


# %%
investment_capitalstock = (
    investment_capitalstock_raw.loc[
        (
            investment_capitalstock_raw
            .index.isin(
                ["Net Capital Stocks (Agriculture, Forestry and Fishing)"],
                level="Item"
            )
        )
        & ( 
            investment_capitalstock_raw
            .index.isin(
                ["Value US$, 2015 prices"],
                level="Element"
            )
        )
    ]
    .to_frame("Net Capital Stocks")
    .droplevel(["Item", "Element", "Unit"])
    .reset_index()
)

investment_capitalstock = (
    investment_capitalstock.loc[~investment_capitalstock["Area Code"].str.isdigit().replace(np.nan, True), :]
    .rename({"Area Code": "Area"}, axis=1)
    .set_index(["Area", "Year"])
    .loc[:, "Net Capital Stocks"]
)
investment_capitalstock_un = (
    investment_capitalstock
    #.set_index(["area", "year"])
    .rename(area_to_UN, level="Area")
    .groupby(["Area", "Year"]).sum()   
)
investment_capitalstock_global = (
    investment_capitalstock_un
    .groupby("Year").sum()
)

# %%
total_employment = (
    employment_indicators_raw.loc[
        (
            employment_indicators_raw
            .index.isin(
                ["Employment in agriculture, forestry and fishing - ILO modelled estimates"],
                level="Indicator"
            )
        )
        & ( 
            employment_indicators_raw
            .index.isin(
                ["Total"],
                level="Sex"
            )
        )
    ]
    .to_frame("Employees")
    .droplevel(["Source", "Indicator", "Sex", "Element", "Unit"])
    .reset_index()
)
total_employment = (
    total_employment.loc[~total_employment["Area Code"].str.isdigit().replace(np.nan, True), :]
    .rename({"Area Code": "Area"}, axis=1)
    .set_index(["Area", "Year"])
    .loc[:, "Employees"]
)
total_employment_un = (
    total_employment
    #.set_index(["area", "year"])
    .rename(area_to_UN, level="Area")
    .groupby(["Area", "Year"]).sum()
)
total_employment_global = (
    total_employment_un.groupby("Year").sum()
)

# %% [markdown]
# # Relative growth of key indicators

# %% [markdown]
# ## Global

# %%
units = {
    'Biomass production': " Gt",
    'Calorie consumption': " EJ",
    'EROEI': "",
    "Employment in agriculture": " Mill.",
    "Energy footprint of agriculture sectors": " EJ",
    "Energy footprint of food processing sectors": " EJ",
    'Fertiliser energy footprint': " EJ",
    #'Fertiliser use',
    "Net capital stock in agriculture": " Tril. $",
    'Population': " Bill."
}
factor = {
    'Biomass production': 10e9,
    'Calorie consumption': 1e6,
    'EROEI': 1e0,
    "Employment in agriculture": 1e3,
    "Energy footprint of agriculture sectors": 1e6,
    "Energy footprint of food processing sectors": 1e6,
    'Fertiliser energy footprint': 1e6,
    #'Fertiliser use',
    'Net capital stock in agriculture': 1e6,
    'Population': 1e9
}

sns.set_theme(style="whitegrid")
t1 = (
    df_filter.loc[
        df_filter.index.isin([
            "consumption",
            "primary",
            "processed",
            "fertiliser",
            #"fertiliser_input",
            "biomass_production"
        ], level="source")
    ]
    .groupby("area", axis=1).sum()
    .groupby(["year", "direction", "source"], axis=0).sum()
    .stack()
    .reorder_levels(["direction", "source", "year", "area"])
    .droplevel("direction")
    .unstack("source")
    .rename_axis(["Variable"], axis=1)
    .rename({
        "biomass_production": "Biomass production",
        "consumption": "Calorie consumption",
        "fertiliser": "Fertiliser energy footprint",
        #"fertiliser_input": "Fertiliser use",
        "primary": "Energy footprint of agriculture sectors",
        "processed": "Energy footprint of food processing sectors"
    }, axis=1)
    .rename_axis(["Year", "Area"], axis=0)
    .groupby(["Year"], axis=0).sum()
    
)

t1["External energy input"] = (
    t1["Fertiliser energy footprint"]
    + t1["Energy footprint of agriculture sectors"]
    + t1["Energy footprint of food processing sectors"]
)

t1["EROEI"] = (
    t1["Calorie consumption"].div(t1["External energy input"])
)

t1["Population"] = global_pop_df
t1["Net capital stock in agriculture"] = investment_capitalstock_global
t1["Employment in agriculture"] = total_employment_global
t1 = t1.loc[:, [
    "EROEI",
    "Calorie consumption",
    "External energy input",
    #"Biomass production",
    "Employment in agriculture",
    "Population",
    "Net capital stock in agriculture"
]]


t1.columns = (
    t1
    .columns
    .map(
        lambda x: f"{x} ({number_to_text(t1.loc[2020, x]/factor[x])}{units[x]})"
    )
)
t2 = t1.div(t1.loc[1995, :]).stack().to_frame("Relative change").reset_index()

fig, ax = plt.subplots(figsize=(15, 8))
sns.lineplot(data=t2, x="Year", y="Relative change", hue="Variable", ax=ax, linewidth=3)
leg = ax.legend(
    ncol=1,
    loc="upper left", 
    #bbox_to_anchor=[0.5, 1.1],
    title="Variable (Value in 2020)"
)
for legobj in leg.legend_handles:
    legobj.set_linewidth(5.0)
plt.savefig('testing.eps', format='eps')
fig.show()



# %% [markdown]
# ## By UN regions

# %%
pd.set_option('display.float_format', lambda x: '%.2f' % x)

t0 = (
    df_filter.loc[
        df_filter.index.isin([
            "consumption",
            "primary",
            "processed",
            "fertiliser",
            "fertiliser_input",
            "biomass_production",
            "biomass_footprint"
        ], level="source")
    ]
    .groupby("area", axis=1).sum()
    .groupby(["year", "direction", "source"], axis=0).sum()
    .stack()
    .reorder_levels(["direction", "source", "year", "area"])
    .droplevel("direction")
    .unstack("source")
    .rename({
        "biomass_production": "Biomass production",
        "consumption": "Calorie consumption",
        "fertiliser": "Fertiliser energy footprint",
        "fertiliser_input": "Fertiliser use footprint",
        "primary": "Primary food energy footprint",
        "processed": "Procssed food energy footprint",
        "biomass_footprint": "Biomass footprint"
    }, axis=1)
    .rename_axis(["Year", "Area"], axis=0)
    .rename(area_to_UN, axis=0, level="Area")
    .groupby(["Area", "Year"], axis=0).sum()
    .merge(
        un_pop_df.to_frame("Population"),
        how="left",
        left_index=True,
        right_index=True
    )
    .merge(
        investment_capitalstock_un.to_frame("Net capital stock"),
        how="left",
        left_index=True,
        right_index=True
    )
    .merge(
        total_employment_un.to_frame("Employment"),
        how="left",
        left_index=True,
        right_index=True
    )
    .rename_axis(["Variable"], axis=1)
)


areas = t0.index.get_level_values("Area").unique()
correlation_scores = []
fig, axes = plt.subplots(
    nrows=len(areas), 
    ncols=1, 
    figsize=(10, 5*len(areas)),
    gridspec_kw={"hspace": 0.3}
)

for index, area in enumerate(areas):
    t1 = t0.loc[area]
    #t1 = t1.rolling(5, min_periods=3, center=True, axis=0).mean()
    
    t1["EROEI"] = (
        t1["Calorie consumption"].div(
            t1["Fertiliser energy footprint"]
            + t1["Primary food energy footprint"]
            + t1["Procssed food energy footprint"]
        )
    )
    correlation_scores.append(t1.corr().loc["EROEI"])
    t1.columns = t1.columns.map(lambda x: f"{x} ({number_to_text(t1.loc[2020, x])})")
    
    t2 = t1.div(t1.loc[1995, :]).stack().to_frame("Relative change").reset_index()
    cmap = dict(zip(t1.columns.values, sns.color_palette("tab20")))
    ax = axes[index]
    sns.lineplot(data=t2, x="Year", y="Relative change", hue="Variable", ax=ax, legend="brief", palette=cmap)
    ax.legend(bbox_to_anchor=(1, 1), title="Variable (Value in 2020)")
    ax.set_title(area)

fig.show()

# Southern Africa large increase in 2016 is due to large increase in the processed energy input in South Africa
# Polynesia, Micronesia, Melanesia, and ROW have been aggregated to ROW.

# %%
# %% [markdown]
# ## By comm_group

# %%
t0 = (
    df_filter.loc[
        df_filter.index.isin([
            "consumption",
            "primary",
            "processed",
            "fertiliser",
            "fertiliser_input",
            "biomass_production",
            "biomass_footprint"
        ], level="source")
    ]
    .groupby("comm_group", axis=1).sum()
    .groupby(["year", "direction", "source"], axis=0).sum()
    .stack()
    .reorder_levels(["direction", "source", "year", "comm_group"])
    .droplevel("direction")
    .unstack("source")
    .rename({
        "biomass_production": "Biomass production",
        "consumption": "Calorie consumption",
        "fertiliser": "Fertiliser energy footprint",
        "fertiliser_input": "Fertiliser use footprint",
        "primary": "Primary food energy footprint",
        "processed": "Procssed food energy footprint",
        "biomass_footprint": "Biomass footprint"
    }, axis=1)
    .rename_axis(["Year", "Commodity group"], axis=0)
    .rename(area_to_UN, axis=0, level="Commodity group")
    .groupby(["Commodity group", "Year"], axis=0).sum()
#     .merge(
#         un_pop_df.to_frame("Population"),
#         how="left",
#         left_index=True,
#         right_index=True
#     )
    .rename_axis(["Variable"], axis=1)
)
t0[t0<1e-5] = 0

# %%
comm_groups = t0.index.get_level_values("Commodity group").unique()

fig, axes = plt.subplots(
    nrows=len(comm_groups), 
    ncols=1, 
    figsize=(10, 5*len(comm_groups)),
    gridspec_kw={"hspace": 0.3}
)

for index, comm_group in enumerate(comm_groups):
    t1 = t0.loc[comm_group]
    t1 = t1.rolling(5, min_periods=3, center=True, axis=0).mean()
    t1["EROEI"] = (
        t1["Calorie consumption"].div(
            t1["Fertiliser energy footprint"]
            + t1["Primary food energy footprint"]
            + t1["Procssed food energy footprint"]
        )
    )
    t1.columns = t1.columns.map(lambda x: f"{x} ({number_to_text(t1.loc[2020, x])})")
    cmap = dict(zip(t1.columns.values, sns.color_palette("tab10")))
    t2 = t1.div(t1.loc[1995, :]).replace([np.nan, np.inf, -np.inf], np.nan).stack().to_frame("Relative change").reset_index()
    ax = axes[index]
    sns.lineplot(data=t2, x="Year", y="Relative change", hue="Variable", ax=ax, legend="brief", palette=cmap)
    ax.legend(bbox_to_anchor=(1, 1), title="Variable (Value in 2020)")
    ax.set_title(comm_group)

fig.show()

# %% [markdown]
# ## Crop specific UN region

# %%
comm_group = "Sugar crops"
t0 = (
    df_filter.loc[
        df_filter.index.isin([
            "consumption",
            "primary",
            "processed",
            "fertiliser",
            "fertiliser_input",
            "biomass_production",
            "biomass_footprint"
        ], level="source")
    ]
    .groupby(["comm_group", "area"], axis=1).sum()
    .loc[:, comm_group]
    .groupby(["year", "direction", "source"], axis=0).sum()
    .stack()
    .reorder_levels(["direction", "source", "year", "area"])
    .droplevel("direction")
    .unstack("source")
    .rename({
        "biomass_production": "Biomass production",
        "consumption": "Calorie consumption",
        "fertiliser": "Fertiliser energy footprint",
        "fertiliser_input": "Fertiliser use footprint",
        "primary": "Primary food energy footprint",
        "processed": "Procssed food energy footprint",
        "biomass_footprint": "Biomass footprint"
    }, axis=1)
    .rename_axis(["Year", "Area"], axis=0)
    .rename(area_to_UN, axis=0, level="Area")
    .groupby(["Area", "Year"], axis=0).sum()
    .merge(
        un_pop_df.to_frame("Population"),
        how="left",
        left_index=True,
        right_index=True
    )
    .rename_axis(["Variable"], axis=1)
)


areas = t0.index.get_level_values("Area").unique()

fig, axes = plt.subplots(
    nrows=len(areas), 
    ncols=1, 
    figsize=(10, 5*len(areas)),
    gridspec_kw={"hspace": 0.3}
)

for index, area in enumerate(areas):
    t1 = t0.loc[area]
    #t1 = t1.rolling(5, min_periods=3, center=True, axis=0).mean()
    
    t1["EROEI"] = (
        t1["Calorie consumption"].div(
            t1["Fertiliser energy footprint"]
            + t1["Primary food energy footprint"]
            + t1["Procssed food energy footprint"]
        )
    )
    t1.columns = t1.columns.map(lambda x: f"{x} ({number_to_text(t1.loc[2020, x])})")
    cmap = dict(zip(t1.columns.values, sns.color_palette("tab10")))

    t2 = t1.div(t1.loc[1995, :]).stack().to_frame("Relative change").reset_index()
    cmap = dict(zip(t1.columns.values, sns.color_palette("tab10")))
    ax = axes[index]
    sns.lineplot(data=t2, x="Year", y="Relative change", hue="Variable", ax=ax, legend="brief", palette=cmap)
    ax.legend(bbox_to_anchor=(1, 1))
    ax.set_title(area)

fig.show()
# Southern Africa large increase in 2016 is due to large increase in the processed energy input in South Africa

# %% [markdown]
# # Paper plots

# %% [markdown]
# ### Figure 2

# %%
units = {
    'Biomass production': " Gt",
    'Calorie consumption': " EJ",
    'EROEI': "",
    "Employment in agriculture": " Mill.",
    "Energy footprint of agriculture sectors": " EJ",
    "Energy footprint of food processing sectors": " EJ",
    'Fertiliser energy footprint': " EJ",
    'External energy input': " EJ",
    #'Fertiliser use',
    "Net capital stock in agriculture": " Tril. $",
    'Population': " Bill.",
    "Land use": " Gha"
}
factor = {
    'Biomass production': 10e9,
    'Calorie consumption': 1e6,
    'EROEI': 1e0,
    "Employment in agriculture": 1e3,
    "Energy footprint of agriculture sectors": 1e6,
    "Energy footprint of food processing sectors": 1e6,
    'Fertiliser energy footprint': 1e6,
    #'Fertiliser use',
    'External energy input': 1e6,
    'Net capital stock in agriculture': 1e6,
    'Population': 1e9,
    "Land use": 1e9
}

sns.set_theme(style="whitegrid")
t1 = (
    df_filter.loc[
        df_filter.index.isin([
            "consumption",
            "primary",
            "processed",
            "fertiliser",
            #"fertiliser_input",
            "biomass_production"
        ], level="source")
    ]
    .groupby("area", axis=1).sum()
    .groupby(["year", "direction", "source"], axis=0).sum()
    .stack()
    .reorder_levels(["direction", "source", "year", "area"])
    .droplevel("direction")
    .unstack("source")
    .rename_axis(["Variable"], axis=1)
    .rename({
        "biomass_production": "Biomass production",
        "consumption": "Calorie consumption",
        "fertiliser": "Fertiliser energy footprint",
        #"fertiliser_input": "Fertiliser use",
        "primary": "Energy footprint of agriculture sectors",
        "processed": "Energy footprint of food processing sectors"
    }, axis=1)
    .rename_axis(["Year", "Area"], axis=0)
    .groupby(["Year"], axis=0).sum()
    
)

t1["External energy input"] = (
    t1["Fertiliser energy footprint"]
    + t1["Energy footprint of agriculture sectors"]
    + t1["Energy footprint of food processing sectors"]
)

t1["EROEI"] = (
    t1["Calorie consumption"].div(t1["External energy input"])
)
t1["Land use"] = (grazing_landuse + crop_landuse).rename_axis(["Year"])
t1["Population"] = global_pop_df
t1["Net capital stock in agriculture"] = investment_capitalstock_global
t1["Employment in agriculture"] = total_employment_global
variables = [
    "Population",
    "Net capital stock in agriculture",
    "Employment in agriculture",
    "External energy input",
    "Calorie consumption",
    "EROEI",
    "Land use"
]
sizes = dict(zip(
    variables,
    [1, 1, 1, 2, 2, 3]
))
t1 = t1.loc[:, variables]


t1.columns = (
    t1
    .columns
    .map(
        lambda x: f"{x} ({number_to_text(t1.loc[2019, x]/factor[x])}{units[x]})"
    )
)
t2 = t1.div(t1.loc[1995, :]).stack().to_frame("Relative change").reset_index()
fig, ax = plt.subplots(figsize=(15, 8))

t2_plot = t2[t2["Variable"].str.contains("Population")]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=2, color="grey", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=4)

t2_plot = t2[t2["Variable"].str.contains("Land", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=2, color="purple", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=5)

t2_plot = t2[t2["Variable"].str.contains("Net", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=2, color="orange", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=6)

t2_plot = t2[t2["Variable"].str.contains("Employment", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=2, color="b", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=7)

t2_plot = t2[t2["Variable"].str.contains("External", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=3, color="r", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=8)

t2_plot = t2[t2["Variable"].str.contains("Calorie", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=3, color="g", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=9)

t2_plot = t2[t2["Variable"].str.contains("EROEI", case=False)]
ax.plot(t2_plot["Year"], t2_plot["Relative change"], linewidth=4, color="k", linestyle=("-"), label=t2_plot.Variable.iloc[0], zorder=10)

leg = ax.legend(
    ncol=1,
    loc="upper left", 
    #bbox_to_anchor=[0.5, 1.1],
    title="Variable (Value in 2019)",
    fontsize="large",
    title_fontsize="large"
)
for legobj in leg.legend_handles:
    legobj.set_linewidth(5.0)
    
plt.setp(ax.spines.values(), color="k", linewidth=1.5)
ax.set_xlim(1995, 2020)
ax.set_xlabel("Year", size=18)
ax.set_ylabel("Relative change", size=18)
ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), fontsize=15)
ax.set_yticks(ax.get_yticks(), ax.get_yticklabels(), fontsize=15)
fig.show()

# %% [markdown]
# ### Figure 3
# %%
region_color_scheme = {
    'Northern America': (1.0, 0.4980392156862745, 0.054901960784313725),
    'Central America': (1.0, 0.7333333333333333, 0.47058823529411764),
    'Caribbean': (0.8392156862745098, 0.15294117647058825, 0.1568627450980392),
    'South America': (1.0, 0.596078431372549, 0.5882352941176471),
    
    'Northern Europe': (0.12156862745098039, 0.4666666666666667, 0.7058823529411765),
    'Western Europe': (0.6823529411764706, 0.7803921568627451, 0.9098039215686274),
    'Southern Europe': (0.09019607843137255, 0.7450980392156863, 0.8117647058823529),
    'Eastern Europe': (0.6196078431372549, 0.8549019607843137, 0.8980392156862745),
    
    'Western Asia': (0.5490196078431373, 0.33725490196078434, 0.29411764705882354),
    'Northern Africa': (0.7686274509803922, 0.611764705882353, 0.5803921568627451),
    
    'Eastern Africa': (0.17254901960784313, 0.6274509803921569, 0.17254901960784313),
    'Western Africa': (0.596078431372549, 0.8745098039215686, 0.5411764705882353),
    'Middle Africa': (0.8588235294117647, 0.8588235294117647, 0.5529411764705883),
    'Southern Africa': (0.7372549019607844, 0.7411764705882353, 0.13333333333333333),
    
    'Australia and New Zealand': (0.4980392156862745, 0.4980392156862745, 0.4980392156862745),
    'ROW': (0.7803921568627451, 0.7803921568627451, 0.7803921568627451),
    
    'Central Asia': (0.7725490196078432, 0.6901960784313725, 0.8352941176470589),
    'Eastern Asia': (0.5803921568627451, 0.403921568627451, 0.7411764705882353),
    'South-eastern Asia': (0.9686274509803922, 0.7137254901960784, 0.8235294117647058),
    'Southern Asia': (0.8901960784313725, 0.4666666666666667, 0.7607843137254902),    
}

# %%
five_year_agg = {
    1995: '1995-1999',
    1996: '1995-1999',
    1997: '1995-1999',
    1998: '1995-1999',
    1999: '1995-1999',
    2000: np.nan,
    2001: np.nan,
    2002: np.nan,
    2003: np.nan,
    2004: np.nan,
    2005: np.nan,
    2006: np.nan,
    2007: np.nan,
    2008: np.nan,
    2009: np.nan,
    2010: np.nan,
    2011: np.nan,
    2012: np.nan,
    2013: np.nan,
    2014: np.nan,
    2015: '2015-2019',
    2016: '2015-2019',
    2017: '2015-2019',
    2018: '2015-2019',
    2019: '2015-2019',
}
# %%
t1 = (
    macro_statistics_raw.loc[
        (macro_statistics_raw.index.isin(["Gross Domestic Product"], level="Item"))
        & (macro_statistics_raw.index.isin(["Value US$, 2015 prices"], level="Element"))
        # (macro_statistics_raw.index.isin(["Gross Domestic Product"], level="Item"))
    ]
    .groupby(["Year", "Area Code"]).sum()
)
ts_GDP = (
    t1[
        (~t1.index.get_level_values("Area Code").map(lambda x: type(x) == int).values)
        & (t1.index.get_level_values("Year") >= 1995) 
        & (t1.index.get_level_values("Year") <= 2019)
    ]
    .rename(five_year_agg, level="Year")
    .groupby(["Year", "Area Code"]).mean()
    .rename(lambda x: cc.convert(x, to="UNregion"), level="Area Code")
    .rename({"Polynesia": "ROW", "Micronesia": "ROW", "Melanesia": "ROW", "RoW": "ROW", "ROW": "ROW", "": "ROW"})
    .groupby(["Year", "Area Code"]).sum()
    .to_frame("GDP")
)

ts_POP = (
    pop_df[(pop_df["Year"] >= 1995) & ((pop_df["Year"] <= 2020))]
    .groupby(["Year", "UN_region"])["Population"].sum()
    .rename(five_year_agg, level="Year")
    .groupby(["Year", "UN_region"]).mean()
)

t1 = (
    df_filter
    .rename(five_year_agg, level="year")
    .rename(area_to_UN, level="area", axis=1)
    .groupby(["area"], axis=1).sum()
    .groupby(["direction", "source", "year"]).sum()
    #.reorder_levels([1, 2, 0])
)
ts_EROEI = t1.loc[("energy_output", "consumption")].div(t1.loc["energy_input"].groupby("year").sum()).stack()


ts_figure3 = (
    ts_EROEI
    .rename_axis(["Year", "Region"])
    .to_frame("EROEI")
    .reset_index()
    .merge(
        (
            (ts_POP)
            .rename_axis(["Year", "Region"])
            .to_frame("Population")
            .reset_index()
        ),
        on=["Year", "Region"],
        how="left"
    )
    .merge(
        (
            (ts_GDP*1e6)
            .rename_axis(["Year", "Region"])
            .reset_index()
        ),
        on=["Year", "Region"],
        how="left"
    )
)
ts_figure3["GDP per capita"] = ts_figure3["GDP"].div(ts_figure3["Population"])
ts_figure3["Colour"] = ts_figure3["Region"].map(region_color_scheme)
df_plot = ts_figure3.set_index(["Region", "Year"])
df_plot["Log10(EROEI)"] = np.log10(df_plot["EROEI"])
df_plot["Log10(GDP per capita)"] = np.log10(df_plot["GDP per capita"])
#df_plot = df_plot.sort_values(by="Population", ascending=False)

# %%
region_abbreviation = {
    'Australia and New Zealand': "O",
    'Caribbean': "C",
    'Central America': "C-Am",
    'Central Asia': "C-As",
    'Eastern Africa': "E-Af",
    'Eastern Asia': "E-As",
    'Eastern Europe': "E-Eu",
    'Middle Africa': "M-Af",
    'Northern Africa': "N-Af",
    'Northern America': "N-Am",
    'Northern Europe': "N-Eu",
    'ROW': "R",
    'South America': "S-Am",
    'South-eastern Asia': "SE-As",
    'Southern Africa': "S-Af",
    'Southern Asia': "S-As",
    'Southern Europe': "S-Eu",
    'Western Africa': "W-Af",
    'Western Asia': "W-As",
    'Western Europe': "W-Eu"
}

# %%

region_multiplier = {
    'Australia and New Zealand': {'x': 0.9, 'y': 1.02},
    'Caribbean': {'x': 0.9, 'y': 1},
    'Central America': {'x': 1.05, 'y': 0.91},
    'Central Asia': {'x': 0.82, 'y': 1},
    'Eastern Africa': {'x': 0.82, 'y': 1},
    'Eastern Asia': {'x': 0.9, 'y': 1.17},
    'Eastern Europe': {'x': 0.8, 'y': 1},
    'Middle Africa': {'x': 0.8, 'y': 1},
    'Northern Africa': {'x': 0.81, 'y': 1.01},
    'Northern America': {'x': 1, 'y': 0.86},
    'Northern Europe': {'x': 0.81, 'y': 0.95},
    'ROW': {'x': 1, 'y': 1.1},
    'South America': {'x': 0.83, 'y': 0.88},
    'South-eastern Asia': {'x': 1.05, 'y': 0.87},
    'Southern Africa': {'x': 0.83, 'y': 0.98},
    'Southern Asia': {'x': 0.75, 'y': 1},
    'Southern Europe': {'x': 0.92, 'y': 0.88},
    'Western Africa': {'x': 0.90, 'y': 0.87},
    'Western Asia': {'x': 0.79, 'y': 0.95},
    'Western Europe': {'x': 0.79, 'y': 1}
}

plot_regions = df_plot.groupby("Region")["Population"].mean().sort_values(ascending=False).index.values
x = "GDP per capita"
y = "EROEI"
start_period = "1995-1999"
end_period = "2015-2019"

bbox_props = dict(boxstyle="round,pad=0.3", fc="white", ec="k", alpha=0.7)
fig, ax = plt.subplots(figsize=(15, 8))
arrows = []
for region in plot_regions:
    t1 = df_plot.loc[region]
    label = f"{region} ({region_abbreviation[region]})"
    arrows.append(plt.annotate(
        "",
        xy=(t1.loc[end_period, x], t1.loc[end_period, y]),
        xytext=(t1.loc[start_period, x], t1.loc[start_period, y]),
        label=label,
        arrowprops=dict(
            arrowstyle="-|>,head_width=0.4,head_length=0.8,widthB=100",
            shrinkA=0,
            shrinkB=0,
            lw=1,
            facecolor=t1.loc[start_period, "Colour"],
            edgecolor="black",
            #color=t1.loc[start_period, "Colour"],
        )
    ))
    
    plt.annotate(
        region_abbreviation[region],
        xy=(t1.loc[start_period, x], t1.loc[start_period, y]),
        xytext=(
            t1.loc[start_period, x]
            *region_multiplier[region]["x"], t1.loc[start_period, y]*region_multiplier[region]["y"]),
        label=label,
        color="k",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=t1.loc[start_period, "Colour"], alpha=1, lw=2),
        fontsize=10,
        #alpha=0.1,
        zorder=5
    )
ax.scatter(x=df_plot[x], y=df_plot[y], c=df_plot["Colour"], s=df_plot["Population"]/1e6, zorder=2)
ax.legend([x.arrow_patch for x in arrows], [x.get_label() for x in arrows], ncol=4, title=None, edgecolor="k", loc="upper center", bbox_to_anchor=[0.5, 1.22], fontsize="medium")
ax.minorticks_on()
ax.set_yscale('log')
ax.set_xscale('log')
ax.set_ylabel("EROEI\n5-year averages", size=18)
ax.set_xlabel("GDP per capita\nUSD in 2015 prices", size=18)
ax.grid(axis="x", which="minor")
ax.grid(axis="y", which="minor")
#ax.tick_params(which='minor', size=4, width=1, direction="out", left=True, bottom=True, color="grey")
plt.setp(ax.spines.values(), color="k", linewidth=1.5)
xlims = ax.get_xlim()
ylims = ax.get_ylim()

ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), fontsize=15)
ax.set_yticks(ax.get_yticks(), ax.get_yticklabels(), fontsize=15)
ax.set_xlim(xlims)
ax.set_ylim(ylims)

fig.show()


# %% [markdown]
# Figure 4a

# %%
def figure4a_data(df_filter, years, area_mapper):
    t1 = (
        df_filter
        .rename(area_mapper, axis=1, level="area")
        .groupby("area", axis=1)
        .sum()
        .loc[years, :]
        .groupby(["direction", "source"])
        .sum()
    )
    t1_eroi = (
        t1.loc[("energy_output", "consumption")]
        .div(t1.loc["energy_input"].sum())
        .dropna()
        .to_frame("EROEI")
    )
    t1_pop = (
        pop_df.groupby(["Year", "UN_region"])["Population"].sum()
        .loc[years]
        .groupby("UN_region")
        .mean()
        .div(1e9)
    )
    t1_consumption_share = t1.loc["energy_output"].loc["consumption"]
    t1_consumption_share = t1_consumption_share.div(t1_consumption_share.sum())*100
    t2 = (
        df_filter
        .sum(axis=1)
        .loc[years]
        .groupby(["direction", "source"])
        .sum()
    )
    t2_eroi = t2.loc[("energy_output", "consumption")] / t2.loc["energy_input"].sum()

    t3 = (
        t1_eroi
        .merge(
            t1_pop.to_frame("Population"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_consumption_share.to_frame("Consumption share (%)"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .sort_values(by="EROEI", ascending=False)
        .rename_axis(["Region"])
        .reset_index()
    )
    t3["colour"] = t3["Region"].map(region_color_scheme)
    return t3, t2_eroi

# %%
def plot_figure4a(x, y, w, c, title, global_eroi, xlabel="World population (Bill.)"):
    xpos = []
    agg_width = []

    a = 0
    for i in range(len(w)):
        if i == 0:
            a+=w[i]

            xpos.append(w[i]/2)

        else:
            a += w[i]

            xpos.append(a - w[i]/2)


    fig, ax = plt.subplots(figsize=(15, 7))

    ax.bar(
        xpos,
        height=y,
        width=w,
        color=c,
        #alpha=0.95,
        label=x,
        edgecolor="k"
    )

    #plt.xticks(ticks = xpos, labels = w)

    ax.axhline(y=global_eroi, color="k")
    ax.text(x=0.8*w.sum(), y=global_eroi*1.05, s="Global EROEI", fontsize=15)
    #plt.axvline(x = 150)
    ax.legend(ncols=4, title="UN region", edgecolor="k", fontsize="medium", title_fontsize="medium")
    ax.set_ylabel("EROEI", size=18)
    ax.set_xlabel(xlabel, size=18)
    ax.set_title(title, size=18)
    ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), fontsize=15)
    ax.set_yticks(ax.get_yticks(), ax.get_yticklabels(), fontsize=15)
    plt.setp(ax.spines.values(), color="k", linewidth=1.5)
    ax.set_xlim((0, w.sum()))


    plt.show()

# %%
figure4a, global_eroi = figure4a_data(df_filter, np.arange(2015, 2020), area_to_UN)
figure4a_cmap = figure4a.set_index("Region")["colour"].to_dict()

plot_figure4a(figure4a["Region"], figure4a["EROEI"], figure4a["Population"], figure4a["colour"], "5-year average from 2015 to 2019", global_eroi)


# %%
def figure4b_data(df_filter, years, region=None):
    if region == None:
        t0 = df_filter.copy()
    else:
        t0 = (
            df_filter
            .rename(area_to_UN, level="area", axis=1)
            .groupby(["area", "item"], axis=1)
            .sum()
            .loc[:, [region]]
        )
    t1 = (
        t0
        .rename(product_groups, axis=1, level="item")
        .groupby(["item"], axis=1).sum()
        .loc[years, :]
        .groupby(["direction", "source"])
        .sum()
    )
    t1_energy_output = t1.loc[("energy_output", "consumption")]
    t1_energy_input = t1.loc["energy_input"].sum()
    t1_eroi = t1_energy_output.div(t1_energy_input)
    t1_consumption_share = t1_energy_output.div(t1_energy_output.sum()).sort_values()*100
    t1_input_shares = t1_energy_input.div(t1_energy_input.sum()).sort_values()*100

    t2 = (
        df_filter
        .sum(axis=1)
        .loc[years]
        .groupby(["direction", "source"])
        .sum()
    )
    t2_eroi = t2.loc[("energy_output", "consumption")] / t2.loc["energy_input"].sum()

    t1_regions = (
        df_filter
        .rename(product_groups, axis=1, level="item")
        .rename(area_to_UN, axis=1, level="area")
        .groupby(["area", "item"], axis=1).sum()
        .loc[years, :]
        .groupby(["direction", "source"])
        .sum()
    )
    t1_regions_eroi = (
        t1_regions.loc["energy_output"].sum(axis=0)
        .div(t1_regions.loc["energy_input"].sum(axis=0))
        .unstack("area")
    )
    t1_eroi_upper = t1_regions_eroi.max(axis=1)
    t1_eroi_lower = t1_regions_eroi.min(axis=1)

    t3 = (
        t1_eroi.to_frame("EROEI")
        .merge(
            t1_consumption_share.to_frame("Calorie share"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_energy_output.to_frame("Calories output"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_input_shares.to_frame("Energy input shares"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_energy_input.to_frame("Energy input"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_eroi_lower.to_frame("EROEI lower"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .merge(
            t1_eroi_upper.to_frame("EROEI upper"),
            left_index=True,
            right_index=True,
            how="left"
        )
        .sort_values(by="EROEI", ascending=False)
        .rename_axis(["Commodity group"])
        .reset_index()
    )
    t3["colour"] = t3["Commodity group"].map(dict(zip(t3["Commodity group"], list(sns.color_palette("tab10")))))
    return t3, t2_eroi

def plot_figure4b(x, y, w, c, upper, lower, title, xlabel, global_eroi, errorbar=False):
    xpos = []
    agg_width = []

    a = 0
    for i in range(len(w)):
        if i == 0:
            a+=w[i]

            xpos.append(w[i]/2)

        else:
            a += w[i]

            xpos.append(a - w[i]/2)


    fig, ax = plt.subplots(figsize=(15, 7))
    if errorbar:
        ax.bar(
            xpos,
            height=y,
            width=w,
            color=c,
            yerr=((y-lower)/10, (upper-y)/10),
            alpha=1,
            edgecolor="k",
            error_kw={
                "ecolor": "k",
                "alpha": 0.7
            },
            label=x,
        )
    else:
        ax.bar(
            xpos,
            height=y,
            width=w,
            color=c,
            edgecolor="k",
            alpha=1,
            label=x,
        )      

    #plt.xticks(ticks = xpos, labels = w)


    ax.axhline(y=global_eroi, color="k", )
    ax.text(x=0.85*w.sum(), y=global_eroi*1.05, s="Global EROEI", fontsize=15)
    #plt.axvline(x = 150)
    ax.legend(ncols=3, title="Product groups", edgecolor="k", fontsize="medium", title_fontsize="medium")
    ax.set_ylabel("EROEI", size=18)
    ax.set_xlabel(f"{xlabel} (%)", size=18)
    if title is not None:
        ax.set_title(title, size=18)
    plt.setp(ax.spines.values(), color="k", linewidth=1.5)
    ax.set_xticks(ax.get_xticks(), ax.get_xticklabels(), fontsize=15)
    ax.set_yticks(ax.get_yticks(), ax.get_yticklabels(), fontsize=15)
    ax.set_xlim((0, w.sum()))


    plt.show()


# %%
figure4b, global_eroi = figure4b_data(df_filter, np.arange(2015, 2020))
product_group_colour_map = figure4b.set_index(["Commodity group"])["colour"].to_dict()
plot_figure4b(
    x=figure4b["Commodity group"],
    y=figure4b["EROEI"],
    w=figure4b["Calorie share"],
    c=figure4b["colour"],
    upper=figure4b["EROEI upper"],
    lower=figure4b["EROEI lower"],
    title=None,
    xlabel="Calorie share",
    global_eroi=global_eroi,
    errorbar=True
)
plot_figure4b(
    x=figure4b["Commodity group"],
    y=figure4b["EROEI"],
    w=figure4b["Energy input shares"],
    c=figure4b["colour"],
    upper=figure4b["EROEI upper"],
    lower=figure4b["EROEI lower"],
    title=None,
    xlabel="Energy footprint share",
    global_eroi=global_eroi,
    errorbar=True
)

