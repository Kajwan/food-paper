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
from tqdm import tqdm
from joblib import Parallel, delayed
from functions import eroi_of_food_upstream

# %%
years = np.arange(1995, 2021)
data_path = Path("../../data")
include_fertiliser = True
run_parallel = True
n_cpus = 26

# %%
# ? Include "Tobacco" and "Wool, silk worm cocoons"?
agriculture_products = [
    'Paddy rice',
    'Wheat',
    'Cereal grains nec',
    'Vegetables, fruit, nuts',
    'Oil seeds',
    'Sugar cane, sugar beet',
    'Plant-based fibers',
    'Crops nec',
    'Cattle',
    'Pigs',
    'Poultry',
    'Meat animals nec',
    'Animal products nec',
    'Raw milk',
    'Fish and other fishing products; services incidental of fishing (05)'
]

# ? Should "Chemical and fertilizer minerals, ..." be included?
fertiliser_products = [
    'Chemical and fertilizer minerals, salt and other mining and quarrying products n.e.c.',
    'N-fertiliser',
    'P- and other fertiliser'
]

processed_products = [
    'Products of meat cattle',
    'Products of meat pigs',
    'Products of meat poultry',
    'Meat products nec',
    'products of Vegetable oils and fats',
    'Dairy products',
    'Processed rice',
    'Sugar',
    'Food products nec',
    'Beverages',
    'Fish products'
]

# %%
if __name__ == "__main__":

    if run_parallel:
        (
            Parallel(n_jobs=n_cpus)
            (delayed(eroi_of_food_upstream)(year, **kwargs)
            for (
                year,
                kwargs,
            ) in zip(
                years,
                [{
                    "data_path": data_path,
                    "include_fertiliser": include_fertiliser,
                    "agriculture_products": agriculture_products,
                    "fertiliser_products": fertiliser_products,
                    "processed_products": processed_products
                }]*len(years)
            ))
        )
    else:
        for year in tqdm(years):
            eroi_of_food_upstream(
                year=year,
                data_path=data_path,
                include_fertiliser=include_fertiliser,
                agriculture_products=agriculture_products,
                fertiliser_products=fertiliser_products,
                processed_products=processed_products
            )

# %%
