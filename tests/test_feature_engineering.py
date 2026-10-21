from src.features import DERIVED_FEATURES, add_derived_features
from src.stages.feature_engineering import build_features


def test_derived_features_added(sample_df):
    out = add_derived_features(sample_df)
    for col in DERIVED_FEATURES:
        assert col in out.columns
    assert (out["rooms_total"] == sample_df["Bedrooms"] + sample_df["Bathrooms"]).all()


def test_build_features_shape(sample_df, config):
    X, y = build_features(sample_df, config)
    assert X.shape[0] == sample_df.shape[0]
    assert len(y) == sample_df.shape[0]
    assert "rooms_total" in X.columns
    assert "House_ID" not in X.columns


def test_target_removed_from_features(sample_df, config):
    X, _ = build_features(sample_df, config)
    assert config["feature_engineering"]["target"] not in X.columns
