"""Tests for ML models: L1 Fall Detection and L2 Health Risk Prediction."""

import pytest
import numpy as np

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    generate_singapore_seniors,
    generate_caregivers,
    generate_accelerometer_sequence,
    extract_features,
    FallDetector,
    HealthRiskPredictor,
    RiskLevel,
)


class TestExtractFeatures:
    def test_output_shape(self):
        buffer = generate_accelerometer_sequence("Normal Walk")
        features = extract_features(buffer)
        assert features.shape == (18,)

    def test_output_is_numpy_array(self):
        buffer = generate_accelerometer_sequence("Normal Walk")
        features = extract_features(buffer)
        assert isinstance(features, np.ndarray)

    def test_features_are_finite(self):
        buffer = generate_accelerometer_sequence("Normal Walk")
        features = extract_features(buffer)
        assert np.all(np.isfinite(features))

    def test_consistent_across_sequence_types(self):
        for seq_type in ["Normal Walk", "Shuffle Gait", "Fall"]:
            buffer = generate_accelerometer_sequence(seq_type)
            features = extract_features(buffer)
            assert features.shape == (18,)
            assert np.all(np.isfinite(features))


class TestFallDetector:
    @pytest.fixture
    def detector(self):
        return FallDetector()

    def test_detector_initialization(self, detector):
        assert detector.model is not None

    def test_classify_returns_dict(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        assert isinstance(result, dict)

    def test_classify_contains_required_keys(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        assert "label" in result
        assert "class_id" in result
        assert "confidence" in result
        assert "all_probabilities" in result

    def test_classify_valid_labels(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        assert result["label"] in ["Normal Walk", "Shuffle Gait", "Fall"]

    def test_classify_confidence_range(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_classify_all_probabilities_sum_to_one(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        total = sum(result["all_probabilities"].values())
        assert abs(total - 1.0) < 1e-6

    def test_classify_normal_walk(self, detector):
        buffer = generate_accelerometer_sequence("Normal Walk")
        result = detector.classify(buffer)
        assert result["label"] == "Normal Walk"

    def test_classify_fall(self, detector):
        buffer = generate_accelerometer_sequence("Fall")
        result = detector.classify(buffer)
        assert result["label"] == "Fall"

    def test_classify_shuffle_gait(self, detector):
        buffer = generate_accelerometer_sequence("Shuffle Gait")
        result = detector.classify(buffer)
        assert result["label"] == "Shuffle Gait"


class TestHealthRiskPredictor:
    @pytest.fixture
    def seniors(self):
        return generate_singapore_seniors()

    @pytest.fixture
    def predictor(self, seniors):
        return HealthRiskPredictor(seniors)

    def test_predictor_initialization(self, predictor):
        assert predictor.model is not None
        assert predictor.explainer is not None

    def test_predict_returns_risk_assessment(self, predictor, seniors):
        senior = seniors[0]
        result = predictor.predict(senior)
        assert isinstance(result.senior_id, str)
        assert isinstance(result.senior_name, str)
        assert isinstance(result.risk_level, RiskLevel)

    def test_predict_risk_level_values(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            assert result.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH]

    def test_predict_risk_score_range(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            assert 0.0 <= result.risk_score <= 1.5

    def test_predict_probabilities_sum(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            total = sum(result.probabilities.values())
            assert abs(total - 1.0) < 1e-6

    def test_predict_top_3_factors_count(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            assert len(result.top_3_factors) == 3

    def test_predict_factors_have_valid_direction(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            for factor in result.top_3_factors:
                assert factor.direction in ["increases_risk", "decreases_risk"]

    def test_predict_factors_have_feature_names(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            for factor in result.top_3_factors:
                assert factor.feature_name in [
                    "age", "resting_hr", "spo2", "sleep_hours",
                    "step_count", "prev_hospitalisations", "frailty_index"
                ]

    def test_predict_factors_have_shap_values(self, predictor, seniors):
        for senior in seniors:
            result = predictor.predict(senior)
            for factor in result.top_3_factors:
                assert isinstance(factor.shap_value, float)

    def test_clinical_risk_label_high_frailty(self, predictor):
        seniors = generate_singapore_seniors()
        high_frailty = [s for s in seniors if s.features.frailty_index > 0.6][0]
        result = predictor.predict(high_frailty)
        assert result.risk_level == RiskLevel.HIGH

    def test_clinical_risk_label_low_spo2(self, predictor):
        seniors = generate_singapore_seniors()
        low_spo2 = [s for s in seniors if s.features.spo2 < 92][0]
        result = predictor.predict(low_spo2)
        assert result.risk_level == RiskLevel.HIGH
