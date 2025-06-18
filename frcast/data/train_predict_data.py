from frcast.data.system_margins import resample_margins
from frcast.data.system_demand import aggregate_demand
from frcast.data.br_price import aggregate_br_price
from frcast.data.fr_prices import create_lag_shifted_df, get_historical_fr_price
from frcast.data.preprocessing import create_temporal_features_df
import pandas as pd

def get_train_features_target_df(train_end_date=None):
    """
    Retrieve the model train features as a DataFrame for one year

    If no train_end_date, the function defaults to the last 12 months
    ending at today's date. Note that FR-EAC feature data is only available from 
    2024-03-13 onwards, and the start date will be adjusted accordingly.

    Parameters
    ----------
    start_date : str or pd.Timestamp, optional
        Start date for the feature extraction period. Default is None.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing all model input features for one year.
    """
    if(train_end_date is None):
        train_end_date = pd.Timestamp.now().normalize()
    else:
        train_end_date = pd.Timestamp(train_end_date)
    
    train_start_date = train_end_date - pd.Timedelta(days = 365)
    # FR-EAC data is only available at given API from 2024-03-13
    if(train_start_date <= pd.Timestamp('2024-03-13')):
        train_start_date = pd.Timestamp('2024-03-13')
    
    margins_resampled = resample_margins(train_start_date, train_end_date)
    demand_agg = aggregate_demand(train_start_date, train_end_date)
    br_agg = aggregate_br_price(train_start_date, train_end_date)

    parameters_lags = {'dcl_price': [6, 12], 'drl_price': [6, 12]}
    lag_shifted_df = create_lag_shifted_df(train_start_date, train_end_date, parameters_lags)

    temporal_features = [ 'month', 'working day']
    temporal_features_df = create_temporal_features_df(train_start_date, train_end_date, temporal_features)

    X_train = pd.concat([margins_resampled, demand_agg, br_agg, lag_shifted_df, temporal_features_df], axis = 1)
    y = get_historical_fr_price(train_start_date, train_end_date)
    y_train = y['dcl_price']
    return X_train, y_train

def get_prediction_features_df(prediction_date=None):
    """
    Retrieve the model test features as a DataFrame for the specified date range.

    This function is intended for generating test-time input features (e.g., for prediction) for one-day only (test_date).

    Parameters
    ----------
    start_date : str or pd.Timestamp, optional
        Start date for the feature extraction period. Defaults to today's date if not provided.
    end_date : str or pd.Timestamp, optional
        End date for the feature extraction period. Defaults to today's date if not provided.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing model input features for the specified test period.
    """
    if(prediction_date is None):
        prediction_date = pd.Timestamp.now().normalize() + pd.Timedelta(days = 1)
    else:
        prediction_date = pd.Timestamp(prediction_date)

    # test_date = test_date - pd.Timedelta(days = 1)
    
    margins_resampled = resample_margins(prediction_date, prediction_date)
    demand_agg = aggregate_demand(prediction_date, prediction_date)
    br_agg = aggregate_br_price(prediction_date, prediction_date)

    parameters_lags = {'dcl_price': [6, 12], 'drl_price': [6, 12]}
    lag_shifted_df = create_lag_shifted_df(prediction_date, prediction_date, parameters_lags)

    temporal_features = [ 'month', 'working day']
    temporal_features_df = create_temporal_features_df(prediction_date, prediction_date, temporal_features)

    X_pred = pd.concat([margins_resampled, demand_agg, br_agg, lag_shifted_df, temporal_features_df], axis = 1)
    return X_pred



    

