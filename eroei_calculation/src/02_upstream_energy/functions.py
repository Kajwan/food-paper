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
from pathlib import Path
import numpy as np

# TODO: add save path as argument
# TODO: add function documentation
# TODO: add input to change between product or flow version of energy data. 


def upstream_impact(
    A: pd.DataFrame,
    Y: pd.DataFrame,
    S: pd.DataFrame,
    target_sectors: list = [],
    cut_sectors: list = [],
    remove_negative_demand: bool = False
):
    # Extracting a list with the names of sectors not target or cut.
    all_sectors = A.index.get_level_values("sector")
    other_sectors = (
        all_sectors
        .drop(cut_sectors)
        .drop(target_sectors)
        .values
    )

    # Cut sectors from economy by setting them to zero in A, Y, and S.
    A_modified = (
        A
        .drop(cut_sectors, axis=0, level=1)
        .drop(cut_sectors, axis=1, level=1)
    )
    Y_modified = (
        Y
        .drop(cut_sectors, axis=0, level=1)
        .drop("Exports: Total (fob)", axis=1, level=1)
    )
    if remove_negative_demand:
        Y_modified[Y_modified < 0] = 0

    S_modified = (
        S
        .drop(cut_sectors, axis=1, level=1)
    )

    # Calculate modified L
    I = pd.DataFrame(
        np.eye(len(A_modified)),
        index=A_modified.index,
        columns=A_modified.columns,
    )
    L_modified = pd.DataFrame(
        np.linalg.pinv(I-A_modified),
        index=A_modified.index,
        columns=A_modified.columns,
    )

    # Define all, but the L_other_other matrix
    L_all_target = (
        L_modified
        .drop(other_sectors, axis=1, level="sector")
    )
    Y_target_all = (
        Y_modified
        .drop(other_sectors, axis=0, level="sector")
    )
    A_target_other = (
        A_modified
        .drop(other_sectors, axis=0, level="sector")
        .drop(target_sectors, axis=1, level="sector")
    )
    Y_other_all = (
        Y_modified
        .drop(target_sectors, axis=0, level="sector")
    )

    A_other_other = (
        A_modified
        .drop(target_sectors, axis=0, level="sector")
        .drop(target_sectors, axis=1, level="sector")
    )

    # Calculate modified L for other sectors
    I_other_other = pd.DataFrame(
        np.eye(len(A_other_other)),
        index=A_other_other.index,
        columns=A_other_other.columns,
    )
    L_other_other = pd.DataFrame(
        np.linalg.pinv(I_other_other-A_other_other),
        index=A_other_other.index,
        columns=A_other_other.columns,
    )

    # Calculate demands
    indirect_demand = (
        A_target_other.dot(L_other_other.dot(Y_other_all))
    )
    direct_demand = (
        Y_target_all
    )
    total_demand = (
        direct_demand + indirect_demand
    )

    # Calculate upstream production for producer perspective
    upstream_production = (
        L_all_target
        .dot(total_demand)
    )

    # Diagonalise for target and producer perspective
    total_demand_diag = pd.DataFrame(
        np.diag(total_demand.sum(axis=1)),
        index=total_demand.index,
        columns=total_demand.index
    )
    upstream_production_diag = pd.DataFrame(
        np.diag(upstream_production.sum(axis=1)),
        index=upstream_production.index,
        columns=upstream_production.index
    )

    # Calculate upstream impact
    final_consumer_perspective = (
        S_modified
        .dot(
            L_all_target
            .dot(total_demand)
        )
    )
    target_perspective = (
        S_modified
        .dot(
            L_all_target
            .dot(total_demand_diag)
        )
    )
    producer_perspective = (
        S_modified
        .dot(upstream_production_diag)
    )

    results = {
        "Final consumer perspective": final_consumer_perspective,
        "Target perspective": target_perspective,
        "Producer perspective": producer_perspective,
        "Indirect demand": indirect_demand,
        "Direct demand": direct_demand,
        "Upstream production": upstream_production
    }

    return results


def eroi_of_food_upstream(
    year,
    data_path,
    include_fertiliser=True,
    agriculture_products=[],
    fertiliser_products=[],
    processed_products=[],
):

    MRIOT_path = (
        data_path
        / "EXIOBASE"
        / "IOT_txt"
        / "pxp"
        / f"IOT_{year}_pxp"
    )

    energy_extension_path = (
        data_path
        / "EXIOBASE"
        / "Extensions"
        / "energy"
        / "pxp"
        / f"IOT_{year}_pxp"
    )

    A = pd.read_csv(
        MRIOT_path / "A.txt",
        sep="\t",
        index_col=[0, 1],
        header=[0, 1]
    )

    Y = pd.read_csv(
        MRIOT_path / "Y.txt",
        sep="\t",
        index_col=[0, 1],
        header=[0, 1]
    )

    x = pd.read_csv(
        MRIOT_path / "x.txt",
        sep="\t",
        index_col=[0, 1],
        header=[0]
    ).loc[:, "indout"]

    F = pd.read_csv(
        energy_extension_path / "net_energy_use.tsv",
        sep="\t",
        index_col=[0, 1],
        header=[0, 1]
    )

    F_agg = F.groupby(by=["IEA_product"], axis=0).sum()

    S = F_agg.div(x, axis=1).replace([np.nan, np.inf, -np.inf], 0)


    if include_fertiliser:
        primary_production = upstream_impact(
            A,
            Y,
            S,
            target_sectors=agriculture_products,
            remove_negative_demand=False
        )

        processed_production = upstream_impact(
            A,
            Y,
            S,
            target_sectors=processed_products,
            cut_sectors=agriculture_products,
            remove_negative_demand=False
        )
        suffix = "_incl_fertiliser"

    else:
        primary_production = upstream_impact(
            A,
            Y,
            S,
            target_sectors=agriculture_products,
            cut_sectors=fertiliser_products,
            remove_negative_demand=False
        )

        processed_production = upstream_impact(
            A,
            Y,
            S,
            target_sectors=processed_products,
            cut_sectors=agriculture_products + fertiliser_products,
            remove_negative_demand=False
        )

        suffix = ""
    
    save_path = (
        data_path
        / "interim"
        / "upstream_energy_use"
        / "unallocated"
        / f"{year}"
        / "target_perspective"
    )
    os.makedirs(save_path, exist_ok=True)

    (
        primary_production["Target perspective"]
        .groupby(level="IEA_product")
        .sum()
        .to_csv(
            save_path / f"primary_crops_product{suffix}.tsv",
            sep="\t",
        )
    )

    (
        processed_production["Target perspective"]
        .groupby(level="IEA_product")
        .sum()
        .to_csv(
            save_path / f"processed_food_product{suffix}.tsv",
            sep="\t"
        )
    )
