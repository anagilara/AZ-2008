# Gestor de Pagos Web (Python)

Aplicacion web en Python para administrar pagos con interfaz moderna, filtros y panel de resumen.

## Funcionalidades

- Crear, editar y eliminar pagos.
- Marcar pagos como pagados.
- Estados de pago: pending, paid, overdue, cancelled.
- Actualizacion automatica a overdue cuando vence un pago pendiente.
- Busqueda por cliente, concepto o notas.
- Filtro por estado.
- Resumen con montos total, pagado, pendiente y vencido.
- Persistencia en SQLite (archivo local payments.db).

## Requisitos

- Python 3.10+

## Instalacion y ejecucion

1. Crear entorno virtual:

	python3 -m venv .venv

2. Activar entorno:

	source .venv/bin/activate

3. Instalar dependencias:

	pip install -r requirements.txt

4. Ejecutar la app:

	python app.py

5. Abrir en navegador:

	http://127.0.0.1:5000

## Estructura

- app.py: Backend Flask y rutas.
- templates/: Vistas HTML.
- static/styles.css: Estilos responsivos.
- requirements.txt: Dependencias Python.

## Notas

- La base de datos SQLite se crea automaticamente al iniciar.
- El archivo payments.db esta excluido en .gitignore.