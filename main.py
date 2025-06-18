import frcast
import pandas as pd

def main():
    '''Predicts DCL pricing for next day as delivery day 
    (EFA 1: 23:00 of today to EFA 6: 19:00 of the next day)'''
    # Collect train dataset for one-year back
    X, y = frcast.get_train_features_target_df()
    # Spliting into train (9 months data) and validation set (3 months data)
    splits = frcast.generate_time_series_splits(X,y, n_splits=4, test_size = 3*30*6)
    # Hyperparameters tuning
    optuna_study = frcast.run_xgb_optuna_tuning(X, y, n_trials=50)
    # Fit the best-model
    best_model = frcast.train_final_xgb_model_from_study(X, y, optuna_study)
    # Features dataset for the next day
    X_pred = frcast.get_prediction_features_df()
    # Prediction from the next day
    y_pred = best_model.predict(X_pred)
    y_pred = pd.Series(data = y_pred, index = X_pred.index)
    print("Predicted DCL Prices:")
    print(y_pred)
    
    return y

if __name__ == "__main__":
    main()