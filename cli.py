"""Interactive CLI interface for the attendance calculator."""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel

from config import Config
from models import AttendanceRecord
from core import calculate_record, calculate_all
from io_excel import load_excel, export_excel
from utils import format_time, minutes_to_hours, parse_time

console = Console()


def show_menu() -> str:
    """Display main menu and return user choice."""
    console.print()
    console.print(Panel(
        "[bold cyan]Calculadora de Asistencias - URSOMEX[/bold cyan]",
        subtitle="Sistema de Control de Asistencia"
    ))
    console.print("[1] Cargar archivo Excel")
    console.print("[2] Ver registros")
    console.print("[3] Editar registro")
    console.print("[4] Recalcular todos")
    console.print("[5] Exportar a Excel")
    console.print("[6] Configurar parámetros")
    console.print("[7] Salir")
    console.print()
    return Prompt.ask("Seleccione una opción", choices=["1", "2", "3", "4", "5", "6", "7"])


def display_records(records: List[AttendanceRecord], start: int = 0, count: int = 20) -> None:
    """Display records in a formatted table."""
    if not records:
        console.print("[yellow]No hay registros cargados.[/yellow]")
        return

    table = Table(title="Registros de Asistencia", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", width=10)
    table.add_column("Fecha", width=12)
    table.add_column("Empleado", width=20)
    table.add_column("Entrada", width=8)
    table.add_column("Sal. Comer", width=10)
    table.add_column("Reg. Comer", width=10)
    table.add_column("Sal. Cenar", width=10)
    table.add_column("Reg. Cenar", width=10)
    table.add_column("Salida", width=8)
    table.add_column("Laborado", width=9)
    table.add_column("H. Extra", width=8)
    table.add_column("Desc. Com.", width=10)
    table.add_column("Desc. Perm.", width=10)

    end = min(start + count, len(records))
    for i in range(start, end):
        rec = records[i]
        table.add_row(
            str(i),
            rec.employee_id,
            rec.date,
            rec.employee_name,
            format_time(rec.entry),
            format_time(rec.meal_out),
            format_time(rec.meal_in),
            format_time(rec.dinner_out),
            format_time(rec.dinner_in),
            format_time(rec.exit),
            f"{minutes_to_hours(rec.net_worked):.2f}",
            f"{minutes_to_hours(rec.overtime):.2f}",
            f"{minutes_to_hours(rec.meal_deduction + rec.dinner_deduction):.2f}",
            f"{minutes_to_hours(rec.permit_deduction):.2f}",
        )

    console.print(table)
    console.print(f"Mostrando {start + 1}-{end} de {len(records)} registros")


def display_single_record(rec: AttendanceRecord, index: int) -> None:
    """Display a single record in detail."""
    table = Table(title=f"Registro #{index}", show_lines=True)
    table.add_column("Campo", style="bold")
    table.add_column("Valor")

    table.add_row("ID", rec.employee_id)
    table.add_row("Fecha", rec.date)
    table.add_row("Empleado", rec.employee_name)
    table.add_row("Entrada", format_time(rec.entry))
    table.add_row("Salida a Comer", format_time(rec.meal_out))
    table.add_row("Regreso de Comer", format_time(rec.meal_in))
    table.add_row("Salida a Cenar", format_time(rec.dinner_out))
    table.add_row("Regreso de Cenar", format_time(rec.dinner_in))
    table.add_row("Salida", format_time(rec.exit))
    permits_str = ", ".join(format_time(p) for p in rec.permits) if rec.permits else "(ninguno)"
    table.add_row("Permisos", permits_str)
    table.add_row("---", "--- Resultados ---")
    table.add_row("Tiempo total (min)", f"{rec.total_minutes:.1f}")
    table.add_row("Desc. comida (min)", f"{rec.meal_deduction:.1f}")
    table.add_row("Desc. cena (min)", f"{rec.dinner_deduction:.1f}")
    table.add_row("Desc. permisos (min)", f"{rec.permit_deduction:.1f}")
    table.add_row("Tiempo laborado (hrs)", f"{minutes_to_hours(rec.net_worked):.2f}")
    table.add_row("Horas extra (hrs)", f"{minutes_to_hours(rec.overtime):.2f}")

    console.print(table)


def edit_record_menu(records: List[AttendanceRecord], config: Config) -> None:
    """Handle editing a record."""
    if not records:
        console.print("[yellow]No hay registros cargados.[/yellow]")
        return

    idx = IntPrompt.ask(f"Índice del registro a editar (0-{len(records) - 1})")
    if idx < 0 or idx >= len(records):
        console.print("[red]Índice fuera de rango.[/red]")
        return

    rec = records[idx]
    display_single_record(rec, idx)

    console.print()
    console.print("[1] Modificar un evento (hora)")
    console.print("[2] Añadir permiso")
    console.print("[3] Eliminar permiso")
    console.print("[4] Cancelar")

    choice = Prompt.ask("Seleccione acción", choices=["1", "2", "3", "4"])

    if choice == "1":
        console.print("Campos editables:")
        console.print("  1. Entrada")
        console.print("  2. Salida a Comer")
        console.print("  3. Regreso de Comer")
        console.print("  4. Salida a Cenar")
        console.print("  5. Regreso de Cenar")
        console.print("  6. Salida")
        field_choice = Prompt.ask("Campo a modificar", choices=["1", "2", "3", "4", "5", "6"])
        new_val = Prompt.ask("Nueva hora (HH:MM, o vacío para borrar)")
        parsed = parse_time(new_val) if new_val.strip() else None

        field_map = {
            "1": "entry", "2": "meal_out", "3": "meal_in",
            "4": "dinner_out", "5": "dinner_in", "6": "exit",
        }
        setattr(rec, field_map[field_choice], parsed)

    elif choice == "2":
        new_val = Prompt.ask("Hora del permiso a añadir (HH:MM)")
        parsed = parse_time(new_val)
        if parsed:
            rec.permits.append(parsed)
            rec.permits.sort()
            console.print(f"[green]Permiso {new_val} añadido.[/green]")
        else:
            console.print("[red]Hora no válida.[/red]")

    elif choice == "3":
        if not rec.permits:
            console.print("[yellow]No hay permisos para eliminar.[/yellow]")
        else:
            for pi, p in enumerate(rec.permits):
                console.print(f"  {pi}: {format_time(p)}")
            pi = IntPrompt.ask("Índice del permiso a eliminar")
            if 0 <= pi < len(rec.permits):
                removed = rec.permits.pop(pi)
                console.print(f"[green]Permiso {format_time(removed)} eliminado.[/green]")
            else:
                console.print("[red]Índice fuera de rango.[/red]")

    elif choice == "4":
        return

    # Recalculate after edit
    calculate_record(rec, config)
    console.print("[green]Registro recalculado:[/green]")
    display_single_record(rec, idx)


def configure_menu(config: Config) -> None:
    """Handle configuration changes."""
    console.print()
    console.print(Panel("[bold]Configuración Actual[/bold]"))
    console.print(f"  1. Umbral comida: {config.meal_threshold} minutos")
    console.print(f"  2. Umbral cena: {config.dinner_threshold} minutos")
    console.print(f"  3. Jornada base: {config.base_workday} minutos ({config.base_workday / 60:.1f} hrs)")
    console.print(f"  4. Modo redondeo: {config.rounding_mode}")
    console.print(f"  5. Minutos redondeo: {config.rounding_minutes}")
    console.print(f"  6. Volver")

    choice = Prompt.ask("Parámetro a modificar", choices=["1", "2", "3", "4", "5", "6"])

    if choice == "1":
        config.meal_threshold = IntPrompt.ask("Nuevo umbral comida (minutos)", default=config.meal_threshold)
    elif choice == "2":
        config.dinner_threshold = IntPrompt.ask("Nuevo umbral cena (minutos)", default=config.dinner_threshold)
    elif choice == "3":
        config.base_workday = IntPrompt.ask("Nueva jornada base (minutos)", default=config.base_workday)
    elif choice == "4":
        config.rounding_mode = Prompt.ask(
            "Modo de redondeo", choices=["none", "ceil", "floor", "round"],
            default=config.rounding_mode
        )
    elif choice == "5":
        config.rounding_minutes = IntPrompt.ask("Minutos de redondeo", default=config.rounding_minutes)

    console.print("[green]Configuración actualizada.[/green]")


def run_cli() -> None:
    """Main CLI loop."""
    config = Config()
    records: List[AttendanceRecord] = []

    while True:
        choice = show_menu()

        if choice == "1":
            filepath = Prompt.ask("Ruta del archivo Excel")
            try:
                records = load_excel(filepath)
                records = calculate_all(records, config)
                console.print(f"[green]Se cargaron {len(records)} registros.[/green]")
            except FileNotFoundError:
                console.print(f"[red]Archivo no encontrado: {filepath}[/red]")
            except Exception as e:
                console.print(f"[red]Error al cargar archivo: {e}[/red]")

        elif choice == "2":
            if not records:
                console.print("[yellow]No hay registros cargados.[/yellow]")
            else:
                start = IntPrompt.ask("Desde registro", default=0)
                count = IntPrompt.ask("Cantidad a mostrar", default=20)
                display_records(records, start, count)

        elif choice == "3":
            edit_record_menu(records, config)

        elif choice == "4":
            records = calculate_all(records, config)
            console.print(f"[green]Se recalcularon {len(records)} registros.[/green]")

        elif choice == "5":
            if not records:
                console.print("[yellow]No hay registros para exportar.[/yellow]")
            else:
                filepath = Prompt.ask("Ruta del archivo de salida", default="resultado.xlsx")
                try:
                    export_excel(records, filepath)
                    console.print(f"[green]Archivo exportado: {filepath}[/green]")
                except Exception as e:
                    console.print(f"[red]Error al exportar: {e}[/red]")

        elif choice == "6":
            configure_menu(config)

        elif choice == "7":
            console.print("[bold cyan]¡Hasta luego![/bold cyan]")
            break
