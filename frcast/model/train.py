
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit

import mlflow
import numpy as np
import optuna
import pandas as pd
import xgboost as xgb


def generate_time_series_splits(X, y, n_splits=3, test_size=3*30*6):
    """
    Generate time series cross-validation splits with a fixed test set size.

    This function uses sklearn's TimeSeriesSplit to create sequential train/validation splits 
    for time series forecasting, ensuring that future data is never used to predict the past.

    Parameters:
        X (pd.DataFrame or np.ndarray): Feature matrix.
        y (pd.Series or np.ndarray): Target vector.
        n_splits (int): Number of splits (folds) to generate.
        test_size (int): Number of samples in each validation (test) fold.

    Returns:
        list of tuples: A list of (train_index, val_index) pairs for each fold.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
    return list(tscv.split(X, y))


def evaluate_xgb_trial(trial, X, y, splits):
    """
    Evaluate a set of XGBoost hyperparameters within an Optuna trial using time series cross-validation.

    Parameters:
        trial (optuna.trial.Trial): The Optuna trial object to suggest hyperparameters.
        X (pd.DataFrame): Feature matrix for training and validation.
        y (pd.Series): Target variable.
        splits (list of tuples): Precomputed time series train/validation indices.

    Returns:
        float: Mean cross-validated MAE (mean absolute error) for the given trial's parameters.
    """
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 0, 5),
        'reg_alpha': trial.suggest_float('reg_alpha', 0, 5),
        'reg_lambda': trial.suggest_float('reg_lambda', 0, 5),
        'random_state': 42
    }

    scores = []

    for train_idx, val_idx in splits:
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train, 
                  eval_set=[(X_val, y_val)],
                  verbose=False)

        preds = model.predict(X_val)
        score = mean_absolute_error(y_val, preds)
        scores.append(score)

    return np.mean(scores)

def run_xgb_optuna_tuning(X, y, n_trials=50):
    """
    Run hyperparameter optimization for an XGBoost model using Optuna with time series cross-validation.

    This function performs hyperparameter tuning using Optuna's Bayesian optimization framework.
    It evaluates each trial with time series splits and returns the full Optuna study object.

    Parameters:
        X (pd.DataFrame): Feature matrix for model training.
        y (pd.Series): Target variable.
        n_trials (int): Number of Optuna trials to run.

    Returns:
        optuna.study.Study: The Optuna study object containing all trial results.
    """
    splits = generate_time_series_splits(X, y)
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    study = optuna.create_study(direction='minimize')
    study.optimize(lambda trial: evaluate_xgb_trial(trial, X, y, splits),
                   n_trials=n_trials, show_progress_bar=False)
    
    # print('Minimum MAE:', study.best_value)
    return study

def train_final_xgb_model_from_study(X, y, study):
    """
    Train a final XGBoost model using the best hyperparameters from an Optuna study.

    This function extracts the best trial from the Optuna study, instantiates an XGBoost regressor,
    logs the final model parameters and validation MAE to MLflow, and fits the model on the full dataset.

    Parameters:
        X (pd.DataFrame): Full feature matrix for training.
        y (pd.Series): Target variable.
        study (optuna.study.Study): Completed Optuna study with best trial.

    Returns:
        xgboost.XGBRegressor: The trained XGBoost model with optimal hyperparameters.
    """
    best_params = study.best_trial.params
    best_model = xgb.XGBRegressor(**best_params)
    
    with mlflow.start_run(run_name="xgb_fit_best_model"):
        mlflow.log_metric("mean_cv_mae", study.best_value)
        mlflow.log_params(best_params)
    
    best_model.fit(X, y)
    return best_model
