"""
Punto de Entrada Principal - Optimización de Proceso de Columnas de Concreto Armado.
Uso de NumPy y Pandas para cálculo volumétrico, optimización estructural y logística de vaciado.
"""

import os
import argparse
import numpy as np
import pandas as pd
from tabulate import tabulate

from src.calculo_volumen import (
    calcular_propiedades_iniciales,
    calcular_geometria_columna,
    calcular_acero_columna
)
from src.optimizador_proceso import (
    ejecutar_optimizacion_dataset,
    optimizar_columna_individual
)
from src.dosificacion import (
    cuantificar_materiales,
    optimizar_logistica_vaciado,
    obtener_parametros_fc,
    COSTO_ACERO_KG,
    COSTO_ENCOFRADO_M2
)

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_DATOS = os.path.join(DIRECTORIO_ACTUAL, "data")
RUTA_CSV_ENTRADA = os.path.join(RUTA_DATOS, "columnas_entrada.csv")
RUTA_CSV_SALIDA = os.path.join(RUTA_DATOS, "columnas_optimizadas.csv")
RUTA_CSV_LOGISTICA = os.path.join(RUTA_DATOS, "resumen_vaciado_concreto.csv")


def asegurar_datos_ejemplo():
    """Crea el directorio data y un archivo CSV de ejemplo si no existe."""
    os.makedirs(RUTA_DATOS, exist_ok=True)
    if not os.path.exists(RUTA_CSV_ENTRADA):
        print(f"[INFO] Creando dataset de ejemplo en {RUTA_CSV_ENTRADA}...")
        datos_base = {
            "columna_id": ["C-101", "C-102", "C-103", "C-104", "C-201", "C-202", "C-203", "C-204", "C-301", "C-302", "C-303", "C-304"],
            "nivel": ["Piso 1", "Piso 1", "Piso 1", "Piso 1", "Piso 2", "Piso 2", "Piso 2", "Piso 2", "Piso 3", "Piso 3", "Piso 3", "Piso 3"],
            "tipo_seccion": ["rectangular", "rectangular", "rectangular", "circular", "rectangular", "rectangular", "rectangular", "circular", "rectangular", "rectangular", "rectangular", "circular"],
            "b_m": [0.60, 0.55, 0.50, 0.60, 0.55, 0.50, 0.45, 0.55, 0.50, 0.45, 0.40, 0.50],
            "h_m": [0.60, 0.70, 0.50, 0.60, 0.55, 0.65, 0.45, 0.55, 0.50, 0.55, 0.40, 0.50],
            "altura_H_m": [3.20, 3.20, 3.20, 3.20, 3.00, 3.00, 3.00, 3.00, 2.80, 2.80, 2.80, 2.80],
            "carga_axial_Pu_kN": [1650.0, 2100.0, 1200.0, 1400.0, 1250.0, 1600.0, 850.0, 1050.0, 800.0, 1050.0, 550.0, 700.0],
            "fc_kg_cm2": [280, 280, 280, 280, 210, 210, 210, 210, 210, 210, 210, 210],
            "cuantia_inicial": [0.025, 0.025, 0.020, 0.020, 0.025, 0.025, 0.020, 0.020, 0.020, 0.020, 0.015, 0.018]
        }
        df_base = pd.DataFrame(datos_base)
        df_base.to_csv(RUTA_CSV_ENTRADA, index=False)


