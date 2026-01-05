# Data Sources

Brief summary of inputs used to build the country-month panel in `data/output/country_level/country_panel.csv`, and the conflict-month panel in `data/output/conflict_level/conflict_panel.csv`

## Fatalities

- UCDP GED Global version 25.1 between 1989-01-01 and 2024-12-31 from https://ucdp.uu.se/downloads/.

Location: `data/input/ucdp/GEDEvent_v25_1.csv`

## Agreements

- Peace Agreement Dataset from PA-X v9, between 1990 and 2024. https://www.peaceagreements.org/

Location: `data/input/pax/pax_data_2144_agreements_v9_10.csv`

## Isocodes and Regions

- Country name, ISO3, region, subregion

Location: `data/input/isocodes/isocodes_appended.csv` 

# Control Variables

- <code>gdp_per_capita</code>: annual GDP pc (June) from World Bank https://data.worldbank.org/indicator/NY.GDP.PCAP.CD

Location: `data/input/gdp_pc/gdp_pc.csv`

It was linearly interpolated to monthly frequency, then log-transformed and normalized (by country) in the panel construction scripts.


## Instrumental Variables

### UN voting similarity

- UN Security Council Members Data by year (>= 1989): DPPA-SCMEMBERSHIP.csv https://psdata.un.org/dataset/DPPA-SCMembership

Location: `data/input/un/DPPA-SCMEMBERSHIP.csv`

- UNGA roll-call voting, Y/N/A votes for similarity measures (>= 1968).  https://digitallibrary.un.org/record/4060887?ln=en 

Location: `data/input/un/2025_9_19_ga_voting.csv` 

### Regional spillovers

- CEPII GeoDist: bilateral distances between countries by region/subregion. https://www.cepii.fr/cepii/en/bdd_modele/bdd_modele_item.asp?id=6

Location:  `data/input/distance/dist_cepii.xls`

We constructed conditional distance by region/subregion and inverses.

- CEPII BACI HS92 V202501: bilateral trade flows between countries by region/subregion for 1995-2023. https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37

Location: `data/input/trade/BACI_HS92_V202501/*.csv`

### External Support (SC at war)

- UCDP External Support (ESD), External support by UNSC members in conflicts at triad-level https://ucdp.uu.se/downloads/

Location: `data/input/external_support/ucdp-esd-ty-181.xlsx` 
