"""Tests for data models and generation functions."""

import pytest
import numpy as np
from datetime import datetime

# Import from app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    Zone, Day, EventType, RiskBand, RiskLevel,
    Senior, SeniorFeatures, Caregiver, Event,
    SHAPFactor, RiskAssessment, SeniorAssignment, ScheduleAssignment, LogEntry,
    generate_singapore_seniors,
    generate_caregivers,
    generate_accelerometer_sequence,
    generate_preloaded_events,
)


class TestEnums:
    def test_zone_values(self):
        assert Zone.NORTH.value == "North"
        assert Zone.SOUTH.value == "South"
        assert Zone.EAST.value == "East"
        assert Zone.WEST.value == "West"
        assert Zone.CENTRAL.value == "Central"

    def test_day_values(self):
        assert Day.MON.value == "Monday"
        assert Day.FRI.value == "Friday"

    def test_event_type_values(self):
        assert EventType.FALL.value == "Fall Detected"
        assert EventType.SPO2_DROP.value == "SpO2 Drop"
        assert EventType.MISSED_MEDS.value == "Missed Medication"

    def test_risk_band_values(self):
        assert RiskBand.RED.value == "Red"
        assert RiskBand.AMBER.value == "Amber"
        assert RiskBand.GREEN.value == "Green"

    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "Low"
        assert RiskLevel.MEDIUM.value == "Medium"
        assert RiskLevel.HIGH.value == "High"


class TestSeniorFeatures:
    def test_valid_features(self):
        f = SeniorFeatures(
            age=75,
            resting_hr=72,
            spo2=97,
            sleep_hours=6.5,
            step_count=2000,
            prev_hospitalisations=1,
            frailty_index=0.35
        )
        assert f.age == 75
        assert f.resting_hr == 72
        assert f.spo2 == 97

    def test_frailty_index_range(self):
        f = SeniorFeatures(
            age=80, resting_hr=70, spo2=96, sleep_hours=7.0,
            step_count=3000, prev_hospitalisations=0, frailty_index=0.0
        )
        assert f.frailty_index == 0.0


class TestSenior:
    def test_senior_creation(self):
        f = SeniorFeatures(72, 85, 91, 6.0, 2500, 2, 0.45)
        senior = Senior(
            id="S01",
            name="Tan Poh Lek",
            age=78,
            zone=Zone.NORTH,
            care_needs=["Dementia", "Mobility Support"],
            care_hours=2.0,
            features=f,
            family_contact="+65 9123 4567",
            risk_band=RiskBand.RED
        )
        assert senior.id == "S01"
        assert senior.name == "Tan Poh Lek"
        assert senior.zone == Zone.NORTH
        assert senior.risk_band == RiskBand.RED

    def test_senior_default_risk_band(self):
        f = SeniorFeatures(72, 85, 91, 6.0, 2500, 2, 0.45)
        senior = Senior(
            id="S02",
            name="Test Senior",
            age=72,
            zone=Zone.SOUTH,
            care_needs=["Chronic Disease"],
            care_hours=2.0,
            features=f
        )
        assert senior.risk_band == RiskBand.GREEN


class TestCaregiver:
    def test_caregiver_creation(self):
        cg = Caregiver(
            id="CG01",
            name="Nurse Aileen Tan",
            certifications=["Nursing", "Dementia Care"],
            home_zone=Zone.NORTH,
            availability=[Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI],
            max_seniors_per_day=2,
            active=True
        )
        assert cg.id == "CG01"
        assert len(cg.certifications) == 2
        assert len(cg.availability) == 5

    def test_caregiver_default_active(self):
        cg = Caregiver(
            id="CG02",
            name="Nurse Bee Cheng",
            certifications=["Nursing"],
            home_zone=Zone.SOUTH,
            availability=[Day.MON]
        )
        assert cg.active is True