def procesar_flujo_completo(ruta_csv: str = RUTA_CSV_ENTRADA):
    """
    Ejecuta el ciclo de vida completo del cálculo y optimización:
    1. Carga de CSV con Pandas.
    2. Cálculos volumétricos y estructurales con NumPy y Pandas.
    3. Optimización ACI 318 dimensional y de cuantía.
    4. Cuantificación de insumos (cemento, agregados, agua).
    5. Optimización logística de despacho de mixers.
    6. Exportación de CSVs y reporte formateado.
    """
    print("=" * 80)
    print("  OPTIMIZADOR DE PROCESO Y VOLUMEN DE COLUMNAS - INGENIERÍA CIVIL")
    print("=" * 80)
    print(f"[*] Leyendo archivo de entrada: {ruta_csv}")
    df_entrada = pd.read_csv(ruta_csv)
    print(f"[✓] {len(df_entrada)} columnas cargadas exitosamente.\n")

    # 1. Propiedades iniciales
    print("[*] Calculando áreas, volúmenes, encofrado y costos iniciales (NumPy/Pandas)...")
    df_calculado = calcular_propiedades_iniciales(df_entrada)

    # 2. Optimización dimensional y de refuerzo
    print("[*] Ejecutando optimización de dimensiones y cuantías con ACI 318...")
    df_opt = ejecutar_optimizacion_dataset(df_calculado)

    # 3. Cuantificación de materiales detallada
    df_opt = cuantificar_materiales(df_opt, sufijo_volumen="volumen_opt_m3")

    # 4. Guardar archivo CSV optimizado
    df_opt.to_csv(RUTA_CSV_SALIDA, index=False)
    print(f"[✓] Archivo de resultados generado: {RUTA_CSV_SALIDA}")

    # 5. Optimización logística de vaciado
    df_logistica = optimizar_logistica_vaciado(df_opt, columna_volumen="volumen_opt_m3")
    df_logistica.to_csv(RUTA_CSV_LOGISTICA, index=False)
    print(f"[✓] Archivo logístico generado: {RUTA_CSV_LOGISTICA}\n")

    # 6. Reportes y Resúmenes Estadísticos con Pandas
    vol_ini_total = df_opt["volumen_inicial_m3"].sum()
    vol_opt_total = df_opt["volumen_opt_m3"].sum()
    ahorro_vol = vol_ini_total - vol_opt_total
    porc_vol = (ahorro_vol / vol_ini_total) * 100.0

    costo_ini_total = df_opt["costo_inicial_usd"].sum()
    costo_opt_total = df_opt["costo_opt_usd"].sum()
    ahorro_costo = costo_ini_total - costo_opt_total
    porc_costo = (ahorro_costo / costo_ini_total) * 100.0

    co2_ahorro_total = df_opt["ahorro_co2_kg"].sum()
    bolsas_cemento_total = df_opt["cemento_bolsas"].sum()
    acero_opt_total = df_opt["acero_opt_kg"].sum()

    # Tabla resumen por columna (primeras y representativas)
    columnas_mostrar = [
        "columna_id", "nivel", "tipo_seccion",
        "b_m", "h_m", "volumen_inicial_m3",
        "b_opt_m", "h_opt_m", "volumen_opt_m3",
        "ahorro_volumen_m3", "porc_ahorro_costo"
    ]
    df_tabla = df_opt[columnas_mostrar].copy()
    df_tabla.columns = [
        "Columna", "Nivel", "Tipo",
        "b ini (m)", "h ini (m)", "Vol ini (m³)",
        "b opt (m)", "h opt (m)", "Vol opt (m³)",
        "Δ Vol (m³)", "Ahorro ($%)"
    ]

    print("=" * 80)
    print("  TABLA COMPARATIVA: DISEÑO INICIAL vs DISEÑO OPTIMIZADO")
    print("=" * 80)
    print(tabulate(df_tabla, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 80)
    print("  RESUMEN LOGÍSTICO DE VACIADO DE CONCRETO POR NIVEL (MIXERS 8 m³)")
    print("=" * 80)
    print(tabulate(df_logistica, headers="keys", tablefmt="fancy_grid", showindex=False))

    print("\n" + "=" * 80)
    print("  MÉTRICAS EJECUTIVAS GLOBALES DEL PROCESO")
    print("=" * 80)
    print(f" • Volumen total inicial de concreto : {vol_ini_total:10.2f} m³")
    print(f" • Volumen total optimizado          : {vol_opt_total:10.2f} m³")
    print(f" • Reducción neta de concreto        : {ahorro_vol:10.2f} m³  (-{porc_vol:.1f}%)")
    print(f" • Costo inicial proyectado          : ${costo_ini_total:10.2f} USD")
    print(f" • Costo optimizado final            : ${costo_opt_total:10.2f} USD")
    print(f" • AHORRO ECONÓMICO TOTAL            : ${ahorro_costo:10.2f} USD  (-{porc_costo:.1f}%)")
    print(f" • Reducción de Emisiones CO₂eq      : {co2_ahorro_total:10.2f} kg CO₂")
    print(f" • Total Cemento requerido           : {bolsas_cemento_total:10.1f} bolsas (42.5 kg)")
    print(f" • Total Acero de refuerzo           : {acero_opt_total:10.1f} kg")
    print("=" * 80 + "\n")


def calcular_columna_individual_cli(
    col_id: str,
    seccion: str,
    b: float,
    h: float,
    H: float,
    pu: float,
    fc: int,
    agregar_al_csv: bool = False
):
    """
    Calcula el volumen y optimización de una columna específica ingresada por el usuario
    (cumple con el ejemplo: registro de columna y cálculo de volumen en función de dimensiones).
    """
    print("\n" + "=" * 70)
    print(f"  CÁLCULO Y OPTIMIZACIÓN INDIVIDUAL DE COLUMNA: {col_id}")
    print("=" * 70)
    
    ag_ini, vol_ini, enc_ini = calcular_geometria_columna(seccion, b, h, H)
    cuantia_def = 0.020
    acero_ini = calcular_acero_columna(ag_ini, H, cuantia_def)
    params_fc = obtener_parametros_fc(fc)
    costo_ini = (vol_ini * params_fc["costo_concreto_m3"]) + (acero_ini * COSTO_ACERO_KG) + (enc_ini * COSTO_ENCOFRADO_M2)

    print(f" [1] Dimensiones ingresadas   : {b:.2f} m x {h:.2f} m (H = {H:.2f} m, {seccion})")
    print(f" [2] Resistencia f'c          : {fc} kg/cm²")
    print(f" [3] Carga axial factorizada  : {pu:.1f} kN")
    print(f" [4] Área de sección Ag       : {ag_ini:.4f} m²")
    print(f" [5] VOLUMEN DE CONCRETO      : {vol_ini:.3f} m³")
    print(f" [6] Área de encofrado        : {enc_ini:.2f} m²")
    print(f" [7] Acero estimado inicial   : {acero_ini:.2f} kg")
    print(f" [8] Costo estimado inicial   : ${costo_ini:.2f} USD")

    # Optimización
    opt = optimizar_columna_individual(
        tipo_seccion=seccion,
        altura_h=H,
        pu_kn=pu,
        fc_kg_cm2=fc,
        b_actual=b,
        h_actual=h
    )

    ahorro_vol = vol_ini - opt["volumen_opt_m3"]
    ahorro_costo = costo_ini - opt["costo_opt_usd"]
    porc_ahorro = (ahorro_costo / costo_ini) * 100.0 if costo_ini > 0 else 0.0

    print("\n  >>> RESULTADO DE OPTIMIZACIÓN ACI 318 <<<")
    print(f"  * Sección óptima recomendada: {opt['b_opt_m']:.2f} m x {opt['h_opt_m']:.2f} m")
    print(f"  * Cuantía óptima de acero   : {opt['cuantia_opt'] * 100:.2f}% (Acero: {opt['acero_opt_kg']:.2f} kg)")
    print(f"  * Volumen optimizado        : {opt['volumen_opt_m3']:.3f} m³ (Ahorro: {ahorro_vol:.3f} m³)")
    print(f"  * Capacidad φPn resistente  : {opt['phi_Pn_capacidad_kN']:.1f} kN (>= {pu:.1f} kN OK)")
    print(f"  * Costo optimizado          : ${opt['costo_opt_usd']:.2f} USD")
    print(f"  * AHORRO ESTIMADO           : ${ahorro_costo:.2f} USD ({porc_ahorro:.1f}%)")
    print("=" * 70)

    if agregar_al_csv:
        nueva_fila = {
            "columna_id": col_id,
            "nivel": "Personalizado",
            "tipo_seccion": seccion,
            "b_m": b,
            "h_m": h,
            "altura_H_m": H,
            "carga_axial_Pu_kN": pu,
            "fc_kg_cm2": fc,
            "cuantia_inicial": cuantia_def
        }
        df_actual = pd.read_csv(RUTA_CSV_ENTRADA)
        df_actual = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
        df_actual.to_csv(RUTA_CSV_ENTRADA, index=False)
        print(f"[✓] Columna {col_id} añadida exitosamente a {RUTA_CSV_ENTRADA}.\n")


def modo_interactivo():
    """Modo interactivo en consola para ingresar datos de una columna."""
    print("\n--- MODO INTERACTIVO DE REGISTRO DE COLUMNA ---")
    col_id = input("Ingrese el identificador/número de columna (ej. C-101): ").strip() or "C-NEW"
    seccion = input("Tipo de sección (rectangular / circular) [def: rectangular]: ").strip().lower() or "rectangular"
    
    if seccion == "circular":
        diametro = float(input("Diámetro en metros (ej. 0.50): "))
        b, h = diametro, diametro
    else:
        b = float(input("Ancho de la base b en metros (ej. 0.40): "))
        h = float(input("Peralte h en metros (ej. 0.50): "))

    H = float(input("Altura libre H en metros (ej. 3.00): "))
    pu = float(input("Carga axial última Pu en kN (ej. 1200): "))
    fc = int(input("Resistencia del concreto f'c en kg/cm² (210, 280, 350) [def: 210]: ") or "210")
    
    resp_guardar = input("¿Desea guardar esta columna en el archivo CSV de entrada? (s/n) [def: s]: ").strip().lower()
    guardar = resp_guardar != "n"

    calcular_columna_individual_cli(col_id, seccion, b, h, H, pu, fc, agregar_al_csv=guardar)


def main():
    parser = argparse.ArgumentParser(description="Optimización de Volúmenes y Procesos de Columnas en Ingeniería Civil")
    parser.add_argument("--archivo", type=str, default=RUTA_CSV_ENTRADA, help="Ruta al archivo CSV con datos de columnas")
    parser.add_argument("--interactivo", action="store_true", help="Iniciar en modo interactivo para ingresar una columna")
    parser.add_argument("--columna", type=str, help="ID de columna para cálculo rápido")
    parser.add_argument("--seccion", type=str, default="rectangular", choices=["rectangular", "circular"], help="Tipo de sección")
    parser.add_argument("--b", type=float, help="Base o diámetro (m)")
    parser.add_argument("--h", type=float, help="Peralte (m)")
    parser.add_argument("--altura", type=float, help="Altura H (m)")
    parser.add_argument("--pu", type=float, default=1000.0, help="Carga axial Pu (kN)")
    parser.add_argument("--fc", type=int, default=210, help="Resistencia f'c (kg/cm²)")
    parser.add_argument("--guardar", action="store_true", help="Guardar la columna en el CSV de entrada")

    args = parser.parse_args()

    asegurar_datos_ejemplo()

    if args.interactivo:
        modo_interactivo()
    elif args.columna and args.b and args.altura:
        h_val = args.h if args.h else args.b
        calcular_columna_individual_cli(
            args.columna, args.seccion, args.b, h_val, args.altura, args.pu, args.fc, agregar_al_csv=args.guardar
        )
    else:
        procesar_flujo_completo(args.archivo)


if __name__ == "__main__":
    main()
