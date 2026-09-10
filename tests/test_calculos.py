"""
Pruebas Unitarias para el Optimizador de Columnas de Concreto Armado.
"""

import pytest
import numpy as np
import pandas as pd
from src.calculo_volumen import (
    calcular_geometria_columna,
    calcular_acero_columna,
    calcular_propiedades_iniciales
)
from src.optimizador_proceso import (
    optimizar_columna_individual,
    ejecutar_optimizacion_dataset
)
from src.dosificacion import (
    obtener_parametros_fc,
    cuantificar_materiales,
    optimizar_logistica_vaciado
)


def test_geometria_rectangular():
    b, h, H = 0.40, 0.50, 3.00
    ag, vol, enc = calcular_geometria_columna("rectangular", b, h, H)
    assert np.isclose(ag, 0.20)
    assert np.isclose(vol, 0.60)
    assert np.isclose(enc, 2.0 * (0.40 + 0.50) * 3.0)


def test_geometria_circular():
    D, H = 0.50, 3.00
    ag, vol, enc = calcular_geometria_columna("circular", D, D, H)
    esperado_ag = np.pi * ((D / 2.0) ** 2)
    assert np.isclose(ag, esperado_ag)
    assert np.isclose(vol, esperado_ag * H)
    assert np.isclose(enc, np.pi * D * H)


def test_calculo_acero():
    ag = 0.20
    H = 3.00
    cuantia = 0.02
    peso = calcular_acero_columna(ag, H, cuantia)
    # peso = (0.02 * 0.20) * 3.00 * 7850 * 1.15 * 1.25
    esperado = (0.02 * 0.20) * 3.00 * 7850.0 * 1.15 * 1.25
    assert np.isclose(peso, esperado)


def test_parametros_fc():
    params = obtener_parametros_fc(210)
    assert params["cemento_bolsas"] == 9.73
    assert params["costo_concreto_m3"] == 110.0


def test_optimizacion_resistencia_estructural():
    pu = 1200.0  # kN
    fc = 280     # kg/cm²
    H = 3.00     # m
    resultado = optimizar_columna_individual(
        tipo_seccion="rectangular",
        altura_h=H,
        pu_kn=pu,
        fc_kg_cm2=fc,
        b_actual=0.50,
        h_actual=0.50
    )
    # La capacidad resistente nominal reducida phi*Pn debe ser mayor o igual a Pu
    assert resultado["phi_Pn_capacidad_kN"] >= pu
    # Las dimensiones deben ser factibles (>= 0.25 m)
    assert resultado["b_opt_m"] >= 0.25
    assert resultado["h_opt_m"] >= 0.25
    # La cuantía debe estar en rango ACI [1%, 4%]
    assert 0.01 <= resultado["cuantia_opt"] <= 0.04


def test_flujo_dataframe_completo():
    df_test = pd.DataFrame([{
        "columna_id": "C-T1",
        "nivel": "Piso 1",
        "tipo_seccion": "rectangular",
        "b_m": 0.60,
        "h_m": 0.60,
        "altura_H_m": 3.00,
        "carga_axial_Pu_kN": 1000.0,
        "fc_kg_cm2": 210,
        "cuantia_inicial": 0.025
    }])

    df_calc = calcular_propiedades_iniciales(df_test)
    assert "volumen_inicial_m3" in df_calc.columns
    assert df_calc["volumen_inicial_m3"].iloc[0] == 1.08

    df_opt = ejecutar_optimizacion_dataset(df_calc)
    assert "volumen_opt_m3" in df_opt.columns
    assert df_opt["volumen_opt_m3"].iloc[0] < df_opt["volumen_inicial_m3"].iloc[0]
    assert df_opt["ahorro_volumen_m3"].iloc[0] > 0
    assert df_opt["ahorro_costo_usd"].iloc[0] > 0

    df_mat = cuantificar_materiales(df_opt)
    assert "cemento_bolsas" in df_mat.columns
    assert df_mat["cemento_bolsas"].iloc[0] > 0

    df_log = optimizar_logistica_vaciado(df_opt)
    assert len(df_log) == 1
    assert df_log["total_viajes_mixer"].iloc[0] >= 1

def test_calculo_columna_cli():
    # Test column C-501
    ag, vol, enc = calcular_geometria_columna("rectangular", 0.40, 0.50, 3.20)
    opt = optimizar_columna_individual("rectangular", 3.20, 1100.0, 280, 0.40, 0.50)
    assert opt["phi_Pn_capacidad_kN"] >= 1100.0
    assert opt["volumen_opt_m3"] < vol
