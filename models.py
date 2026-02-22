"""Data models for attendance records."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class AttendanceRecord:
    """Represents a single attendance record for one employee on one day."""

    employee_id: str = ""
    date: str = ""
    employee_name: str = ""
    entry: Optional[datetime] = None
    meal_out: Optional[datetime] = None
    meal_in: Optional[datetime] = None
    dinner_out: Optional[datetime] = None
    dinner_in: Optional[datetime] = None
    exit: Optional[datetime] = None
    permits: List[datetime] = field(default_factory=list)

    # Calculated fields
    total_minutes: float = 0.0
    meal_deduction: float = 0.0
    dinner_deduction: float = 0.0
    permit_deduction: float = 0.0
    net_worked: float = 0.0
    overtime: float = 0.0
