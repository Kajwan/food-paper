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
import xmltodict
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from lxml import etree
import matplotlib.pyplot as plt
import country_converter as coco

cc = coco.CountryConverter()

# %%
server_path = Path("/home/kajwanr/indecol")

fertiliser_path = (
    server_path
    / "DATA"
    / "eroi_of_food"
    / "fertiliser"
)

# %%
def spold_to_xml(fertiliser_path):
    spold_files = os.listdir(fertiliser_path / "spold")
    os.makedirs(
        fertiliser_path
        / "xml"
        / "LCIA"
    )


    for spold_file in spold_files:
        if "Lcia" in spold_file:
            os.rename(
                fertiliser_path / "spold" / spold_file,
                fertiliser_path / "xml"/ "LCIA" / spold_file.replace("spold", "xml")
            )


def prepare_LCIA_data(fertiliser_path):
    xml_files = os.listdir(fertiliser_path / "xml" / "LCIA")

    list_of_rows = []
    for xml_file in tqdm(xml_files):
        root = etree.parse(fertiliser_path / "xml" / "LCIA" / xml_file)
        dict_file = xmltodict.parse(etree.tostring(root))

        row = {}

        row["region"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["activityDescription"]
            ["geography"]
            ["shortname"]
            ["#text"]
        )

        row["name"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["activityDescription"]
            ["activity"]
            ["activityName"]
            ["#text"]
        )

        row["timestamp"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["administrativeInformation"]
            ["fileAttributes"]
            ["@fileTimestamp"]
        )

        row["start_date"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["activityDescription"]
            ["timePeriod"]
            ["@startDate"]
        )

        row["end_date"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["activityDescription"]
            ["timePeriod"]
            ["@endDate"]
        )

        row["valid_for_period"] = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["activityDescription"]
            ["timePeriod"]
            ['@isDataValidForEntirePeriod']
        )

        impact_indicators = (
            dict_file
            ["ecoSpold"]
            ["childActivityDataset"]
            ["flowData"]
            ["impactIndicator"]
        )
        for indicator in impact_indicators:
            if indicator["impactMethodName"] == "Cumulative Energy Demand (CED)":
                row["cummulative_energy_demand"] = (
                    float(indicator["@amount"])
                )
                row["unit"] = (
                    indicator["unitName"]
                )
        list_of_rows.append(
            pd.Series(row)
        )

    fertiliser_df = pd.concat(list_of_rows, axis=1).T

    fertiliser_df["short_name"] = fertiliser_df.name.apply(lambda x: x.split(", as ")[-1])
    fertiliser_df["start_year"] = pd.DatetimeIndex(fertiliser_df["start_date"]).year
    fertiliser_df["region_ISO3"] = fertiliser_df.region.apply(lambda x: cc.convert(x, not_found="ROW"))
    fertiliser_df["region_name"] = fertiliser_df.region.apply(lambda x: cc.convert(x, not_found="ROW", to="name_short"))
    fertiliser_df["continent"] = fertiliser_df.region.apply(lambda x: cc.convert(x, not_found="ROW", to="continent"))
    fertiliser_df["subcontinent"] = fertiliser_df.region.apply(lambda x: cc.convert(x, not_found="ROW", to="UNregion"))

    return fertiliser_df


def plot_fertililser_distribution(fertiliser_df):
    # * Variation in fertiliser
    a = fertiliser_df.groupby("short_name").cummulative_energy_demand
    a.median()#.mul(fertiliser_consumption.values)
    a.std()

    c = (
        fertiliser_df[fertiliser_df.region_ISO3 == "ROW"]
        .groupby("short_name").cummulative_energy_demand.mean()
    )
    # ? Squeeze K2O data to a normal distribution?
    # d = np.random.normal(
    #     c.loc["K2O"], 
    #     11,
    #     size=len(fertiliser_df[fertiliser_df.short_name == "K2O"])
    # )

    fig, ax = plt.subplots()

    a.hist(ax=ax, alpha=0.7, legend=True)
    #ax.hist(d, label="K2O - Simulated", alpha=0.7, color="r")
    #ax.legend()
    ax.vlines(c, ymin=0, ymax=17.5, colors=["k", "k", "k"])
    fig.show()


def fertiliser_stat(consumption, fertiliser_df, fertiliser="P2O5"):
    fertiliser = "P2O5"
    b = (
        fertiliser_df
        .set_index(["short_name", "region_ISO3", "valid_for_period", "unit"])
        .loc[[fertiliser], "cummulative_energy_demand"]
    )
    print(b.sort_values(), "\n")

    print(f"[{fertiliser}] Max/min value", np.round(b.max()/b.min(), 2), "\n")

    print(
        "Shares by",
        consumption
        .groupby("item")
        .value
        .sum()
        .div(consumption.value.sum())
        .round(3)
        *100
    )


def fill_missing_region_values(x, region, subcontinent_mean, continent_mean):
    if x.energy_stressor == 0:
        try:
            return subcontinent_mean.loc[x.subcontinent, x.short_name]
        except KeyError:
            try:
                return continent_mean.loc[x.continent, x.short_name]
            except KeyError:
                if x.region_ISO3 == "SUN":
                     return region.loc["RUS", x.short_name]
                elif x.region_ISO3 == "BLX":
                     return region.loc["BEL", x.short_name]
                elif x.region_ISO3 == "CSK":
                     return region.loc["CZE", x.short_name]
                elif x.region_ISO3 == "YUG":
                     return region.loc["HRV", x.short_name]
                elif x.region_ISO3 == "SCG":
                     return region.loc["SRB", x.short_name]
                elif x.region_ISO3 == "SCG":
                     return region.loc["SRB", x.short_name]
                else:
                     return continent_mean.loc["ROW", x.short_name]
    else:
        return x.energy_stressor


