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
from functions import (
    prepare_LCIA_data,
    fill_missing_regions,
    fill_timeseries,
    calculate_energy_footprint,
)
import country_converter as coco

cc = coco.CountryConverter(include_obsolete=False)

# %%
data_path = Path("../../data")

fabio_path = (
    data_path
    / "FABIO"
    / "biomass"
)

fertiliser_path = (
    data_path
    / "interim"
    / "fertiliser"
)

os.makedirs(fertiliser_path / "energy_footprint", exist_ok=True)

# %%
fabio_regions = pd.read_csv(
    fabio_path / "regions.csv"
)
fabio_items = pd.read_csv(
    fabio_path / "items.csv"
)

# %%
consumption = pd.read_csv(
    fertiliser_path / "use" / "fertiliser_use_reduced.csv",
    sep="\t",
    header=[0],
    index_col=[0]
)


# %%
fertiliser_df = prepare_LCIA_data(fertiliser_path)

# %%
# * Prepare LCI data
df = fill_missing_regions(fertiliser_df, fabio_regions)

# %%
df = fill_timeseries(
    df,
    data_year=2016,
    first_year=1980,
    last_year=2020,
    inefficiency=1.3,
    max_inefficiency=1.1
)

# %%
df = calculate_energy_footprint(df, consumption)

# %%
df.to_csv(
    fertiliser_path / "energy_footprint" / "all_years.tsv",
    sep="\t"
)
