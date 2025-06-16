from frcast.data.preprocessing import get_eac_auction_volume_or_price
from frcast.data.time_periods import get_query_periods, get_settlement_periods, get_efa_index
from urllib.parse import quote

import pandas as pd
import re
import requests


def get_historical_fr_price(fr_from: str, fr_to: str):
    '''
    Collects frequency response data from NESO API and transforms into timeseries dataframe of price and volume
    
    Parameters:
    fr_from (str): starting date of data collection (inclusive)
    fr_to (str): end date of data collection (inclusive)

    Returns:
    clearing_price_fr (dataframe): A time series dataframe of FR clearing pricing at four-hour frequency (EFA block wise) 
    cleared_volume_fr (dataframe):  A time series dataframe of FR cleared volume at four-hour frequency (EFA block wise)
    '''
    # query_start_date = pd.to_datetime(start_date) - pd.Timedelta(days = 1) # to collect data of EFA 1 of the start date
    # efa_start_time = pd.to_datetime(start_date)-pd.Timedelta(hours = 1) # EFA 1 starts at 23:00 of the previous day
    
    # end_date = pd.to_datetime(end_date) + pd.Timedelta(days = 1) # To be inclusive of the end date
    # efa_end_time = pd.to_datetime(end_date) - pd.Timedelta(hours = 5)  # EFA ends at 19:00 of the day
    fr_start_date = pd.to_datetime(fr_from) - pd.Timedelta(days = 1)
    fr_end_date = pd.to_datetime(fr_to) + pd.Timedelta(days = 1)

    fr_efa_start_time = pd.to_datetime(fr_from) - pd.Timedelta(hours = 1)
    fr_efa_end_time = pd.to_datetime(fr_to) + pd.Timedelta(hours = 19)
    query = f'''SELECT * FROM "596f29ac-0387-4ba4-a6d3-95c243140707"
            WHERE "serviceType" = 'Response' 
            AND  "deliveryStart" >= '{fr_start_date}'
            AND "deliveryStart" <= '{fr_end_date}'
            '''
            
    # URL encode query
    url = f"https://api.neso.energy/api/3/action/datastore_search_sql?sql={quote(query)}"
    # Data collection from NESO API
    try: # Fetch data
        response = requests.get(url)
        data = response.json()
        fr_auctions = pd.DataFrame(data['result']['records'])
        # Standardize column names
        fr_auctions.columns = [re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower() for col in fr_auctions.columns]
        fr_auctions.clearing_price = fr_auctions.clearing_price.astype('float64')
        # fr_auctions.cleared_volume = fr_auctions.cleared_volume.astype('float64')  
    except: 
        print('Historical FR clearing price and volume data is not fetched from API')
        fr_auctions = pd.DataFrame()
    # Data transformation 
    if(fr_auctions.empty): #Data not fetched
        clearing_price_fr = pd.DataFrame()
    else: 
        # Transform raw data to timeseries clearing prices
        clearing_price_fr = get_eac_auction_volume_or_price(fr_auctions, extracting_value='price')                                                                                                                
        # cleared_volume_fr = get_eac_auction_volume_or_price(fr_auctions, extracting_value='volume')  
        clearing_price_fr = clearing_price_fr[(clearing_price_fr.index >= fr_efa_start_time)
                                            &(clearing_price_fr.index <= fr_efa_end_time)] 
        # cleared_volume_fr = cleared_volume_fr[(cleared_volume_fr.index >= fr_efa_start_time)
        #                                     &(cleared_volume_fr.index <= fr_efa_end_time)]                           
        # print('Frequency response is available from:', clearing_price_fr.index.min(), 'to', clearing_price_fr.index.max())
    return clearing_price_fr

def create_lag_shifted_df(start_date, end_date, parameters_lags):
    '''
    Concats series of an input series by defined lags

    Returns:
    A dataframe of same index of df with shifted lags of parameters
    '''
    efa_index = get_efa_index(start_date, end_date)
    # print(efa_index)
    # query_start_date, query_end_date = get_query_periods(start_date, end_date)
    lag_shifted_df = pd.DataFrame(index = efa_index)
    previous_days_date = pd.to_datetime(start_date) - pd.Timedelta(days = 2)
    end_date = pd.to_datetime(end_date) + pd.Timedelta(days = 1)
    previous_days_date = previous_days_date.strftime('%Y-%m-%d')
    clearing_price_fr = get_historical_fr_price(previous_days_date, end_date)
    series_index = clearing_price_fr.index
    # print(clearing_price_fr.index[0], clearing_price_fr.index[-1])
    for parameter, lags in parameters_lags.items():
        parameter_series = clearing_price_fr[parameter].copy()

        for lag in lags:
            shifted_index = series_index + pd.Timedelta(hours=4*lag) 
            shifted_series = pd.Series(data = parameter_series.values,
                                       index = shifted_index)
            lag_shifted_df.loc[:, parameter+'_lag_' +str(lag)] = shifted_series[efa_index]
    return lag_shifted_df


    

