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
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import fabio_functions
import country_converter as coco

# TODO: Include variable to automatically make flow or product version of results.

cc = coco.CountryConverter(include_obsolete=True)
years = np.arange(1995, 2021)

exclude_negatives = True
data_path = Path("../../data")

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
auxiliary_path = (
    data_path
    / "auxiliary"
)

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

fertiliser_path = (
    data_path
    / "interim"
    / "fertiliser"
    / "energy_footprint"
)


# %%
def read_region_footprint(save_path, iso_code):
    df = pd.read_feather(
        save_path / f"{iso_code}"
    )
    df.columns = df.columns.map(lambda x: tuple(x.split(";")))
    df = df.set_index([
        "area_output",
        "item_output",
        "comm_group_output",
        "group_output"
    ])
    return df


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


reader = fabio_functions.read(
    fabio_path,
    year=2005,
    version=1.2
)
regions = reader.regions.copy()
regions.loc[regions.iso3c == "CIV", "area"] = "Côte d'Ivoire"

regions = regions.rename({"iso3c": "area_ISO3"}, axis=1)

regions["UNregions"] = (
    regions["area_ISO3"]
    .apply(lambda x: cc.convert(x, src="ISO3", to="UNregion", not_found=None))
)
regions["region"] = (
    regions["area_ISO3"]
    .apply(lambda x: cc.convert(x, src="ISO3", to="EXIO3", not_found=None))
)

regions.loc[
    regions["area"] == "Belgium-Luxembourg", ["UNregions", "region"]
] = ["Western Europe", "BE"]
regions.loc[
    regions["area"] == "Czechoslovakia", ["UNregions", "region"]
] = ["Southern Europe", "HR"]
regions.loc[
    regions["area"] == "Yugoslav SFR", ["UNregions", "region"]
] = ["Southern Europe", "HR"]
regions.loc[
    regions["area"] == "Serbia and Montenegro", ["UNregions", "region"]
] = ["Southern Europe", "WE"]
regions.loc[
    regions["area"] == "RoW", ["UNregions", "region"]
] = ["ROW", "WA"]
regions.loc[
    regions["area"] == "Netherlands Antilles", ["UNregions", "region"]
] = ["Western Europe", "NL"]

UN_regions_mapper = (
    regions.groupby("UNregions")["area_ISO3"].agg(list).to_dict()
)
EXIOBASE_region_mapper = regions.set_index(["area"])["region"].to_dict()
area_to_UN = (
    regions
    .set_index("area")
    ["UNregions"]
    .to_dict()
)
iso3_mapper = regions.set_index(["area_ISO3"])["area"].to_dict()