class TestEvent:
    def test_event_creation(self):
        event = Event(
            id="E1",
            senior_id="S01",
            senior_name="Tan Poh Lek",
            senior_age=78,
            event_type=EventType.FALL,
            timestamp=datetime.now(),
            risk_band=RiskBand.RED,
            confidence=0.91,
            metadata={"zone": "North"}
        )
        assert event.id == "E1"
        assert event.event_type == EventType.FALL
        assert event.risk_band == RiskBand.RED
        assert event.confidence == 0.91
        assert event.metadata["zone"] == "North"

    def test_event_default_processed(self):
        event = Event(
            id="E2",
            senior_id="S02",
            senior_name="Test",
            senior_age=75,
            event_type=EventType.SPO2_DROP,
            timestamp=datetime.now(),
            risk_band=RiskBand.AMBER
        )
        assert event.processed is False


class TestGenerateSingaporeSeniors:
    def test_returns_list(self):
        seniors = generate_singapore_seniors()
        assert isinstance(seniors, list)

    def test_returns_20_seniors(self):
        seniors = generate_singapore_seniors()
        assert len(seniors) == 20

    def test_all_have_valid_ids(self):
        seniors = generate_singapore_seniors()
        for s in seniors:
            assert s.id.startswith("S")
            assert len(s.id) == 3

    def test_all_have_names(self):
        seniors = generate_singapore_seniors()
        for s in seniors:
            assert len(s.name) > 0

    def test_all_have_valid_zones(self):
        seniors = generate_singapore_seniors()
        valid_zones = {Zone.NORTH, Zone.SOUTH, Zone.EAST, Zone.WEST, Zone.CENTRAL}
        for s in seniors:
            assert s.zone in valid_zones

    def test_all_have_features(self):
        seniors = generate_singapore_seniors()
        for s in seniors:
            assert isinstance(s.features, SeniorFeatures)

    def test_age_range(self):
        seniors = generate_singapore_seniors()
        for s in seniors:
            assert 65 <= s.age <= 90


class TestGenerateCaregivers:
    def test_returns_list(self):
        caregivers = generate_caregivers()
        assert isinstance(caregivers, list)

    def test_returns_5_caregivers(self):
        caregivers = generate_caregivers()
        assert len(caregivers) == 5

    def test_all_have_valid_ids(self):
        caregivers = generate_caregivers()
        for cg in caregivers:
            assert cg.id.startswith("CG")
            assert len(cg.id) == 4

    def test_all_have_availability(self):
        caregivers = generate_caregivers()
        for cg in caregivers:
            assert len(cg.availability) > 0


class TestGenerateAccelerometerSequence:
    def test_normal_walk_shape(self):
        seq = generate_accelerometer_sequence("Normal Walk")
        assert seq.shape == (150, 3)

    def test_shuffle_gait_shape(self):
        seq = generate_accelerometer_sequence("Shuffle Gait")
        assert seq.shape == (150, 3)

    def test_fall_shape(self):
        seq = generate_accelerometer_sequence("Fall")
        assert seq.shape == (150, 3)

    def test_custom_samples(self):
        seq = generate_accelerometer_sequence("Normal Walk", n_samples=300)
        assert seq.shape == (300, 3)

    def test_returns_numpy_array(self):
        seq = generate_accelerometer_sequence("Normal Walk")
        assert isinstance(seq, np.ndarray)

    def test_values_are_finite(self):
        seq = generate_accelerometer_sequence("Normal Walk")
        assert np.all(np.isfinite(seq))

    def test_unknown_type_defaults_to_normal(self):
        seq = generate_accelerometer_sequence("Unknown Type")
        assert seq.shape == (150, 3)


class TestGeneratePreloadedEvents:
    def test_returns_list(self):
        events = generate_preloaded_events()
        assert isinstance(events, list)

    def test_returns_3_events(self):
        events = generate_preloaded_events()
        assert len(events) == 3

    def test_all_have_valid_ids(self):
        events = generate_preloaded_events()
        for e in events:
            assert e.id in ["E1", "E2", "E3"]

    def test_event_types(self):
        events = generate_preloaded_events()
        types = {e.event_type for e in events}
        assert EventType.FALL in types
        assert EventType.SPO2_DROP in types
        assert EventType.MISSED_MEDS in types
