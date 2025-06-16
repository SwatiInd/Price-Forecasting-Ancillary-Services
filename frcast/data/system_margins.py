from frcast.data.time_periods import get_query_periods, get_settlement_periods
from urllib.parse import quote

import pandas as pd
import requests


def fetch_forecasted_margins(start_date, end_date):
    '''
    Resamples forecasted negative reserve, high frequency requirements, and generation availability margins at EFA block

    Parameteters:
    start_date (str): start date (pd.Timestamp)
    end_date (str): end date string (pd.Timestamp)

    Retruns
    dataframe: A timeseries dataframe at EFA frequency
    '''
    query_start_date, query_end_date = get_query_periods(start_date, end_date)
    
    query = f'''SELECT * FROM "0eede912-8820-4c66-a58a-f7436d36b95f"
                WHERE 
                "Date" >= '{query_start_date}'
                AND "Date" <= '{query_end_date}'
                '''
    # URL encode query 
    url = f"https://api.neso.energy/api/3/action/datastore_search_sql?sql={quote(query)}"
    # Fetching data from URL
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data['result']['records'])
        # Standardizing column names and selecting relevant columns
        df.columns = [col.lower().replace(' ', '_').lstrip('_').replace('/', '') for col in df.columns]
        df = df[[ 'negative_reserve', 'high_freq_response_requirement', 
                'generation_availability_margin', 'generator_availability', 'opmr_total', 'national_surplus',
                'date', 'publish_date']]
        # selecting the latest available forecasting data
        df.publish_date = pd.to_datetime(df.publish_date)
        df.date = pd.to_datetime(df.date)
        df = df[(df['date']-df['publish_date'])=='2 days']
        df.set_index('date', inplace = True) 
        # Shifting index by -1 hour for EFA block starting from 23:00
        df.index = df.index-pd.Timedelta(hours = 1)
        # Resampling data by 

    except:
        df = pd.DataFrame()                      

    return df

def resample_margins(start_date, end_date):
    margins = fetch_forecasted_margins(start_date, end_date)
    margins_resampled = margins.resample('4h', origin = 'start').ffill()
    sp_start_time, sp_end_time = get_settlement_periods(start_date, end_date)
    margins_resampled = margins_resampled[(margins_resampled.index >= sp_start_time)&(margins_resampled.index <= sp_end_time)]
    margins_resampled.ffill(inplace = True)
    margins_resampled = margins_resampled[['high_freq_response_requirement',  'negative_reserve', 'generator_availability']]
    return margins_resampled

