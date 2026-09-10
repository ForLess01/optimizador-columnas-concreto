# Optimizador de Proceso y Volumen de Columnas de Concreto Armado (Ingeniería Civil)

Este proyecto implementa una solución integral en **Python** empleando **NumPy** y **Pandas** para el cálculo volumétrico, optimización estructural de secciones y planificación logística del proceso de vaciado de columnas de concreto armado en proyectos de edificación.

---

## 🏗️ Contexto en Ingeniería Civil

En proyectos de construcción y estructuras, las columnas frecuentemente son sobredimensionadas de forma empírica o preliminar, generando:
1. **Desperdicio de materiales:** Exceso innecesario de volumen de concreto ($m^3$) y acero ($kg$).
2. **Sobrecostos directos:** Mayor costo en concreto premezclado, encofrado y mano de obra.
3. **Mayor peso sísmico:** Secciones más pesadas aumentan la masa del edificio e incrementan las fuerzas sísmicas basales.
4. **Ineficiencia logística:** Despachos de mixers desbalanceados con mermas y tiempos muertos.

### 📐 Fundamentación Normativa y Algorítmica (ACI 318 / NTE E.060)

El optimizador evalúa el espacio de soluciones dimensionales discretizadas (múltiplos constructivos de 5 cm) y cuantías de acero longitudinal ($\rho \in [1\%, 4\%]$):

$$\phi P_n = \phi \cdot \alpha \cdot \left[ 0.85 \cdot f'_c \cdot (A_g - A_{st}) + f_y \cdot A_{st} \right] \ge P_u$$

Donde:
* $\phi = 0.65$ para columnas con estribos y $0.75$ para espirales/circulares.
* $\alpha = 0.80$ para rectangulares y $0.85$ para circulares.
* $f'_c$: Resistencia especificada a la compresión del concreto ($kg/cm^2$ o $MPa$).
* $f_y$: Límite de fluencia del acero de refuerzo ($420\text{ MPa}$).
* $P_u$: Carga axial última factorizada ($kN$).

**Función Objetivo de Costo Mínimo:**
$$\min C_{\text{total}} = C_{\text{concreto}}(f'_c) \cdot V(b, h) + C_{\text{acero}} \cdot W_{\text{acero}}(b, h, \rho) + C_{\text{encofrado}} \cdot A_{\text{encofrado}}(b, h)$$

---

## 🚀 Rol de NumPy y Pandas

* **NumPy (`numpy`):**
  * Generación de mallas vectorizadas multidimensionales (`np.meshgrid`, `np.arange`) para evaluar miles de combinaciones $(b, h, \rho)$ simultáneamente.
  * Evaluación matricial de restricciones de resistencia estructural ($\phi P_n \ge P_u$) y selección óptima (`np.argmin`).
  * Cálculo geométrico exacto de áreas, perímetros y volúmenes de concreto.
  * Modelado de mermas y cálculo discreto de camiones mixer (`np.floor`, `np.mod`).

* **Pandas (`pandas`):**
  * Lectura y procesamiento de datasets desde archivos CSV (`pd.read_csv`).
  * Enriquecimiento y transformaciones tabulares de series de datos (volúmenes, insumos, costos).
  * Agrupaciones (`groupby`) y agregaciones por niveles de piso para la logística de vaciado.
  * Exportación estructurada de resultados a archivos CSV (`to_csv`).

---

## 📁 Estructura del Proyecto

```
optimizador-columnas-concreto/
├── main.py                     # Punto de entrada principal (flujo automático y CLI)
├── requirements.txt            # Dependencias del proyecto
├── pytest.ini                  # Configuración del entorno de pruebas
├── README.md                   # Documentación técnica
├── data/
│   ├── columnas_entrada.csv    # CSV con registro y dimensiones iniciales
│   ├── columnas_optimizadas.csv# CSV generado con resultados y métricas de ahorro
│   └── resumen_vaciado_concreto.csv # CSV logístico de mixers por nivel
├── src/
│   ├── __init__.py
│   ├── calculo_volumen.py      # Cálculos geométricos, volúmenes y acero inicial
│   ├── optimizador_proceso.py   # Motor de optimización ACI 318 con NumPy
│   └── dosificacion.py         # Dosificación ACI 211, costos y logística mixer
└── tests/
    ├── __init__.py
    └── test_calculos.py        # Pruebas unitarias automatizadas con pytest
```

---

## 💻 Instalación y Uso

### 1. Clonar el repositorio y preparar el entorno

```bash
git clone https://github.com/ForLess01/optimizador-columnas-concreto.git
cd optimizador-columnas-concreto

# Crear entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ejecutar el flujo completo (Procesa CSV y Optimiza)

```bash
python main.py
```
* Lee automáticamente `data/columnas_entrada.csv`.
* Optimiza todas las columnas registradas.
* Genera los reportes CSV `data/columnas_optimizadas.csv` y `data/resumen_vaciado_concreto.csv`.
* Imprime tablas comparativas en la terminal.

### 3. Registro y Cálculo de una Columna Individual por Dimensiones

Para calcular el volumen y la optimización de una columna específica directamente en terminal:

```bash
python main.py --columna C-501 --b 0.40 --h 0.50 --altura 3.20 --pu 1100 --fc 280
```

Si deseas que la columna calculada se guarde automáticamente en el archivo CSV de entrada:
```bash
python main.py --columna C-501 --b 0.40 --h 0.50 --altura 3.20 --pu 1100 --fc 280 --guardar
```

### 4. Modo Interactivo

```bash
python main.py --interactivo
```
Permite ingresar interactivamente el número de columna, tipo de sección, dimensiones ($b$, $h$, $H$), resistencia $f'_c$ y carga de diseño.

### 5. Ejecutar Pruebas Unitarias

```bash
pytest -v
```

---

## 📊 Salidas del Proyecto (Archivos CSV)

1. **`data/columnas_entrada.csv`:**
   Contiene el registro de columnas: `columna_id`, `nivel`, `tipo_seccion`, `b_m`, `h_m`, `altura_H_m`, `carga_axial_Pu_kN`, `fc_kg_cm2`, `cuantia_inicial`.

2. **`data/columnas_optimizadas.csv`:**
   Incluye la comparativa inicial vs óptima:
   * Dimensiones iniciales y optimizadas ($b$, $h$).
   * Volumen de concreto inicial vs optimizado ($m^3$).
   * Ahorro de concreto ($m^3$ y $\%$).
   * Acero de refuerzo requerido ($kg$).
   * Ahorro económico ($USD$ y $\%$).
   * Reducción de huella de carbono ($kg\text{ CO}_2$).
   * Dosificación desagregada: bolsas de cemento, arena ($m^3$), piedra ($m^3$), agua ($m^3$).

3. **`data/resumen_vaciado_concreto.csv`:**
   Planificación del proceso de vaciado por nivel de piso:
   * Volumen neto y con merma técnica (3%).
   * Número de camiones mixer de $8\text{ m}^3$ completos y viajes adicionales.
   * Costos de flete y logística de despacho.

---

## 👨‍💻 Autor

Desarrollado para optimización de procesos de ingeniería civil y gestión de estructuras de concreto armado.
