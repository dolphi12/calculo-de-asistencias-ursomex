"""Unit tests for the attendance calculator."""

import unittest
from datetime import datetime

from config import Config
from models import AttendanceRecord
from core import (
    calculate_meal_deduction,
    calculate_dinner_deduction,
    calculate_permit_deduction,
    calculate_total_time,
    calculate_record,
    calculate_all,
)
from utils import parse_time, format_time, minutes_between, minutes_to_hours, apply_rounding, parse_permit_string


class TestUtils(unittest.TestCase):

    def test_parse_time_hhmm(self):
        result = parse_time("08:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 8)
        self.assertEqual(result.minute, 30)

    def test_parse_time_hhmmss(self):
        result = parse_time("14:05:30")
        self.assertIsNotNone(result)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 5)

    def test_parse_time_none(self):
        self.assertIsNone(parse_time(None))
        self.assertIsNone(parse_time(""))
        self.assertIsNone(parse_time("nan"))

    def test_parse_time_datetime(self):
        dt = datetime(2024, 1, 1, 9, 0)
        self.assertEqual(parse_time(dt), dt)

    def test_format_time(self):
        dt = datetime(2024, 1, 1, 14, 30)
        self.assertEqual(format_time(dt), "14:30")
        self.assertEqual(format_time(None), "")

    def test_minutes_between(self):
        a = datetime(2024, 1, 1, 8, 0)
        b = datetime(2024, 1, 1, 17, 0)
        self.assertEqual(minutes_between(a, b), 540.0)
        self.assertEqual(minutes_between(None, b), 0.0)

    def test_minutes_to_hours(self):
        self.assertEqual(minutes_to_hours(60), 1.0)
        self.assertEqual(minutes_to_hours(90), 1.5)
        self.assertEqual(minutes_to_hours(0), 0.0)

    def test_apply_rounding_none(self):
        self.assertEqual(apply_rounding(37, "none", 15), 37)

    def test_apply_rounding_ceil(self):
        self.assertEqual(apply_rounding(37, "ceil", 15), 45)

    def test_apply_rounding_floor(self):
        self.assertEqual(apply_rounding(37, "floor", 15), 30)

    def test_apply_rounding_round(self):
        self.assertEqual(apply_rounding(37, "round", 15), 30)
        self.assertEqual(apply_rounding(38, "round", 15), 45)

    def test_parse_permit_string(self):
        result = parse_permit_string("14:30, 15:00, 18:30, 19:00")
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].hour, 14)
        self.assertEqual(result[0].minute, 30)

    def test_parse_permit_string_empty(self):
        self.assertEqual(parse_permit_string(""), [])
        self.assertEqual(parse_permit_string(None), [])
        self.assertEqual(parse_permit_string("nan"), [])


