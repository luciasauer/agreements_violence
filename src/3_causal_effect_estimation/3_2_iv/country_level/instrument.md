## Instrumental Variable: Country-level Panel


- I have to define each instrument used in the country-level panel for the IV estimation, and its logic to predict the treatment (ceasefire agreements implementation).
- Trade volume as weight could be improved considering the time dimension, cause now we are using the sum of trade volume over the whole period.

1 INSTRUMENTS RELATED TO INFLUENCE SCORES IN UN VOTING

- <code>influence_veto_past_12</code>: voting similarity to those in the security council, weighting by veto power.
- <code>influence_gdp_past_12</code>: voting similarity to those in the security council, weighting by gdp and friendship UN.

2 INSTRUMENTS RELATED TO PAST PEACE AGREEMENTS IN REGION, EXCLUDING OWN COUNTRY