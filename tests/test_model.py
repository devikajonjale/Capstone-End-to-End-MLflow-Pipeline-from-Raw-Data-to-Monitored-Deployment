from src.features import prepare_frame
from src.stages.feature_engineering import build_features
from src.stages.train import build_estimator


def test_estimator_fits_and_predicts(sample_df, config):
    X, y = build_features(sample_df, config)
    est = build_estimator(config)
    est.fit(X, y)
    preds = est.predict(X)
    assert len(preds) == len(y)
    assert (preds > 0).all()


def test_serving_path_matches_training_columns(sample_df, config):
    X, y = build_features(sample_df, config)
    est = build_estimator(config)
    est.fit(X, y)
    # a single raw listing, as the API would receive it
    raw = sample_df.drop(columns=["Price_Lakhs"]).iloc[[0]]
    served = prepare_frame(raw, config)
    assert list(served.columns) == list(X.columns)
    assert est.predict(served).shape == (1,)
