# Optimizador de Columnas de Concreto

Calculo volumetrico, optimizacion de secciones de concreto armado y estimacion de materiales y logistica de vaciado para columnas.

## Requisitos

- Python 3.10+
- numpy
- pandas
- tabulate
- pytest

Instalacion de dependencias:

```bash
pip install -r requirements.txt
```

## Estructura

```
optimizador-columnas-concreto/
├── main.py
├── requirements.txt
├── pytest.ini
├── README.md
├── data/
│   ├── columnas_entrada.csv
│   ├── columnas_optimizadas.csv
│   └── resumen_vaciado_concreto.csv
├── src/
│   ├── __init__.py
│   ├── calculo_volumen.py
│   ├── optimizador_proceso.py
│   └── dosificacion.py
└── tests/
    ├── __init__.py
    └── test_calculos.py
```

## Uso

### Procesar archivo CSV completo

Ejecuta el analisis de todas las columnas listadas en `data/columnas_entrada.csv`, calcula volumenes, optimiza las secciones de acuerdo con la capacidad resistente axial y genera los reportes en CSV:

```bash
python main.py
```

Archivos generados:
- `data/columnas_optimizadas.csv`: dimensiones optimas, volumenes, cuantias de acero y ahorro economico.
- `data/resumen_vaciado_concreto.csv`: volumen acumulado por nivel y conteo de camiones mixer de 8 m3.

### Calculo de una columna por linea de comandos

Permite calcular el volumen y la seccion recomendada para una columna individual:

```bash
python main.py --columna C-101 --b 0.40 --h 0.50 --altura 3.00 --pu 1200 --fc 280
```

Para guardarla en el archivo de entrada:

```bash
python main.py --columna C-101 --b 0.40 --h 0.50 --altura 3.00 --pu 1200 --fc 280 --guardar
```

### Modo interactivo

```bash
python main.py --interactivo
```

### Pruebas

```bash
pytest -v
```
