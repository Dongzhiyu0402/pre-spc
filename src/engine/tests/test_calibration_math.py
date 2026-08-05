"""校准数学单元测试（防沉默逻辑错误：区间一致性、拟合正确性）。"""

from engine.calibration.linear import train_linear_model, predict_linear
from engine.calibration.rules import predict_by_rules
from engine.calibration.predict import predict
from engine.calibration.model_store import save_bucket_model, load_bucket_model, list_buckets
from engine.calibration.features import build_features


def test_linear_fit_perfect():
    # y = 2x + 1
    samples = [(x, 2 * x + 1) for x in [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]]
    model = train_linear_model(samples)
    assert abs(model.slope - 2.0) < 1e-6
    assert abs(model.intercept - 1.0) < 1e-6
    median, low, high = predict_linear(model, 10.0)
    assert abs(median - 21.0) < 1e-6
    assert low <= median <= high


def test_rules_interval_consistency():
    pred = predict_by_rules(40.0, platform="cnki", sample_count=0)
    assert pred.est_low <= pred.est_median <= pred.est_high
    assert 0 <= pred.est_median <= 100


def test_rules_sample_narrowing():
    pred0 = predict_by_rules(40.0, sample_count=0)
    pred30 = predict_by_rules(40.0, sample_count=30)
    assert (pred30.est_high - pred30.est_low) <= (pred0.est_high - pred0.est_low)


def test_predict_uses_linear_when_trained(tmp_path):
    samples = [(x, 0.8 * x + 5) for x in [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]]
    model = train_linear_model(samples)
    save_bucket_model(str(tmp_path), "cnki", "undergrad", model.to_dict())
    pred = predict(20.0, platform="cnki", paper_type="undergrad", model_dir=str(tmp_path))
    assert pred.model_status == "linear"
    assert pred.est_low <= pred.est_median <= pred.est_high


def test_model_store_roundtrip(tmp_path):
    save_bucket_model(str(tmp_path), "vip", "postgrad", {"kind": "linear", "slope": 0.9, "intercept": 2.0})
    bucket = load_bucket_model(str(tmp_path), "vip", "postgrad")
    assert bucket["slope"] == 0.9
    assert "vip_postgrad" in list_buckets(str(tmp_path))


def test_build_features():
    f = build_features(raw_score=50.0, max_run_len=20, segment_count=3, doc_length=100, platform="cnki")
    assert f.hit_ratio == 0.2
    d = f.as_dict()
    assert d["raw_score"] == 50.0
