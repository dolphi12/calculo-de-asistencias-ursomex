# Calculadora de Asistencias - URSOMEX

Programa en Python con interfaz de línea de comandos (CLI) para calcular asistencias laborales a partir de un archivo Excel.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

### Menú Principal

1. **Cargar archivo Excel** – Ingresa la ruta de un archivo `.xlsx` con los registros de asistencia.
2. **Ver registros** – Muestra los registros cargados en una tabla con los cálculos.
3. **Editar registro** – Permite modificar eventos (horas), añadir/eliminar permisos; recalcula automáticamente.
4. **Recalcular todos** – Recalcula todos los registros con la configuración actual.
5. **Exportar a Excel** – Genera un archivo `.xlsx` con los resultados.
6. **Configurar parámetros** – Ajusta umbrales de comida/cena, jornada base y redondeo.
7. **Salir** – Cierra el programa.

### Formato del Archivo de Entrada

El archivo Excel debe contener las siguientes columnas:

| Columna | Descripción |
|---|---|
| ID | Identificador del empleado |
| FECHA | Fecha del registro (día/mes/año) |
| EMPLEADO | Nombre del empleado |
| ENTRADA | Hora de entrada (HH:MM) |
| SALIDA A COMER | Hora de salida a comer |
| REGRESO DE COMER | Hora de regreso de comer |
| SALIDA A CENAR | Hora de salida a cenar |
| REGRESO DE CENAR | Hora de regreso de cenar |
| SALIDA | Hora de salida final |
| PERMISO | (Opcional) Horas de permisos separadas por coma |

### Formato del Archivo de Salida

El archivo exportado incluye las columnas de entrada más:

- **TIEMPO LABORADO** (horas, 2 decimales)
- **HORAS EXTRA** (horas, 2 decimales)
- **DESCUENTO COMIDAS** (horas, 2 decimales)
- **DESCUENTO PERMISOS** (horas, 2 decimales)

### Reglas de Cálculo

- **Tiempo total**: Desde ENTRADA hasta SALIDA (o última checada disponible).
- **Comida**: Si la diferencia ≤ umbral (default 60 min), se descuentan 30 min; si no, se descuenta la diferencia completa.
- **Cena**: Misma lógica que comida.
- **Permisos**: Se agrupan en pares de inicio/fin; se descuenta el tiempo completo de cada par.
- **Horas extra**: Si el tiempo laborado neto supera la jornada base (default 480 min), la diferencia son horas extra.

## Estructura del Proyecto

```
main.py         # Punto de entrada
cli.py          # Interfaz de línea de comandos (rich)
config.py       # Parámetros configurables
models.py       # Modelo de datos AttendanceRecord
core.py         # Motor de cálculo
io_excel.py     # Importar/exportar Excel
utils.py        # Utilidades de tiempo
tests.py        # Tests unitarios
requirements.txt
```

## Tests

```bash
python -m unittest tests -v
```