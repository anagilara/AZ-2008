# Gestor de Productos Web (Python) v2

Aplicacion web en Python para administrar productos con operaciones CRUD, filtros y panel de resumen de inventario.

## Funcionalidades

- Crear, editar y eliminar productos.
- Campos de producto: nombre, SKU unico, categoria, precio, stock y descripcion.
- Busqueda por nombre, SKU, categoria o descripcion.
- Filtro por categoria.
- Resumen con total de productos, unidades en stock, valor de inventario y productos con stock bajo.
- Persistencia en SQLite (archivo local products.db).

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

## Pruebas unitarias

Ejecutar pruebas con pytest:

	pytest -q

## Estructura

- app.py: Backend Flask y rutas.
- templates/: Vistas HTML.
- static/styles.css: Estilos responsivos.
- requirements.txt: Dependencias Python.

## Notas

- La base de datos SQLite se crea automaticamente al iniciar.
- El archivo products.db esta excluido en .gitignore.
