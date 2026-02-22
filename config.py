"""Configuration parameters for the attendance calculator."""


class Config:
    """Configurable parameters for attendance calculations."""

    def __init__(self):
        self.meal_threshold: int = 60  # minutes
        self.dinner_threshold: int = 60  # minutes
        self.base_workday: int = 480  # minutes (8 hours)
        self.rounding_mode: str = "none"  # none, ceil, floor, round
        self.rounding_minutes: int = 15  # round to nearest N minutes

    def to_dict(self) -> dict:
        return {
            "meal_threshold": self.meal_threshold,
            "dinner_threshold": self.dinner_threshold,
            "base_workday": self.base_workday,
            "rounding_mode": self.rounding_mode,
            "rounding_minutes": self.rounding_minutes,
        }
