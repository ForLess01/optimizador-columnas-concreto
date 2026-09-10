from typing import Tuple
import numpy as np
import pandas as pd
from .dosificacion import (
    COSTO_ACERO_KG,
    COSTO_ENCOFRADO_M2,
    DENSIDAD_ACERO_KG_M3,
    CO2_ACERO_KG,
    obtener_parametros_fc
)


def calcular_geometria_columna(
    tipo_seccion: str,
    b: float,
    h: float,
    H: float
) -> Tuple[float, float, float]:
    tipo = str(tipo_seccion).strip().lower()
    if tipo == "circular":
        diametro = b
        radio = diametro / 2.0
        ag = np.pi * (radio ** 2)
        volumen = ag * H
        perimetro = np.pi * diametro
        area_encofrado = perimetro * H
    else:
        ag = b * h
        volumen = ag * H
        perimetro = 2.0 * (b + h)
        area_encofrado = perimetro * H

    return float(ag), float(volumen), float(area_encofrado)


def calcular_acero_columna(
    ag_m2: float,
    altura_m: float,
    cuantia: float
) -> float:
    area_acero_m2 = cuantia * ag_m2
    peso_longitudinal = area_acero_m2 * altura_m * DENSIDAD_ACERO_KG_M3 * 1.15
    peso_total = peso_longitudinal * 1.25
    return float(peso_total)


def calcular_propiedades_iniciales(df: pd.DataFrame) -> pd.DataFrame:
    df_out = df.copy()

    ags = []
    volumenes = []
    encofrados = []
    pesos_acero = []
    costos_totales = []
    co2_totales = []

    for _, fila in df_out.iterrows():
        ag, vol, a_enc = calcular_geometria_columna(
            fila["tipo_seccion"],
            fila["b_m"],
            fila["h_m"],
            fila["altura_H_m"]
        )
        p_acero = calcular_acero_columna(
            ag,
            fila["altura_H_m"],
            fila["cuantia_inicial"]
        )
        
        fc_params = obtener_parametros_fc(int(fila["fc_kg_cm2"]))
        costo_conc = vol * fc_params["costo_concreto_m3"]
        costo_ac = p_acero * COSTO_ACERO_KG
        costo_enc = a_enc * COSTO_ENCOFRADO_M2
        costo_total = costo_conc + costo_ac + costo_enc

        co2_conc = vol * fc_params["co2_kg_m3"]
        co2_ac = p_acero * CO2_ACERO_KG
        co2_total = co2_conc + co2_ac

        ags.append(round(ag, 4))
        volumenes.append(round(vol, 3))
        encofrados.append(round(a_enc, 2))
        pesos_acero.append(round(p_acero, 2))
        costos_totales.append(round(costo_total, 2))
        co2_totales.append(round(co2_total, 2))

    df_out["area_seccion_m2"] = np.array(ags)
    df_out["volumen_inicial_m3"] = np.array(volumenes)
    df_out["encofrado_inicial_m2"] = np.array(encofrados)
    df_out["acero_inicial_kg"] = np.array(pesos_acero)
    df_out["costo_inicial_usd"] = np.array(costos_totales)
    df_out["co2_inicial_kg"] = np.array(co2_totales)

    return df_out
