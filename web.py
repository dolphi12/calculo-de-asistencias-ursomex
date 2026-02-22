"""Streamlit web interface for the URSOMEX attendance calculator."""

import tempfile
import os
import pandas as pd
import streamlit as st

from config import Config
from core import calculate_all
from io_excel import load_excel, export_excel
from utils import minutes_to_hours, format_time

st.set_page_config(page_title="URSOMEX - Asistencias", layout="wide", page_icon="🏢")


def build_config_from_sidebar() -> Config:
    """Build a Config object from sidebar widgets."""
    cfg = Config()
    st.sidebar.header("⚙️ Parámetros de Configuración")
    cfg.meal_threshold = st.sidebar.number_input(
        "Umbral comida (min)", min_value=1, max_value=480, value=cfg.meal_threshold
    )
    cfg.dinner_threshold = st.sidebar.number_input(
        "Umbral cena (min)", min_value=1, max_value=480, value=cfg.dinner_threshold
    )
    cfg.base_workday = st.sidebar.number_input(
        "Jornada base (min)", min_value=1, max_value=1440, value=cfg.base_workday
    )
    cfg.rounding_mode = st.sidebar.selectbox(
        "Modo redondeo",
        options=["none", "ceil", "floor", "round"],
        index=["none", "ceil", "floor", "round"].index(cfg.rounding_mode),
    )
    cfg.rounding_minutes = st.sidebar.number_input(
        "Minutos de redondeo", min_value=1, max_value=60, value=cfg.rounding_minutes
    )
    return cfg


def format_hours(minutes: float) -> str:
    """Format minutes as a human-readable hours string."""
    return f"{minutes_to_hours(minutes):.2f} h"


def records_to_dataframe(records) -> pd.DataFrame:
    """Convert a list of AttendanceRecord objects to a display DataFrame."""
    rows = []
    for rec in records:
        rows.append(
            {
                "ID": rec.employee_id,
                "Fecha": rec.date,
                "Empleado": rec.employee_name,
                "Entrada": format_time(rec.entry),
                "Salida": format_time(rec.exit),
                "Horas Laboradas": minutes_to_hours(rec.net_worked),
                "Horas Extra": minutes_to_hours(rec.overtime),
            }
        )
    return pd.DataFrame(rows)


def main():
    st.title("🏢 URSOMEX – Calculadora de Asistencias")

    config = build_config_from_sidebar()

    uploaded_file = st.file_uploader(
        "Cargar archivo Excel (.xlsx)", type=["xlsx"], key="file_uploader"
    )

    if uploaded_file is not None:
        # Only reload from file when the uploaded file changes
        if (
            "uploaded_file_name" not in st.session_state
            or st.session_state.uploaded_file_name != uploaded_file.name
            or "raw_records" not in st.session_state
        ):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            try:
                st.session_state.raw_records = load_excel(tmp_path)
                st.session_state.uploaded_file_name = uploaded_file.name
            finally:
                os.unlink(tmp_path)

    if "raw_records" in st.session_state and st.session_state.raw_records:
        records = calculate_all(st.session_state.raw_records, config)
        df = records_to_dataframe(records)

        tab_dashboard, tab_table, tab_export = st.tabs(
            ["📊 Dashboard", "📋 Tabla de Datos", "⬇️ Exportar"]
        )

        with tab_dashboard:
            total_records = len(records)
            total_worked = sum(r.net_worked for r in records)
            total_overtime = sum(r.overtime for r in records)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Registros", total_records)
            col2.metric("Horas Laboradas Totales", format_hours(total_worked))
            col3.metric("Horas Extra Totales", format_hours(total_overtime))

            st.subheader("Horas Laboradas vs. Horas Extra por Empleado")
            chart_df = (
                df.groupby("Empleado")[["Horas Laboradas", "Horas Extra"]]
                .sum()
                .reset_index()
                .set_index("Empleado")
            )
            st.bar_chart(chart_df)

        with tab_table:
            st.subheader("Registros Detallados")
            st.dataframe(df, use_container_width=True)

        with tab_export:
            st.subheader("Exportar Resultados")
            if st.button("Generar archivo Excel"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                    tmp_path = tmp.name
                try:
                    export_excel(records, tmp_path)
                    with open(tmp_path, "rb") as f:
                        st.session_state.export_bytes = f.read()
                finally:
                    os.unlink(tmp_path)

            if "export_bytes" in st.session_state:
                st.download_button(
                    label="⬇️ Descargar resultados.xlsx",
                    data=st.session_state.export_bytes,
                    file_name="resultados_asistencias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
    else:
        st.info("Carga un archivo Excel (.xlsx) para comenzar.")


if __name__ == "__main__":
    main()
