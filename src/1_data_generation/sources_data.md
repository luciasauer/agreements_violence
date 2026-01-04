# Fatalities

- UCDP GED Global version 25.1 between 1989-01-01 and 2024-12-31. https://ucdp.uu.se/downloads/

# Agreements

- Peace Agreement Dataset from PA-X v9, between 1990-01-01 and 2024-12-31. https://www.peaceagreements.org/

# Control Variables

- <code>gdp_per_capita</code>: World Bank https://data.worldbank.org/indicator/NY.GDP.PCAP.CD
- <code>population</code>: World Bank https://data.worldbank.org/indicator/SP.POP.TOTL

# Instrumental Variables

## **First Set of Instruments: UN General Assembly Voting Similarity**

- UN Security Council Members Data: DPPA-SCMEMBERSHIP.csv https://psdata.un.org/dataset/DPPA-SCMembership
- UNGA voting data: https://digitallibrary.un.org/record/4060887?ln=en

## **Second Set of Instruments: Regional Peace Agreement Spillovers**

Our second instrumental strategy exploits variation in peace agreement activity in other coun-
tries within the same region or subregion, excluding the focal country. 

- **Distances** between countries: CEPII GeoDist https://www.cepii.fr/cepii/en/bdd_modele/bdd_modele_item.asp?id=6
- **Trade volumes**: CEPII BACI HS92 (1995-2023) https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37

- UCDP External Support: at triad-level