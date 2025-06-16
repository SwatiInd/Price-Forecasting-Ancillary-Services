from frcast.data.preprocessing import aggregate_sp_to_efa, get_eac_auction_volume_or_price
from frcast.data.time_periods import get_query_periods, get_settlement_periods
from urllib.parse import quote

import pandas as pd
import re
import requests

def fetch_br_price_and_volume(start_date, end_date):
    '''
    Collects balancing reserve (BR) data from NESO API and transforms into timeseries dataframe of price and volume
    Returns:
    clearing_price_fr (dataframe): A time series dataframe of BR clearing pricing at half-hour frequency (settlement period) 
    cleared_volume_fr (dataframe):  A time series dataframe of BR cleared volume at half-hour frequency (settlement period)
    '''
    # query_start_date = pd.to_datetime(start_date) - pd.Timedelta(days = 1) # SP starting from 23:00 
    # sp_start_time = pd.to_datetime(start_date) - pd.Timedelta(hours = 1)
    
    # end_date = pd.to_datetime(end_date)  + pd.Timedelta(days = 1) # Inclusive of the end date
    # sp_end_time = pd.to_datetime(end_date)- pd.Timedelta(hours = 1.5) # SP corresponding to EFA 6 is at 22:30
    query_start_date, query_end_date = get_query_periods(start_date, end_date)
    sp_start_time, sp_end_time = get_settlement_periods(start_date, end_date)
    query = f'''SELECT * FROM "1b3f2ee1-74a0-4939-a5a3-f01f19e663e4"
            WHERE "serviceType" = 'Balancing Reserve' 
            AND  "deliveryStart" >= '{query_start_date}'
            AND "deliveryStart" <= '{query_end_date}'
            '''
    # URL encode query
    url = f"https://api.neso.energy/api/3/action/datastore_search_sql?sql={quote(query)}"
    try:
        # Fetch data
        response = requests.get(url)
        data = response.json()
        br_auctions = pd.DataFrame(data['result']['records'])
        # Standardize column names
        br_auctions.columns = [re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower() for col in br_auctions.columns]    
        br_auctions.clearing_price = br_auctions.clearing_price.astype('float64')     
        br_auctions.cleared_volume = br_auctions.cleared_volume.astype('float64')                                              
    except:
        print('Historical FR clearing price and volume data is not fetched from API')
        clearing_price_br = pd.DataFrame()
        # cleared_volume_br = pd.DataFrame()
    # Data transformation 
    if(br_auctions.empty): #Data not fetched
        clearing_price_br, cleared_volume_br = pd.DataFrame(), pd.DataFrame()
    else: # Transform raw data to timeseries clearing prices
        clearing_price_br = get_eac_auction_volume_or_price(br_auctions, extracting_value='price')                                                                                                                
        # cleared_volume_br = get_eac_auction_volume_or_price(br_auctions, extracting_value='volume') 

        clearing_price_br = clearing_price_br[(clearing_price_br.index >= sp_start_time)
                                        &(clearing_price_br.index <= sp_end_time)] 

        # cleared_volume_br = cleared_volume_br[(cleared_volume_br.index >= sp_start_time)
        #                                 &(cleared_volume_br.index <= sp_end_time)]
        # print('Balancing reserve data is available from:', clearing_price_br.index.min(), 'to', clearing_price_br.index.max())
    return clearing_price_br

def aggregate_br_price(start_date, end_date):
    '''
    Retrieve Balancing Reserve (BR) market data for the given date range,
    then aggregate 30-minute settlement-period values to Electricity
    Forward Agreement (EFA) blocks, returning the minimum, maximum, and
    mean for each EFA block.

    Parameters
    ----------
    start_date : str or datetime-like
        Inclusive start of the query window. Accepts any
        pandas-parsable date (e.g. ``"2025-01-01"`` or ``pd.Timestamp``).
    end_date : str or datetime-like
        Inclusive end of the query window.

    Returns
    -------
    pandas.DataFrame
        Multi-indexed by ``["date", "efa_block"]`` with columns
        ``["min", "max", "mean"]`` representing the aggregated BR values
        across each of the six EFA blocks (EFA 1-6) for every day in the
        range.
    '''
    clearing_price_br = fetch_br_price_and_volume(start_date, end_date)
    br_pricing_agg_efa = aggregate_sp_to_efa(clearing_price_br, aggregation_parameters=['min', 'max', 'mean'])
    br_price_important_features = ['pbr_price_min', 'pbr_price_max', 'pbr_price_mean', #PBR price
                                    'nbr_price_min', 'nbr_price_max',  'nbr_price_mean',] #NBR price
    br_featured_df = br_pricing_agg_efa[br_price_important_features]
    return br_featured_df


