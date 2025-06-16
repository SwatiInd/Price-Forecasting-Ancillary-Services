from frcast.data.time_periods import get_efa_index
import pandas as pd

def aggregate_sp_to_efa(df: pd.DataFrame,
                            aggregation_parameters: list, 
                            freq = '4h'):
        '''
        aggregates half-hourly data  to four-hourly for parameters in the list

        Parameters:
        df (dataframe): A dataframe with timeseries index
        aggregation_parameters (list): A list containing all required parameters to be aggregated, (e.g.: ['min', 'max'])
        freq (str): Frequency for which data to be aggregated 
                    default: 4h for EFA block duration

        Returns:
        dataframe: A timeseries dataframe of all aggregated_parameters at freq
        '''
        agg_df = df.copy()
        agg_df = agg_df.resample(freq, origin = 'start').agg(aggregation_parameters)
        if(isinstance(agg_df.columns, pd.MultiIndex)): # multiindex if df has one more than one columns
            agg_df.columns = ['_'.join(col).lower() for col in agg_df.columns]
        else:
            parameter = df.columns.tolist()[0]
            agg_df.columns = [parameter+ '_'+ col for col in agg_df.column]
        # print('The aggregated data for is from', agg_df.index.min(), 'to', agg_df.index.max())
        return agg_df

def get_eac_auction_volume_or_price(eac_auction_df: pd.DataFrame, extracting_value: str):                                   
    '''
    Transforms raw auction dataframe to clearing price time series

    Parameters:
    eac_auction_df (dataframe): A dataframe of auctioned results
    extracting_value (str): It must be ['volume', 'price'] for cleared volume and clearing price, respectively.
    
    Output:
    Dataframe: Timeseries for extracting value of the service type
    '''
    service_stacked_df = eac_auction_df.copy()
    # Converting from string -> utc -> 'London' -> Naive timezone 
    # 2025-04-09T22:00:00 -> 2025-04-09 22:00:00 -> 2025-04-09 22:00:00+01:00 -> 2025-04-09 23:00:00
    service_stacked_df.delivery_start = pd.to_datetime(service_stacked_df.delivery_start, utc = True).dt.tz_convert('Europe/London').dt.tz_localize(None, nonexistent='shift_forward')
    service_stacked_df.delivery_end = pd.to_datetime(service_stacked_df.delivery_end, utc = True).dt.tz_convert('Europe/London').dt.tz_localize(None, nonexistent='shift_forward')

    service_stacked_df.index = service_stacked_df.delivery_start
    # response_df.head()
    start_time, end_time = service_stacked_df.index.min(), service_stacked_df.index.max()
    # print(service_type, 'service data is for the period from', start_time, 'to', end_time)  
    index_columns = ['delivery_start', 'auction_product']
    if(extracting_value == 'volume'):
        extracting_column = ['cleared_volume']
    elif(extracting_value == 'price'):
        extracting_column = ['clearing_price']
    else:
        extracting_column = []
        print('Input of extracting value is different than volume/price')
    if(len(extracting_column)==0):
        unstacked_df = pd.DataFrame()
    else:
        df_indexed =  service_stacked_df[index_columns + extracting_column].set_index(index_columns)
        # df_indexed.drop_duplicates(inplace=True, keep='first') # Duplicate indexes can occur sometime
        df_indexed = df_indexed[~df_indexed.index.duplicated(keep='first')]
        unstacked_df = df_indexed.unstack() # Mutliindex dataframe with level 1 -> clearing_price and level 2 -> services (DCL, DCH)
        unstacked_df.columns = unstacked_df.columns.get_level_values(1)
        unstacked_df = unstacked_df.rename_axis('delivery_start')
        unstacked_df.sort_index(inplace = True)
        unstacked_df.columns = [(col+'_'+extracting_value).lower() for col in unstacked_df.columns]
    return unstacked_df

def create_temporal_features_df(start_date, end_date, temporal_features):
    '''Builds a dataframe of temporal features 

    Return
    ------
    dataframe
        A dataframe of the same index as of output series and values of time features
    '''
    # efa_start_time = pd.to_datetime(start_date) - pd.Timedelta(hours = 1) # EFA 1 starts at 23:00 of the previous day
    # efa_end_time = pd.to_datetime(end_date) + pd.Timedelta(hours = 19) # EFA ends at 19:00 of the day
    efa_index = get_efa_index(start_date, end_date)
    temporal_features_df = pd.DataFrame(index = efa_index, 
                                        columns = temporal_features,
                                        )
    if('hour' in temporal_features):
        temporal_features_df.loc[:, 'hour'] = efa_index.hour
    
    if('day' in temporal_features):
        temporal_features_df.loc[:, 'day'] = efa_index.day

    if('month' in temporal_features):
        temporal_features_df.loc[:, 'month'] = efa_index.month    
    
    if('weekday' in temporal_features):
        temporal_features_df.loc[:, 'weekday'] = efa_index.weekday # Monday ->0, Sunday -> 6
        # based on weekday (0, 1, 2, 3, 4) working day -> 0 , weekend (5, 6) ->1 
    if('working day' in temporal_features):
        temporal_features_df.loc[:, 'weekday'] = efa_index.weekday # Monday ->0, Sunday -> 6
        temporal_features_df .loc[:, 'working day'] = temporal_features_df.weekday.apply(lambda x:0 if x<5 else 1)
        if('weekday' not in temporal_features):
            temporal_features_df.drop('weekday', axis = 1, inplace = True)
    temporal_features_df = temporal_features_df.astype('int64')
    return temporal_features_df