def fill_missing_regions(fertiliser_df, fabio_regions):
    df = (
        fertiliser_df
        .loc[:, ["region_ISO3", "region_name", "continent", "subcontinent", "short_name", "cummulative_energy_demand"]]
    )

    df_region = (
        df
        .groupby(["short_name", "region_ISO3"])
        .cummulative_energy_demand
        .mean()
        .unstack(level="short_name")
    )

    df_subcontinent = (
        df
        .groupby(["short_name", "subcontinent"])
        .cummulative_energy_demand
        .mean()
        .to_frame("subcontinent_mean")
        .reset_index()
        .pivot(
            index="subcontinent",
            columns="short_name",
            values="subcontinent_mean"
        )
    )
    df_continent = (
        df
        .groupby(["short_name", "continent"])
        .cummulative_energy_demand
        .mean()
        .to_frame("continent_mean")
        .reset_index()
        .pivot(
            index="continent",
            columns="short_name",
            values="continent_mean"
        )
    )

    new_regions = [x for x in fabio_regions.iso3c.unique() if x not in df.region_ISO3.unique()]
    new_regions = pd.DataFrame(
        new_regions,
        columns=["region_ISO3"]
    )
    new_regions["continent"] = new_regions.region_ISO3.apply(lambda x: cc.convert(x, not_found=None, src="ISO3", to="continent"))
    new_regions["subcontinent"] = new_regions.region_ISO3.apply(lambda x: cc.convert(x, not_found=None, src="ISO3", to="UNregion"))

    df_filled = (
        pd.concat(
            [df, new_regions]
        )
        .pivot(
            index=["region_ISO3", "continent", "subcontinent"],
            columns="short_name",
            values="cummulative_energy_demand"
        )
        .dropna(how="all", axis=1)
        .fillna(0)
        .stack()
        .to_frame("energy_stressor")
        .reset_index()
    )
    # TODO: Use groupby.transform instead.
    df_filled["energy_stressor"] = (
        df_filled.apply(
            fill_missing_region_values,
            axis=1,
            **{
                "region": df_region,
                "subcontinent_mean": df_subcontinent,
                "continent_mean": df_continent
            }
        )
    )
    return df_filled


def fill_timeseries(
        df,
        data_year=2016,
        first_year=1980,
        last_year=2020,
        inefficiency=1.3,
        max_inefficiency=1.1,
    ):
    df_now = (
        df
        .loc[:, ["region_ISO3", "short_name", "energy_stressor"]]
        .pivot(
            index="short_name",
            columns="region_ISO3",
            values="energy_stressor"
        )
    )

    df_then = df_now.copy()
    df_then = (
        (df_then*inefficiency)
        .clip(
            df_now.min(axis=1),
            df_now.max(axis=1)*max_inefficiency,
            axis=0
        )
    )

    combined = (
        pd.concat(
            [df_then, df_now],
            keys=[first_year, data_year],
            names=["year"],
            axis=0
        )
        .unstack("short_name")
        .reorder_levels([-1, 0], axis=1)
        .sort_index(axis=1)
    )

    fill_out = pd.DataFrame(
        np.nan,
        index=np.arange(first_year, last_year+1),
        columns=combined.columns,
    )
    fill_out.index.names = ["year"]
    combined_filled = (
        combined
        .combine_first(fill_out)
        .astype(float)
        .interpolate(
            method="linear",
            limit_area="inside",
            axis=0
        )
        .interpolate(
            method="pad",
            axis=0
        )
    )

    return combined_filled


def calculate_energy_footprint(df, consumption):
    a = (
        df
        .stack(level=df.columns.names)
        .to_frame("energy_stressor")
        .reset_index()
        .rename(
            {
                "short_name": "fertiliser",
                "region_ISO3": "iso3c"
            },
            axis=1
        )
    )

    b = consumption.loc[
        :,
        [
            "year",
            "iso3c",
            "item",
            "comm_group",
            "group",
            "fertiliser",
            "fertiliser_use_corrected"
        ]
    ]
    c = b.merge(
        a,
        how="left",
        on=["year", "iso3c", "fertiliser"]
    )

    c["energy_footprint"] = c["fertiliser_use_corrected"].mul(c["energy_stressor"])

    return c


def compare_with_IO_data(
        server_path,
        df,
        year=2010
    ):
    upstream_path = (
        server_path
        / "DATA"
        / "eroi_of_food"
        / "upstream_energy_use"
        / "unallocated"
        / f"{year}"
        / "target_perspective"
    )

    upstream_incl = pd.read_csv(
        upstream_path / f"primary_crops_incl_fertiliser.tsv",
        sep="\t",
        index_col=[0],
        header=[0, 1]
    )

    upstream = pd.read_csv(
        upstream_path / f"primary_crops.tsv",
        sep="\t",
        index_col=[0],
        header=[0, 1]
    )

    io = (
        upstream_incl.sum().sum()
        - upstream.sum().sum()
    )

    lca = df[df.year == year]
    lca = (
        lca.energy_footprint.sum()
        * 1e-6  # MJ to TJ
        * 1e3  # kg to tons
    )

    print("Ecoinvent vs EXIOBASE:", lca/io)

# %%
