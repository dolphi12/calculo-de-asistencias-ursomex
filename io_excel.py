"""Excel import/export functions."""

import pandas as pd
from typing import List
from models import AttendanceRecord
from utils import parse_time, format_time, minutes_to_hours, parse_permit_string


# Column name mappings (Spanish -> internal attribute name)
COLUMN_MAP = {
    "ID": "employee_id",
    "FECHA": "date",
    "EMPLEADO": "employee_name",
    "ENTRADA": "entry",
    "SALIDA A COMER": "meal_out",
    "REGRESO DE COMER": "meal_in",
    "SALIDA A CENAR": "dinner_out",
    "REGRESO DE CENAR": "dinner_in",
    "SALIDA": "exit",
    "PERMISO": "permits",
}

# Fields that should be parsed as time values
_TIME_FIELDS = {"entry", "meal_out", "meal_in", "dinner_out", "dinner_in", "exit"}


def load_excel(filepath: str) -> List[AttendanceRecord]:
    """Load attendance records from an Excel file."""
    df = pd.read_excel(filepath, engine="openpyxl")

    # Normalize column names
    df.columns = [str(c).strip().upper() for c in df.columns]

    records = []
    for _, row in df.iterrows():
        rec = AttendanceRecord()

        for col_name, attr_name in COLUMN_MAP.items():
            if col_name not in df.columns:
                continue
            val = row.get(col_name, "")
            if attr_name == "permits":
                setattr(rec, attr_name, parse_permit_string(val))
            elif attr_name in _TIME_FIELDS:
                setattr(rec, attr_name, parse_time(val))
            elif attr_name == "date":
                setattr(rec, attr_name, str(val).strip() if pd.notna(val) else "")
            else:
                setattr(rec, attr_name, str(val).strip())

        records.append(rec)

    return records


def export_excel(records: List[AttendanceRecord], filepath: str) -> None:
    """Export attendance records to an Excel file."""
    rows = []
    for rec in records:
        # Format permit pairs
        permit_str = ""
        if rec.permits:
            pairs = []
            for i in range(0, len(rec.permits) - 1, 2):
                pairs.append(f"{format_time(rec.permits[i])}-{format_time(rec.permits[i + 1])}")
            if len(rec.permits) % 2 == 1:
                pairs.append(format_time(rec.permits[-1]))
            permit_str = ", ".join(pairs)

        rows.append({
            "ID": rec.employee_id,
            "FECHA": rec.date,
            "EMPLEADO": rec.employee_name,
            "ENTRADA": format_time(rec.entry),
            "SALIDA A COMER": format_time(rec.meal_out),
            "REGRESO DE COMER": format_time(rec.meal_in),
            "SALIDA A CENAR": format_time(rec.dinner_out),
            "REGRESO DE CENAR": format_time(rec.dinner_in),
            "SALIDA": format_time(rec.exit),
            "PERMISO": permit_str,
            "TIEMPO LABORADO": minutes_to_hours(rec.net_worked),
            "HORAS EXTRA": minutes_to_hours(rec.overtime),
            "DESCUENTO COMIDAS": minutes_to_hours(rec.meal_deduction + rec.dinner_deduction),
            "DESCUENTO PERMISOS": minutes_to_hours(rec.permit_deduction),
        })

    df = pd.DataFrame(rows)
    df.to_excel(filepath, index=False, engine="openpyxl")
