# Energy Input and Food Output: The Energy Imbalance Across Regional Agrifood Systems
Code for the publication in PNAS NEXUS.

This code is only shared for documentation purposes and will not be maintained.
No environment.yaml file is provided, so one needs to manually install each Python package.

A few points:
* The fabio_fertilizer part of the code should be run before the eroei_calculation code.
* To create the results at full level of detail, one needs access to the detailed energy accounts of EXIOBASE. These can be using the code shared here: https://github.com/Kajwan/EXIOBASE-energy-accounts, which requires a license to the World Extended Energy Balances published by the IEA.
* 02_upstream_energy/functions.py script needs to be manually changed to make the "IEA flow" version of the tables.
* 05/analyse_results/main.py script is intended to be run as a interactive script for analysis. 