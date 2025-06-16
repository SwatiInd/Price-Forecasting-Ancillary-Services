from frcast.data.preprocessing import aggregate_sp_to_efa
from frcast.data.time_periods import get_query_periods, get_settlement_periods
from urllib.parse import quote

import pandas as pd
import requests


def fetch_demand_forecast(start_date, end_date):
    '''Return half-hourly demand data inclusive start and end date'''
    query_start_date, query_end_date = get_query_periods(start_date, end_date)
    sp_start_time, sp_end_time = get_settlement_periods(start_date, end_date)
    query = f'''SELECT * FROM "9847e7bb-986e-49be-8138-717b25933fbb"
    WHERE "TARGETDATE" >= '{query_start_date}' AND "TARGETDATE" <= '{query_end_date}'
    '''
    # URL encode query
    url = f"https://api.neso.energy/api/3/action/datastore_search_sql?sql={quote(query)}"

    # Fetch data
    try:
        response = requests.get(url)
        data = response.json()
        demand_forecast = pd.DataFrame(data['result']['records'])
        demand_forecast.columns = [col.lower().lstrip('_') for col in demand_forecast.columns]

        # Determines the coordinal start time in datetime format
        demand_forecast.cp_st_time = demand_forecast.cp_st_time.astype('int64')
        demand_forecast['hour'] = demand_forecast['cp_st_time']//100
        demand_forecast['minutes'] = demand_forecast['cp_st_time']%100
        demand_forecast['start_time'] = (pd.to_datetime(demand_forecast['targetdate']) 
                                        + pd.to_timedelta(demand_forecast['hour'], unit = 'h') 
                                        + pd.to_timedelta(demand_forecast['minutes'], unit = 'm'))
        # Set start time as index and keep only last forecast for duplicated index
        demand_forecast.set_index('start_time', inplace = True)
        demand_forecast = demand_forecast[~demand_forecast.index.duplicated(keep='last')]
        # Interploate data at 30 minutes freq
        demand_forecast = demand_forecast['forecastdemand'].resample('30min').interpolate(method='quadratic')
        demand_forecast = demand_forecast[(demand_forecast.index >= sp_start_time)
                                        &(demand_forecast.index <= sp_end_time)]
        demand_forecast = pd.DataFrame(demand_forecast)
    except:
        demand_forecasat = pd.DataFrame()
        print('Demand forecast data is not fetched')

    return demand_forecast

def aggregate_demand(start_date, end_date):
    demand_forecast = fetch_demand_forecast(start_date, end_date)
    demand_features_df = aggregate_sp_to_efa(demand_forecast, ['min', 'max', 'mean'])
    return demand_features_df