class TestCore(unittest.TestCase):

    def _make_record(self, entry="08:00", exit_t="17:00",
                     meal_out=None, meal_in=None,
                     dinner_out=None, dinner_in=None,
                     permits=None):
        rec = AttendanceRecord()
        rec.entry = parse_time(entry)
        rec.exit = parse_time(exit_t)
        rec.meal_out = parse_time(meal_out) if meal_out else None
        rec.meal_in = parse_time(meal_in) if meal_in else None
        rec.dinner_out = parse_time(dinner_out) if dinner_out else None
        rec.dinner_in = parse_time(dinner_in) if dinner_in else None
        rec.permits = [parse_time(p) for p in permits] if permits else []
        return rec

    def test_total_time_basic(self):
        rec = self._make_record("08:00", "17:00")
        self.assertEqual(calculate_total_time(rec), 540.0)

    def test_total_time_no_exit(self):
        rec = self._make_record("08:00", None, meal_out="12:00", meal_in="13:00")
        total_time = calculate_total_time(rec)
        self.assertEqual(total_time, 300.0)  # 08:00 to 13:00

    def test_total_time_no_entry(self):
        rec = self._make_record(None, "17:00")
        self.assertEqual(calculate_total_time(rec), 0.0)

    def test_meal_deduction_within_threshold(self):
        rec = self._make_record(meal_out="12:00", meal_in="12:45")
        self.assertEqual(calculate_meal_deduction(rec, 60), 30.0)

    def test_meal_deduction_exactly_at_threshold(self):
        rec = self._make_record(meal_out="12:00", meal_in="13:00")
        self.assertEqual(calculate_meal_deduction(rec, 60), 30.0)

    def test_meal_deduction_over_threshold(self):
        rec = self._make_record(meal_out="12:00", meal_in="13:30")
        self.assertEqual(calculate_meal_deduction(rec, 60), 90.0)

    def test_meal_deduction_no_data(self):
        rec = self._make_record()
        self.assertEqual(calculate_meal_deduction(rec, 60), 0.0)

    def test_dinner_deduction_within_threshold(self):
        rec = self._make_record(dinner_out="19:00", dinner_in="19:30")
        self.assertEqual(calculate_dinner_deduction(rec, 60), 30.0)

    def test_dinner_deduction_over_threshold(self):
        rec = self._make_record(dinner_out="19:00", dinner_in="20:30")
        self.assertEqual(calculate_dinner_deduction(rec, 60), 90.0)

    def test_permit_deduction(self):
        permits = [parse_time("14:00"), parse_time("14:30"),
                   parse_time("16:00"), parse_time("16:15")]
        self.assertEqual(calculate_permit_deduction(permits), 45.0)

    def test_permit_deduction_odd(self):
        permits = [parse_time("14:00"), parse_time("14:30"),
                   parse_time("16:00")]
        self.assertEqual(calculate_permit_deduction(permits), 30.0)

    def test_permit_deduction_empty(self):
        self.assertEqual(calculate_permit_deduction([]), 0.0)

    def test_calculate_record_full(self):
        config = Config()
        rec = self._make_record(
            entry="08:00", exit_t="17:00",
            meal_out="12:00", meal_in="12:45",
        )
        rec.employee_id = "001"
        rec.date = "01/01/2024"
        rec.employee_name = "Test"
        calculate_record(rec, config)

        # Total: 540 min, Meal deduction: 30 min (<=60), Net: 510
        self.assertEqual(rec.total_minutes, 540.0)
        self.assertEqual(rec.meal_deduction, 30.0)
        self.assertEqual(rec.net_worked, 510.0)
        # Overtime: 510 - 480 = 30
        self.assertEqual(rec.overtime, 30.0)

    def test_calculate_record_no_overtime(self):
        config = Config()
        rec = self._make_record(entry="08:00", exit_t="16:00")
        calculate_record(rec, config)
        self.assertEqual(rec.net_worked, 480.0)
        self.assertEqual(rec.overtime, 0.0)

    def test_calculate_record_with_permits(self):
        config = Config()
        rec = self._make_record(
            entry="08:00", exit_t="18:00",
            meal_out="12:00", meal_in="13:00",
        )
        rec.permits = [parse_time("15:00"), parse_time("15:30")]
        calculate_record(rec, config)
        # Total: 600 min, Meal: 30, Permit: 30, Net: 540
        self.assertEqual(rec.total_minutes, 600.0)
        self.assertEqual(rec.meal_deduction, 30.0)
        self.assertEqual(rec.permit_deduction, 30.0)
        self.assertEqual(rec.net_worked, 540.0)
        self.assertEqual(rec.overtime, 60.0)

    def test_calculate_record_rounding(self):
        config = Config()
        config.rounding_mode = "ceil"
        config.rounding_minutes = 15
        rec = self._make_record(entry="08:00", exit_t="16:37")
        calculate_record(rec, config)
        # Net: 517 min, OT: 37 min, ceil to 15 -> 45
        self.assertEqual(rec.overtime, 45.0)

    def test_calculate_all(self):
        config = Config()
        r1 = self._make_record(entry="08:00", exit_t="16:00")
        r2 = self._make_record(entry="07:00", exit_t="17:00")
        results = calculate_all([r1, r2], config)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].net_worked, 480.0)
        self.assertEqual(results[1].net_worked, 600.0)


class TestIOExcel(unittest.TestCase):

    def test_round_trip(self):
        """Test load and export cycle."""
        import pandas as pd
        import os
        import tempfile
        from io_excel import load_excel, export_excel

        # Create test Excel
        data = {
            "ID": ["001", "002"],
            "FECHA": ["01/01/2024", "02/01/2024"],
            "EMPLEADO": ["Juan", "Maria"],
            "ENTRADA": ["08:00", "07:30"],
            "SALIDA A COMER": ["12:00", "12:30"],
            "REGRESO DE COMER": ["12:45", "13:00"],
            "SALIDA A CENAR": ["", ""],
            "REGRESO DE CENAR": ["", ""],
            "SALIDA": ["17:00", "16:30"],
            "PERMISO": ["", "14:30, 15:00"],
        }
        df = pd.DataFrame(data)
        tmp_in = os.path.join(tempfile.gettempdir(), "test_input.xlsx")
        tmp_out = os.path.join(tempfile.gettempdir(), "test_output.xlsx")

        try:
            df.to_excel(tmp_in, index=False, engine="openpyxl")

            records = load_excel(tmp_in)
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0].employee_name, "Juan")
            self.assertIsNotNone(records[0].entry)
            self.assertEqual(records[0].entry.hour, 8)
            self.assertEqual(len(records[1].permits), 2)

            # Calculate and export
            config = Config()
            from core import calculate_all
            records = calculate_all(records, config)

            export_excel(records, tmp_out)
            self.assertTrue(os.path.exists(tmp_out))

            # Verify output
            df_out = pd.read_excel(tmp_out, engine="openpyxl")
            self.assertIn("TIEMPO LABORADO", df_out.columns)
            self.assertIn("HORAS EXTRA", df_out.columns)
            self.assertIn("DESCUENTO COMIDAS", df_out.columns)
            self.assertIn("DESCUENTO PERMISOS", df_out.columns)
        finally:
            for f in (tmp_in, tmp_out):
                if os.path.exists(f):
                    os.remove(f)


if __name__ == "__main__":
    unittest.main()
