"""Core calculation engine for attendance records."""

from typing import List
from models import AttendanceRecord
from config import Config
from utils import minutes_between, apply_rounding


def calculate_meal_deduction(record: AttendanceRecord, threshold: int) -> float:
    """Calculate meal deduction in minutes."""
    if record.meal_out is None or record.meal_in is None:
        return 0.0
    diff = minutes_between(record.meal_out, record.meal_in)
    if diff <= 0:
        return 0.0
    if diff <= threshold:
        return 30.0
    return diff


def calculate_dinner_deduction(record: AttendanceRecord, threshold: int) -> float:
    """Calculate dinner deduction in minutes."""
    if record.dinner_out is None or record.dinner_in is None:
        return 0.0
    diff = minutes_between(record.dinner_out, record.dinner_in)
    if diff <= 0:
        return 0.0
    if diff <= threshold:
        return 30.0
    return diff


def calculate_permit_deduction(permits: list) -> float:
    """Calculate total permit deduction in minutes from paired permit times."""
    total = 0.0
    # Group in pairs
    for i in range(0, len(permits) - 1, 2):
        diff = minutes_between(permits[i], permits[i + 1])
        if diff > 0:
            total += diff
    return total


def calculate_total_time(record: AttendanceRecord) -> float:
    """Calculate total time at work from entry to exit (or last available event)."""
    start = record.entry
    end = record.exit

    if start is None:
        return 0.0

    # If no exit, find last available event
    if end is None:
        candidates = [
            record.meal_out, record.meal_in,
            record.dinner_out, record.dinner_in,
        ]
        if record.permits:
            candidates.extend(record.permits)
        valid = [c for c in candidates if c is not None]
        if not valid:
            return 0.0
        end = max(valid)

    return minutes_between(start, end)


def calculate_record(record: AttendanceRecord, config: Config) -> AttendanceRecord:
    """Perform all calculations on a single attendance record."""
    record.total_minutes = calculate_total_time(record)
    record.meal_deduction = calculate_meal_deduction(record, config.meal_threshold)
    record.dinner_deduction = calculate_dinner_deduction(record, config.dinner_threshold)
    record.permit_deduction = calculate_permit_deduction(record.permits)

    record.net_worked = record.total_minutes - (
        record.meal_deduction + record.dinner_deduction + record.permit_deduction
    )
    if record.net_worked < 0:
        record.net_worked = 0.0

    raw_overtime = record.net_worked - config.base_workday
    if raw_overtime > 0:
        record.overtime = apply_rounding(
            raw_overtime, config.rounding_mode, config.rounding_minutes
        )
    else:
        record.overtime = 0.0

    return record


def calculate_all(records: List[AttendanceRecord], config: Config) -> List[AttendanceRecord]:
    """Recalculate all records."""
    return [calculate_record(r, config) for r in records]
