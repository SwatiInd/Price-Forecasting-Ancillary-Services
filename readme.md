### NESO Data Sources 

#### Operational Planning Margin Requirements
[NESO: Planning Margins](https://www.neso.energy/data-portal/daily-opmr)
[Operation Planning Margin Analysis](https://github.com/SwatiInd/UK-Power-Analysis/blob/main/Operational_planning_margin.ipynb)

#### Balancing Reserve (BR) Prices
 - Datasource: [NESO: BR Auctions Results] (https://www.neso.energy/data-portal/eac-br-auction-results)
 - Resample: from half-hourly aggregated to four-hourly maximum, minimum, and mean prices. Both positve and negative balance reserve have strong dependence on 'DCL' pricing. As BR is auctioned at 08:15 while FR is at 14:00. Therefore, BR price is considered as a price signal for FR forecast.

#### Historic Demand Forecast
- Datasource: [NESO: Demand Forecast](https://www.neso.energy/data-portal/1-day-ahead-demand-forecast/historic_day_ahead_demand_forecasts)
- From cardinal points, half-hourly forecast is interpoloated and then resampled to four-hourly min, max, and mean values. 

#### Frequency-response: historical prices
- Datasource: [NESO: FR Auction Results](https://www.neso.energy/data-portal/eac-auction-results)
- EAC auction results consist of quick reserve (QR), dynamic containment (DC), dynamic moderate (DM), and dynamic regulation (DR) price and volume. 
- Autocorrelation: Correlation of the present value to previous 7-days values are studied. 
- Cross-correlation: Correlation of the present value to the last 7-days are determined. 


## Modeling
- XGB model, 
- Dataset one year before the forecasting day
- Train (9-months) and validation (3-months) datasets
- Hyperparameter tuning by Optuna
- Best model is further fitted for one year data 




