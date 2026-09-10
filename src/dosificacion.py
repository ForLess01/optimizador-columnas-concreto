"""
Módulo de Dosificación y Parámetros Económicos / Materiales para Concreto Armado.
Define tablas de mezclas según f'c (ACI 211), costos unitarios y logística de mixers.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

# Parámetros de dosificación estándar por m³ de concreto según resistencia f'c (kg/cm²)
# Fuentes referenciales: ACI 211 / Tablas de dosificación CAPECO
DOSIFICACION_POR_FC: Dict[int, Dict[str, float]] = {
    175: {
        "cemento_bolsas": 8.43,   # Bolsas de 42.5 kg
        "arena_m3": 0.54,         # Agregado fino m³
        "piedra_m3": 0.55,        # Agregado grueso m³
        "agua_m3": 0.185,         # Agua m³
        "costo_concreto_m3": 95.0, # USD por m³
        "co2_kg_m3": 310.0        # kg CO2eq / m³
    },
    210: {
        "cemento_bolsas": 9.73,
        "arena_m3": 0.52,
        "piedra_m3": 0.53,
        "agua_m3": 0.186,
        "costo_concreto_m3": 110.0,
        "co2_kg_m3": 350.0
    },
    280: {
        "cemento_bolsas": 13.34,
        "arena_m3": 0.45,
        "piedra_m3": 0.51,
        "agua_m3": 0.185,
        "costo_concreto_m3": 130.0,
        "co2_kg_m3": 410.0
    },
    350: {
        "cemento_bolsas": 16.50,
        "arena_m3": 0.42,
        "piedra_m3": 0.50,
        "agua_m3": 0.180,
        "costo_concreto_m3": 155.0,
        "co2_kg_m3": 470.0
    }
}

# Costos unitarios de materiales y mano de obra
COSTO_ACERO_KG = 1.25          # USD/kg acero corrugado grado 60 (fy = 420 MPa)
COSTO_ENCOFRADO_M2 = 18.50     # USD/m² encofrado y desencofrado de columnas
DENSIDAD_ACERO_KG_M3 = 7850.0  # kg/m³
CO2_ACERO_KG = 1.80            # kg CO2eq por kg de acero

# Capacidad nominal camión mixer (concretera)
CAPACIDAD_MIXER_M3 = 8.0
COSTO_FLETE_MIXER = 75.0       # Costo de despacho/flete por viaje de mixer
MERMA_BOMBEO_PORCENTAJE = 0.03 # 3% merma típica en tubería y bombeo


def obtener_parametros_fc(fc: int) -> Dict[str, float]:
    """Obtiene los parámetros de dosificación para el f'c más cercano disponible."""
    disponibles = np.array(list(DOSIFICACION_POR_FC.keys()))
    cercano = disponibles[np.argmin(np.abs(disponibles - fc))]
    return DOSIFICACION_POR_FC[int(cercano)]


def cuantificar_materiales(df_columnas: pd.DataFrame, sufijo_volumen: Optional[str] = None) -> pd.DataFrame:
    """
    Cuantifica los insumos necesarios (cemento, arena, piedra, agua) y huella CO2
    a partir del volumen de concreto calculado en un DataFrame de pandas.
    """
    df = df_columnas.copy()

    col_vol = sufijo_volumen
    if col_vol is None or col_vol not in df.columns:
        if "volumen_opt_m3" in df.columns:
            col_vol = "volumen_opt_m3"
        elif "volumen_inicial_m3" in df.columns:
            col_vol = "volumen_inicial_m3"
        elif "volumen_m3" in df.columns:
            col_vol = "volumen_m3"
        else:
            raise KeyError("No se encontró columna de volumen en el DataFrame.")

    # Factores vectorizados por fila según f'c
    factores_cemento = np.array([obtener_parametros_fc(fc)["cemento_bolsas"] for fc in df["fc_kg_cm2"]])
    factores_arena = np.array([obtener_parametros_fc(fc)["arena_m3"] for fc in df["fc_kg_cm2"]])
    factores_piedra = np.array([obtener_parametros_fc(fc)["piedra_m3"] for fc in df["fc_kg_cm2"]])
    factores_agua = np.array([obtener_parametros_fc(fc)["agua_m3"] for fc in df["fc_kg_cm2"]])
    factores_co2 = np.array([obtener_parametros_fc(fc)["co2_kg_m3"] for fc in df["fc_kg_cm2"]])

    volumen = df[col_vol].values

    df["cemento_bolsas"] = np.round(volumen * factores_cemento, 1)
    df["arena_m3"] = np.round(volumen * factores_arena, 2)
    df["piedra_m3"] = np.round(volumen * factores_piedra, 2)
    df["agua_m3"] = np.round(volumen * factores_agua, 2)
    df["co2_concreto_kg"] = np.round(volumen * factores_co2, 1)

    return df


def optimizar_logistica_vaciado(df_columnas: pd.DataFrame, columna_volumen: Optional[str] = None) -> pd.DataFrame:
    """
    Optimiza el proceso de despacho y vaciado de concreto premezclado agrupado por nivel/piso.
    Calcula número de camiones mixer requeridos, volumen parcial y mermas.
    """
    col_vol = columna_volumen
    if col_vol is None or col_vol not in df_columnas.columns:
        if "volumen_opt_m3" in df_columnas.columns:
            col_vol = "volumen_opt_m3"
        elif "volumen_inicial_m3" in df_columnas.columns:
            col_vol = "volumen_inicial_m3"
        elif "volumen_m3" in df_columnas.columns:
            col_vol = "volumen_m3"
        else:
            raise KeyError("No se encontró columna de volumen en el DataFrame.")

    resumen_niveles = df_columnas.groupby("nivel").agg(
        num_columnas=("columna_id", "count"),
        volumen_neto_m3=(col_vol, "sum")
    ).reset_index()

    # Considerar merma técnica de vaciado (3%)
    vol_neto = resumen_niveles["volumen_neto_m3"].values
    vol_con_merma = vol_neto * (1.0 + MERMA_BOMBEO_PORCENTAJE)

    # Cálculo logístico de camiones
    camiones_completos = np.floor(vol_con_merma / CAPACIDAD_MIXER_M3).astype(int)
    vol_restante = np.mod(vol_con_merma, CAPACIDAD_MIXER_M3)
    camiones_adicionales = np.where(vol_restante > 0.05, 1, 0)
    total_camiones = camiones_completos + camiones_adicionales

    resumen_niveles["volumen_con_merma_m3"] = np.round(vol_con_merma, 2)
    resumen_niveles["camiones_completos_8m3"] = camiones_completos
    resumen_niveles["volumen_ultimo_mixer_m3"] = np.round(vol_restante, 2)
    resumen_niveles["total_viajes_mixer"] = total_camiones
    resumen_niveles["costo_flete_total_usd"] = total_camiones * COSTO_FLETE_MIXER

    return resumen_niveles
