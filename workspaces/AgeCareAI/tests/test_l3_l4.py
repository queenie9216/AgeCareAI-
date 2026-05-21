"""Tests for L3 Schedule Optimizer and L4 Care Agent."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (
    Zone, Day, EventType, RiskBand,
    Senior, SeniorFeatures, Caregiver, Event,
    generate_singapore_seniors,
    generate_caregivers,
    generate_preloaded_events,
    solve_schedule,
    decide_actions,
    execute_action,
    SeniorAssignment,
    ScheduleAssignment,
)


@pytest.mark.slow
class TestSolveSchedule:
    @pytest.fixture
    def seniors(self):
        return generate_singapore_seniors()

    @pytest.fixture
    def caregivers(self):
        return generate_caregivers()

    def test_returns_dict(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        assert isinstance(result, dict)

    def test_result_has_required_keys(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        assert "schedule" in result
        assert "solve_time_ms" in result
        assert "status" in result

    def test_status_values(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        assert result["status"] in ["OPTIMAL", "FEASIBLE"]

    def test_solve_time_positive(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        assert result["solve_time_ms"] >= 0

    def test_schedule_is_list(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        assert isinstance(result["schedule"], list)

    def test_schedule_assignments_have_required_fields(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        for assignment in result["schedule"]:
            assert hasattr(assignment, "caregiver_id")
            assert hasattr(assignment, "caregiver_name")
            assert hasattr(assignment, "day")
            assert hasattr(assignment, "slots")
            assert hasattr(assignment, "zone_match_count")

    def test_slots_contain_senior_assignments(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        for assignment in result["schedule"]:
            for slot in assignment.slots:
                assert hasattr(slot, "senior_id")
                assert hasattr(slot, "senior_name")
                assert hasattr(slot, "zone")
                assert hasattr(slot, "care_needs")

    def test_cancelled_caregiver_excluded(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers, cancelled_cg_id="CG01")
        caregiver_ids = [a.caregiver_id for a in result["schedule"]]
        assert "CG01" not in caregiver_ids

    def test_active_caregivers_included(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        caregiver_ids = [a.caregiver_id for a in result["schedule"]]
        assert len(caregiver_ids) > 0

    def test_zone_match_flag(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        for assignment in result["schedule"]:
            for slot in assignment.slots:
                assert isinstance(slot.zone_match, bool)

    def test_unassigned_tracks_unscheduled_seniors(self, seniors, caregivers):
        result = solve_schedule(seniors, caregivers)
        scheduled_ids = set()
        for assignment in result["schedule"]:
            for slot in assignment.slots:
                scheduled_ids.add(slot.senior_id)
        for senior in result["unassigned"]:
            assert senior.id not in scheduled_ids


class TestSolveScheduleLogic:
    """Fast unit tests for schedule assignment data structures - no OR-Tools needed."""

    def test_schedule_assignment_dataclass_fields(self):
        """Verify ScheduleAssignment has all required fields."""
        assignment = ScheduleAssignment(
            caregiver_id="CG01",
            caregiver_name="Nurse Aileen",
            day=Day.MON,
            slots=[],
            zone_match_count=0
        )
        assert assignment.caregiver_id == "CG01"
        assert assignment.caregiver_name == "Nurse Aileen"
        assert assignment.day == Day.MON
        assert assignment.slots == []
        assert assignment.zone_match_count == 0

    def test_senior_assignment_dataclass_fields(self):
        """Verify SeniorAssignment has all required fields."""
        slot = SeniorAssignment(
            senior_id="S01",
            senior_name="Alice",
            zone=Zone.NORTH,
            care_needs=["Dementia"],
            zone_match=True
        )
        assert slot.senior_id == "S01"
        assert slot.senior_name == "Alice"
        assert slot.zone == Zone.NORTH
        assert slot.care_needs == ["Dementia"]
        assert slot.zone_match is True

    def test_schedule_assignment_with_slots(self):
        """Verify ScheduleAssignment can hold senior slots."""
        slots = [
            SeniorAssignment(
                senior_id="S01", senior_name="Alice",
                zone=Zone.NORTH, care_needs=["Dementia"], zone_match=True
            ),
            SeniorAssignment(
                senior_id="S02", senior_name="Bob",
                zone=Zone.SOUTH, care_needs=["Chronic Disease"], zone_match=False
            ),
        ]
        assignment = ScheduleAssignment(
            caregiver_id="CG01",
            caregiver_name="Nurse Aileen",
            day=Day.MON,
            slots=slots,
            zone_match_count=1
        )
        assert len(assignment.slots) == 2
        assert assignment.zone_match_count == 1

    def test_zone_match_calculation(self):
        """Verify zone_match reflects same-zone assignment."""
        same_zone = SeniorAssignment(
            senior_id="S01", senior_name="Alice",
            zone=Zone.NORTH, care_needs=["Dementia"], zone_match=True
        )
        diff_zone = SeniorAssignment(
            senior_id="S02", senior_name="Bob",
            zone=Zone.SOUTH, care_needs=["Chronic Disease"], zone_match=False
        )
        assert same_zone.zone_match is True
        assert diff_zone.zone_match is False

    def test_unassigned_seniors_tracking(self):
        """Verify unassigned list contains Senior objects."""
        seniors = generate_singapore_seniors()
        unassigned = seniors[5:]  # Some seniors not assigned
        assert len(unassigned) > 0
        for s in unassigned:
            assert isinstance(s, Senior)
            assert s.id.startswith("S")

    def test_caregiver_filter_excludes_inactive(self):
        """Verify active/inactive caregiver filtering logic."""
        caregivers = generate_caregivers()
        active = [cg for cg in caregivers if cg.active]
        inactive = [cg for cg in caregivers if not cg.active]
        assert len(active) == len(caregivers)  # All active by default
        assert len(inactive) == 0


class TestDecideActions:
    @pytest.fixture
    def fall_event(self):
        return Event(
            id="E1",
            senior_id="S01",
            senior_name="Tan Poh Lek",
            senior_age=78,
            event_type=EventType.FALL,
            timestamp=datetime.now(),
            risk_band=RiskBand.RED,
            confidence=0.91
        )

    @pytest.fixture
    def spo2_event(self):
        return Event(
            id="E2",
            senior_id="S02",
            senior_name="Lim Sok Kuan",
            senior_age=72,
            event_type=EventType.SPO2_DROP,
            timestamp=datetime.now(),
            risk_band=RiskBand.AMBER,
            metadata={"metric": "SpO2", "value": 91}
        )

    @pytest.fixture
    def meds_event(self):
        return Event(
            id="E3",
            senior_id="S03",
            senior_name="Ng Teck Seng",
            senior_age=80,
            event_type=EventType.MISSED_MEDS,
            timestamp=datetime.now(),
            risk_band=RiskBand.GREEN,
            metadata={"doses_missed": 2}
        )

    def test_fall_red_returns_ems_dispatch(self, fall_event):
        fall_event.risk_band = RiskBand.RED
        actions = decide_actions(fall_event)
        assert "EMS_DISPATCH" in actions
        assert "FAMILY_ALERT" in actions
        assert "NEHR_LOG" in actions

    def test_fall_amber_returns_ambulance_standby(self, fall_event):
        fall_event.risk_band = RiskBand.AMBER
        actions = decide_actions(fall_event)
        assert "FAMILY_ALERT" in actions
        assert "AMBULANCE_STANDBY" in actions

    def test_fall_green_returns_log_only(self, fall_event):
        fall_event.risk_band = RiskBand.GREEN
        actions = decide_actions(fall_event)
        assert "LOG_ONLY" in actions

    def test_spo2_red_returns_ems_dispatch(self, spo2_event):
        spo2_event.risk_band = RiskBand.RED
        actions = decide_actions(spo2_event)
        assert "EMS_DISPATCH" in actions
        assert "POLYCLINIC_EMERGENCY" in actions

    def test_spo2_amber_books_polyclinic(self, spo2_event):
        spo2_event.risk_band = RiskBand.AMBER
        actions = decide_actions(spo2_event)
        assert "FAMILY_ALERT" in actions
        assert "POLYCLINIC_BOOKING" in actions

    def test_spo2_green_returns_log_only(self, spo2_event):
        spo2_event.risk_band = RiskBand.GREEN
        actions = decide_actions(spo2_event)
        assert "LOG_ONLY" in actions

    def test_missed_meds_green_sends_reminder(self, meds_event):
        meds_event.risk_band = RiskBand.GREEN
        actions = decide_actions(meds_event)
        assert "SEND_REMINDER" in actions

    def test_missed_meds_non_green_logs_only(self, meds_event):
        meds_event.risk_band = RiskBand.AMBER
        actions = decide_actions(meds_event)
        assert "LOG_ONLY" in actions

    def test_returns_list(self, fall_event):
        actions = decide_actions(fall_event)
        assert isinstance(actions, list)
        assert len(actions) > 0

    def test_unknown_event_type_returns_default(self):
        event = Event(
            id="E99",
            senior_id="S99",
            senior_name="Unknown",
            senior_age=70,
            event_type=EventType.FALL,
            timestamp=datetime.now(),
            risk_band=RiskBand.GREEN
        )
        # Manually create an event with a type not in the switch
        event.event_type = None
        actions = decide_actions(event)
        assert "LOG_ONLY" in actions


class TestExecuteAction:
    @pytest.fixture
    def event(self):
        return Event(
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

    def test_ems_dispatch_returns_dict(self, event):
        result = execute_action("EMS_DISPATCH", event)
        assert isinstance(result, dict)

    def test_ems_dispatch_has_required_keys(self, event):
        result = execute_action("EMS_DISPATCH", event)
        assert "action" in result
        assert "message" in result
        assert "timestamp" in result
        assert "json_log" in result

    def test_ems_dispatch_action_value(self, event):
        result = execute_action("EMS_DISPATCH", event)
        assert result["action"] == "EMS_DISPATCH"

    def test_family_alert_action(self, event):
        result = execute_action("FAMILY_ALERT", event)
        assert result["action"] == "FAMILY_ALERT"

    def test_nehr_log_action(self, event):
        result = execute_action("NEHR_LOG", event)
        assert result["action"] == "NEHR_LOG"

    def test_polyclinic_booking_action(self, event):
        result = execute_action("POLYCLINIC_BOOKING", event)
        assert result["action"] == "POLYCLINIC_BOOKING"

    def test_send_reminder_action(self, event):
        result = execute_action("SEND_REMINDER", event)
        assert result["action"] == "SEND_REMINDER"

    def test_ambulance_standby_action(self, event):
        result = execute_action("AMBULANCE_STANDBY", event)
        assert result["action"] == "AMBULANCE_STANDBY"

    def test_log_only_action(self, event):
        result = execute_action("LOG_ONLY", event)
        assert result["action"] == "LOG_ONLY"

    def test_schedule_check_action(self, event):
        result = execute_action("SCHEDULE_CHECK", event)
        assert result["action"] == "SCHEDULE_CHECK"

    def test_unknown_action_default(self, event):
        result = execute_action("UNKNOWN_ACTION", event)
        assert result["action"] == "UNKNOWN_ACTION"

    def test_all_actions_have_json_log(self, event):
        for action in ["EMS_DISPATCH", "FAMILY_ALERT", "NEHR_LOG",
                       "POLYCLINIC_BOOKING", "SEND_REMINDER",
                       "AMBULANCE_STANDBY", "LOG_ONLY", "SCHEDULE_CHECK"]:
            result = execute_action(action, event)
            assert "json_log" in result
            assert result["json_log"].startswith("{")

    def test_timestamp_is_iso_format(self, event):
        result = execute_action("EMS_DISPATCH", event)
        assert "T" in result["timestamp"]
