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

years = np.arange(1995, 2021)

data_path = Path("../../data")
exclude_negatives = False
final_demand_categories = [
    "balancing",
    "food",
    "losses",
    "other",
    "stock_addition",
    "tourist",
    "unspecified"
]

# %%
fabio_path = (
    data_path
    / "raw"
    / "FABIO"
    / "biomass"
)


# %%
def save_region_footprint(df, save_path, iso_code):
    df = (
        df
        .droplevel(["area_code", "item_code", "comm_code"], axis=0)
        .droplevel(["area_code", "item_code", "comm_code"], axis=1)
        .rename_axis([
            "area_output",
            "item_output",
            "comm_group_output",
            "group_output"
            ], axis=0
        )
        .rename_axis([
            "area_input",
            "item_input",
            "comm_group_input",
            "group_input"
            ], axis=1
        )
        .reset_index()
    )
    df.columns = df.columns.map(";".join)
    df.to_feather(save_path / f"{iso_code}")


# %%
A_issues_list = []
for year_save in years:
    reader = fabio_functions.read(
        path=fabio_path,
        year=year_save,
        version=1.2
    )

    Z = reader.Z(version="mass")
    Y = reader.Y()

    Y_iso3c = (
        Y
        .loc[
            :,
            Y.columns.isin(final_demand_categories, level="final demand")
        ]
        .groupby(["iso3c"], axis=1).sum()
    )
    if exclude_negatives:
        Y_iso3c[Y_iso3c < 0] = 0

    x = Y_iso3c.sum(axis=1) + Z.sum(axis=1)
    A = Z.div(x, axis=1).replace([np.nan, np.inf, -np.inf], 0)
    A_issue = A.loc[np.diag(A >= 1), np.diag(A >= 1)]
    A_issues = (
        pd.concat(
            [
                pd.Series(
                    np.diag(A_issue),
                    index=A_issue.index
                ).to_frame("A_diagonal_value")
            ], keys=[year_save], names=["year"])
    )
    A_issues_list.append(A_issues)
    A_modified = A.copy()
    for issue in A_issue.index:
        A_modified.loc[issue, issue] = 1-1e-10
    I = pd.DataFrame(
        np.diag(np.ones(len(A))),
        index=A.index,
        columns=A.columns
    )
    L = pd.DataFrame(
        np.linalg.inv((I-A_modified)),
        index=A_modified.index,
        columns=A_modified.index
    )

    if exclude_negatives:
        L[L < 0] = 0

    # Saving L and Y for future use
    if exclude_negatives:
        L.to_csv(
            fabio_path / f"L_{year_save}_mass_excl_negatives.tsv",
            sep="\t"
        )
        Y_iso3c.to_csv(
            fabio_path / f"Y_iso3c_{year_save}_excl_negatives.tsv",
            sep="\t"
        )
    else:
        L.to_csv(
            fabio_path / f"L_{year_save}_mass_incl_negatives.tsv",
            sep="\t"
        )
        Y_iso3c.to_csv(
            fabio_path / f"Y_iso3c_{year_save}_incl_negatives.tsv",
            sep="\t"
        )

    iso_codes = Y.columns.get_level_values("iso3c").unique()
    for index_region, iso_code in tqdm(enumerate(iso_codes), desc=f"{year_save}:"):
        Y_iso = Y_iso3c.loc[
            :,
            iso_code
        ]
        x_footprint_region = L.mul(Y_iso, axis=1)
        if exclude_negatives:
            save_path = (
                data_path
                / "interim"
                / "biomass_footprint"
                / "excl_negatives"
                / str(year_save)
            )
        else:
            save_path = (
                data_path
                / "interim"
                / "biomass_footprint"
                / "incl_negatives"
                / str(year_save)
            )
        os.makedirs(save_path, exist_ok=True)
        save_region_footprint(x_footprint_region, save_path, iso_code)
