def predict_from_best_model(X_pred, best_model):
    y_pred = best_model.predict(X_pred)
    return y_pred

