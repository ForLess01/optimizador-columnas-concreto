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
    os.makedirs(RUTA_DATOS, exist_ok=True)
    if not os.path.exists(RUTA_CSV_ENTRADA):
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
    print("=" * 80)
    print("  CALCULO Y OPTIMIZACION DE COLUMNAS DE CONCRETO")
    print("=" * 80)
    df_entrada = pd.read_csv(ruta_csv)
    print(f"Cargadas {len(df_entrada)} columnas desde {ruta_csv}\n")

    df_calculado = calcular_propiedades_iniciales(df_entrada)
    df_opt = ejecutar_optimizacion_dataset(df_calculado)
    df_opt = cuantificar_materiales(df_opt, sufijo_volumen="volumen_opt_m3")

    df_opt.to_csv(RUTA_CSV_SALIDA, index=False)
    print(f"Resultados guardados en: {RUTA_CSV_SALIDA}")

    df_logistica = optimizar_logistica_vaciado(df_opt, columna_volumen="volumen_opt_m3")
    df_logistica.to_csv(RUTA_CSV_LOGISTICA, index=False)
    print(f"Resumen logistico guardado en: {RUTA_CSV_LOGISTICA}\n")

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

    columnas_mostrar = [
        "columna_id", "nivel", "tipo_seccion",
        "b_m", "h_m", "volumen_inicial_m3",
        "b_opt_m", "h_opt_m", "volumen_opt_m3",
        "ahorro_volumen_m3", "porc_ahorro_costo"
    ]
    df_tabla = df_opt[columnas_mostrar].copy()
    df_tabla.columns = [
        "Columna", "Nivel", "Tipo",
        "b ini (m)", "h ini (m)", "Vol ini (m3)",
        "b opt (m)", "h opt (m)", "Vol opt (m3)",
        "Dif Vol (m3)", "Ahorro (%)"
    ]

    print("=" * 80)
    print("  COMPARATIVA: DISENO INICIAL vs DISENO OPTIMIZADO")
    print("=" * 80)
    print(tabulate(df_tabla, headers="keys", tablefmt="grid", showindex=False))

    print("\n" + "=" * 80)
    print("  LOGISTICA DE VACIADO POR NIVEL (MIXERS 8 m3)")
    print("=" * 80)
    print(tabulate(df_logistica, headers="keys", tablefmt="grid", showindex=False))

    print("\n" + "=" * 80)
    print("  RESUMEN TOTAL")
    print("=" * 80)
    print(f" Volumen inicial total          : {vol_ini_total:.2f} m3")
    print(f" Volumen optimizado total       : {vol_opt_total:.2f} m3")
    print(f" Reduccion de volumen           : {ahorro_vol:.2f} m3 (-{porc_vol:.1f}%)")
    print(f" Costo inicial estimado         : ${costo_ini_total:.2f} USD")
    print(f" Costo optimizado               : ${costo_opt_total:.2f} USD")
    print(f" Ahorro economico               : ${ahorro_costo:.2f} USD (-{porc_costo:.1f}%)")
    print(f" Reduccion CO2eq                : {co2_ahorro_total:.2f} kg CO2")
    print(f" Total cemento estimado         : {bolsas_cemento_total:.1f} bolsas (42.5 kg)")
    print(f" Total acero de refuerzo        : {acero_opt_total:.1f} kg")
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
    print("\n" + "=" * 70)
    print(f"  CALCULO INDIVIDUAL DE COLUMNA: {col_id}")
    print("=" * 70)
    
    ag_ini, vol_ini, enc_ini = calcular_geometria_columna(seccion, b, h, H)
    cuantia_def = 0.020
    acero_ini = calcular_acero_columna(ag_ini, H, cuantia_def)
    params_fc = obtener_parametros_fc(fc)
    costo_ini = (vol_ini * params_fc["costo_concreto_m3"]) + (acero_ini * COSTO_ACERO_KG) + (enc_ini * COSTO_ENCOFRADO_M2)

    print(f" Dimensiones ingresadas   : {b:.2f} m x {h:.2f} m (H = {H:.2f} m, {seccion})")
    print(f" Resistencia f'c          : {fc} kg/cm2")
    print(f" Carga axial Pu           : {pu:.1f} kN")
    print(f" Area de seccion Ag       : {ag_ini:.4f} m2")
    print(f" Volumen de concreto      : {vol_ini:.3f} m3")
    print(f" Area de encofrado        : {enc_ini:.2f} m2")
    print(f" Acero estimado inicial   : {acero_ini:.2f} kg")
    print(f" Costo inicial            : ${costo_ini:.2f} USD")

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

    print("\n  OPTIMIZACION ACI 318:")
    print(f"  Seccion optima          : {opt['b_opt_m']:.2f} m x {opt['h_opt_m']:.2f} m")
    print(f"  Cuantia optima          : {opt['cuantia_opt'] * 100:.2f}% (Acero: {opt['acero_opt_kg']:.2f} kg)")
    print(f"  Volumen optimizado      : {opt['volumen_opt_m3']:.3f} m3 (Ahorro: {ahorro_vol:.3f} m3)")
    print(f"  Capacidad phi*Pn        : {opt['phi_Pn_capacidad_kN']:.1f} kN")
    print(f"  Costo optimizado        : ${opt['costo_opt_usd']:.2f} USD")
    print(f"  Ahorro                  : ${ahorro_costo:.2f} USD ({porc_ahorro:.1f}%)")
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
        print(f"Columna {col_id} agregada a {RUTA_CSV_ENTRADA}.\n")


def modo_interactivo():
    print("\nREGISTRO DE COLUMNA")
    col_id = input("Identificador de columna (ej. C-101): ").strip() or "C-NEW"
    seccion = input("Tipo de seccion (rectangular / circular) [def: rectangular]: ").strip().lower() or "rectangular"
    
    if seccion == "circular":
        diametro = float(input("Diametro en metros (ej. 0.50): "))
        b, h = diametro, diametro
    else:
        b = float(input("Base b en metros (ej. 0.40): "))
        h = float(input("Peralte h en metros (ej. 0.50): "))

    H = float(input("Altura libre H en metros (ej. 3.00): "))
    pu = float(input("Carga axial Pu en kN (ej. 1200): "))
    fc = int(input("Resistencia f'c en kg/cm2 (210, 280, 350) [def: 210]: ") or "210")
    
    resp_guardar = input("Guardar en CSV? (s/n) [def: s]: ").strip().lower()
    guardar = resp_guardar != "n"

    calcular_columna_individual_cli(col_id, seccion, b, h, H, pu, fc, agregar_al_csv=guardar)


def main():
    parser = argparse.ArgumentParser(description="Calculo de volumen y optimizacion de columnas de concreto")
    parser.add_argument("--archivo", type=str, default=RUTA_CSV_ENTRADA, help="Ruta al archivo CSV de entrada")
    parser.add_argument("--interactivo", action="store_true", help="Modo interactivo en terminal")
    parser.add_argument("--columna", type=str, help="ID de columna")
    parser.add_argument("--seccion", type=str, default="rectangular", choices=["rectangular", "circular"], help="Tipo de seccion")
    parser.add_argument("--b", type=float, help="Base o diametro (m)")
    parser.add_argument("--h", type=float, help="Peralte (m)")
    parser.add_argument("--altura", type=float, help="Altura H (m)")
    parser.add_argument("--pu", type=float, default=1000.0, help="Carga axial Pu (kN)")
    parser.add_argument("--fc", type=int, default=210, help="Resistencia f'c (kg/cm2)")
    parser.add_argument("--guardar", action="store_true", help="Guardar columna en el CSV")

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