# Use mappings from repository
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
for year in tqdm(years):
    # Load data
    # Global totals
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
    
    # Footprint data
    if exclude_negatives:
        biomass_footprint_path = (
            data_path
            / "interim"
            / "biomass_footprint"
            / "excl_negatives"
            / str(year)
        )
    else:
        biomass_footprint_path = (
            data_path
            / "interim"
            / "biomass_footprint"
            / "incl_negatives"
            / str(year)
        )
    biomass_footprints = []
    for index, region in enumerate(regions.area_ISO3.values):
        biomass_footprints.append(
            read_region_footprint(biomass_footprint_path, region)
            .groupby(level=[1, 2, 3], axis=1).sum()
        )

    biomass_footprint = pd.concat(
        biomass_footprints,
        keys=regions.area_ISO3.values,
        names=["area"],
        axis=1
    )
    biomass_footprint = (
        biomass_footprint
        .rename(iso3_mapper, axis=1, level="area")
    )

    # Upstream energy
    upstream_energy_path = (
        data_path
        / "interim"
        / "upstream_energy_use"
        / "unallocated"
        / f"{year}"
        / "target_perspective"
    )

    primary_upstream_energy = pd.read_csv(
        upstream_energy_path / "primary_crops_product.tsv",
        sep="\t",
        index_col=[0],
        header=[0, 1]
    ).replace([np.inf, np.nan, -np.inf], 0)

    processed_upstream_energy = pd.read_csv(
        upstream_energy_path / "processed_food_product.tsv",
        sep="\t",
        index_col=[0],
        header=[0, 1]
    ).replace([np.inf, np.nan, -np.inf], 0)

    # Fertiliser
    fertiliser_energy_footprint = pd.read_csv(
        fertiliser_path / "energy_footprint" / "all_years.tsv",
        sep="\t",
        index_col=0
    )

    fertiliser_energy_footprint = fertiliser_energy_footprint.loc[
        fertiliser_energy_footprint.year == year
    ]

    fertiliser_energy_footprint["area_output"] = (
        fertiliser_energy_footprint["iso3c"]
        .map(regions.set_index(["area_ISO3"])["area"].to_dict())
    )
    fertiliser_energy_footprint["energy_footprint"] = (
        fertiliser_energy_footprint["energy_footprint"]
        * 1e-6  # MJ to TJ
        * 1e3  # kg to tons
    )

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

    y_regions_cal_other_losses = (
        Y_cal
        .loc[
            :,
            ~Y_cal.columns.isin(final_demand_categories_cal, level="final demand")
        ]
        .groupby(["iso3c"], axis=1).sum()
        .droplevel(["area_code", "item_code", "comm_code"])
    ) * 4.1858e-6  # TJ / Mcal

    if exclude_negatives:
        y_regions_cal[y_regions_cal < 0] = 0

    # Prepare data
    # Fertiliser
    fertiliser_footprint = (
        fertiliser_energy_footprint
        .rename({
            # "country_name": "area_output",
            "group": "group_output",
            "comm_group": "comm_group_output",
            "fertiliser": "fertiliser_name",
            "fertiliser_use_corrected": "fertiliser_amount",
            "energy_footprint": "fertiliser_energy_item",
            "item": "item_output"
        }, axis=1)
        .set_index([
            "area_output",
            "group_output",
            "comm_group_output",
            "item_output",
            "fertiliser_name"
        ])
        .loc[:, ["fertiliser_amount", "fertiliser_energy_item"]]
    )

    F_fertiliser_input = fertiliser_footprint["fertiliser_amount"]
    F_fertiliser_energy = fertiliser_footprint["fertiliser_energy_item"]

    F_fertiliser_input = (
        F_fertiliser_input.unstack(biomass_production.index.names)
    )
    F_fertiliser_energy = (
        F_fertiliser_energy.unstack(biomass_production.index.names)
    )
    S_fertiliser_input = (
        F_fertiliser_input
        .div(biomass_production, axis=1)
        .replace([np.nan, np.inf, -np.inf], 0)
    )

    S_fertiliser_input_vector = (
        F_fertiliser_input.sum(axis=0)
        .div(biomass_production)
        .replace([np.nan, np.inf, -np.inf], 0)
    )

    S_fertiliser_energy = (
        F_fertiliser_energy
        .div(biomass_production, axis=1)
        .replace([np.nan, np.inf, -np.inf], 0)
    )
    S_fertiliser_energy_vector = (
        F_fertiliser_energy.sum(axis=0)
        .div(biomass_production)
        .replace([np.nan, np.inf, -np.inf], 0)
    )

    # Allocate upstream energy using biomass production
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

    primary_upstream_energy_unallocated = (
        primary_upstream_energy
        .stack(["region", "sector"])
        .to_frame("primary_upstream_energy")
        .reset_index()
        .pivot(
            columns=["region", "sector"],
            index=["IEA_product"],
            values="primary_upstream_energy"
        )
    )
    processed_upstream_energy_unallocated = (
        processed_upstream_energy
        .stack(["region", "sector"])
        .to_frame("primary_upstream_energy")
        .reset_index()
        .pivot(
            columns=["region", "sector"],
            index=["IEA_product"],
            values="primary_upstream_energy"
        )
    )

    F_primary_upstream = (
        primary_upstream_energy_unallocated
        .dot(
            biomass_production_mapped_shares
            .loc[primary_upstream_energy_unallocated.columns, :]
        )
    )

    F_processed_upstream = (
        processed_upstream_energy_unallocated
        .dot(
            biomass_production_mapped_shares
            .loc[processed_upstream_energy_unallocated.columns, :]
        )
    )

    S_primary_upstream = (
        F_primary_upstream
        .div(biomass_production, axis=1)
        .replace([np.nan, np.inf, -np.inf], 0)
    )
    S_primary_upstream_vector = (
        F_primary_upstream.sum(axis=0)
        .div(biomass_production)
        .replace([np.nan, np.inf, -np.inf], 0)
    )

    S_processed_upstream = (
        F_processed_upstream
        .div(biomass_production, axis=1)
        .replace([np.nan, np.inf, -np.inf], 0)
    )
    S_processed_upstream_vector = (
        F_processed_upstream.sum(axis=0)
        .div(biomass_production)
        .replace([np.nan, np.inf, -np.inf], 0)
    )

    # Calculate footprints
    upstream_primary_footprint = S_primary_upstream.dot(biomass_footprint)
    upstream_processed_footprint = S_processed_upstream.dot(biomass_footprint)
    upstream_fertiliser_footprint = (
        S_fertiliser_energy
        .loc[:, biomass_footprint.index]
        .dot(biomass_footprint)
    )
    fertiliser_input_footprint = (
        S_fertiliser_input
        .loc[:, biomass_footprint.index]
        .dot(biomass_footprint)
    )

    upstream_primary_footprint_source = (
        biomass_footprint.mul(S_primary_upstream_vector, axis=0)
    )
    upstream_processed_footprint_source = (
        biomass_footprint.mul(S_processed_upstream_vector, axis=0)
    )
    fertiliser_input_footprint_source = (
        biomass_footprint.mul(
            S_fertiliser_input_vector.loc[biomass_footprint.index],
            axis=0
        )
    )
    fertiliser_energy_footprint_source = (
        biomass_footprint.mul(
            S_fertiliser_energy_vector.loc[biomass_footprint.index],
            axis=0
        )
    )

    energy_inputs = pd.concat([
        upstream_primary_footprint,
        upstream_processed_footprint,
        upstream_fertiliser_footprint
    ], axis=0, keys=["primary", "processed", "fertiliser"], names=["source"])

    y_global = (
        y_regions_cal
        .groupby(["item", "comm_group", "group"])
        .sum()
        .rename_axis(["area"], axis=1)
        .rename(iso3_mapper, axis=1)
        .stack()
        .reorder_levels(["area", "item", "comm_group", "group"])
    )

    y_global_other_losses = (
        y_regions_cal_other_losses
        .groupby(["item", "comm_group", "group"])
        .sum()
        .rename_axis(["area"], axis=1)
        .rename(iso3_mapper, axis=1)
        .stack()
        .reorder_levels(["area", "item", "comm_group", "group"])
    )

    energy_outputs = pd.concat(
        [
            y_global.to_frame("consumption").T,
            y_global_other_losses.to_frame("other_losses").T
        ],
        axis=0,
        keys=["consumption", "other_losses"],
        names=["source"]
    )

    biomass_production_result = pd.concat(
        [
            biomass_production
            .rename_axis(energy_inputs.columns.names)
            .to_frame("biomass_production")
            .T
        ], axis=0, keys=["biomass_production"], names=["source"]
    )

    fertiliser_input_footprint_result = (
        pd.concat(
            [fertiliser_input_footprint],
            keys=["fertiliser_input"],
            names=["source"],
            axis=0
        )
    )

    other_results = pd.concat(
        [
            fertiliser_input_footprint,
            (
                biomass_production
                .rename_axis(energy_inputs.columns.names)
                .to_frame("biomass_production").T
            ),
            biomass_footprint.groupby("group_output").sum()
        ],
        keys=["fertiliser_input", "biomass_production", "biomass_footprint"],
        names=["source"],
        axis=0
    )

    results = (
        pd.concat([
            energy_outputs,
            energy_inputs,
            other_results,
            # biomass_output_result,
        ], axis=0, keys=[
            "energy_output",
            "energy_input",
            "other",
            # "biomass_output"
        ], names=["direction"])
        .rename_axis(["direction", "source", "other"], axis=0)
        .rename_axis(["area", "item", "comm_group", "group"], axis=1)
    )

    dom_biomass_footprint = domestic_split(biomass_footprint)
    dom_upstream_primary_footprint = (
        domestic_split(upstream_primary_footprint_source)
    )
    dom_upstream_processed_footprint = (
        domestic_split(upstream_processed_footprint_source)
    )
    dom_fertiliser_input_footprint = (
        domestic_split(fertiliser_input_footprint_source)
    )
    dom_fertiliser_energy_footprint = (
        domestic_split(fertiliser_energy_footprint_source)
    )

    results_source = (
        pd.concat([
            dom_biomass_footprint,
            dom_upstream_primary_footprint,
            dom_upstream_processed_footprint,
            dom_fertiliser_input_footprint,
            dom_fertiliser_energy_footprint
        ], keys=[
            "biomass",
            "primary_energy",
            "processed_energy",
            "fertiliser_input",
            "fertiliser_energy"
        ], names=["variable"])
    )


    # Save data
    if exclude_negatives:
        save_path = (
            data_path
            / "results"
            / "excl_negatives"
            / f"{year}"
        )

    else:
        save_path = (
            data_path
            / "results"
            / "incl_negatives"
            / f"{year}"
        )
    os.makedirs(save_path, exist_ok=True)
    results.to_csv(
        save_path / "results_product.tsv", sep="\t"
    )

    results_source.to_csv(
        save_path / "results_source_product.tsv", sep="\t"
    )
