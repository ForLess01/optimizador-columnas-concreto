from typing import Dict, Any
import numpy as np
import pandas as pd
from .dosificacion import (
    COSTO_ACERO_KG,
    COSTO_ENCOFRADO_M2,
    DENSIDAD_ACERO_KG_M3,
    CO2_ACERO_KG,
    obtener_parametros_fc
)
from .calculo_volumen import calcular_geometria_columna, calcular_acero_columna


def optimizar_columna_individual(
    tipo_seccion: str,
    altura_h: float,
    pu_kn: float,
    fc_kg_cm2: int,
    b_actual: float,
    h_actual: float
) -> Dict[str, Any]:
    fc_params = obtener_parametros_fc(fc_kg_cm2)
    costo_conc_m3 = fc_params["costo_concreto_m3"]
    co2_conc_m3 = fc_params["co2_kg_m3"]
    
    fc_kpa = fc_kg_cm2 * 98.0665
    fy_kpa = 420000.0

    tipo = str(tipo_seccion).strip().lower()

    if tipo == "circular":
        phi = 0.75
        alpha = 0.85
        diametros = np.arange(0.25, 1.25, 0.05)
        cuantias = np.arange(0.01, 0.036, 0.002)
        
        D_grid, rho_grid = np.meshgrid(diametros, cuantias)
        D_flat = D_grid.flatten()
        rho_flat = rho_grid.flatten()

        ag_flat = (np.pi / 4.0) * (D_flat ** 2)
        ast_flat = rho_flat * ag_flat

        phi_pn = phi * alpha * (0.85 * fc_kpa * (ag_flat - ast_flat) + fy_kpa * ast_flat)
        mascara_valida = phi_pn >= pu_kn
        
        if not np.any(mascara_valida):
            d_opt, rho_opt = b_actual, 0.025
        else:
            D_valid = D_flat[mascara_valida]
            rho_valid = rho_flat[mascara_valida]
            ag_valid = ag_flat[mascara_valida]
            ast_valid = ast_flat[mascara_valida]

            vol_valid = ag_valid * altura_h
            perimetro_valid = np.pi * D_valid
            enc_valid = perimetro_valid * altura_h
            acero_kg_valid = ast_valid * altura_h * DENSIDAD_ACERO_KG_M3 * 1.15 * 1.25

            costo_valid = (
                vol_valid * costo_conc_m3 +
                acero_kg_valid * COSTO_ACERO_KG +
                enc_valid * COSTO_ENCOFRADO_M2
            )

            idx_opt = np.argmin(costo_valid)
            d_opt = float(D_valid[idx_opt])
            rho_opt = float(rho_valid[idx_opt])

        b_opt, h_opt = d_opt, d_opt

    else:
        phi = 0.65
        alpha = 0.80

        b_vals = np.arange(0.25, 1.05, 0.05)
        h_vals = np.arange(0.25, 1.05, 0.05)
        rho_vals = np.arange(0.01, 0.036, 0.002)

        B_grid, H_grid, RHO_grid = np.meshgrid(b_vals, h_vals, rho_vals, indexing="ij")
        B_flat = B_grid.flatten()
        H_flat = H_grid.flatten()
        RHO_flat = RHO_grid.flatten()

        aspect_ratio = B_flat / H_flat
        mascara_aspecto = (aspect_ratio >= 0.6) & (aspect_ratio <= 1.67)

        B_cand = B_flat[mascara_aspecto]
        H_cand = H_flat[mascara_aspecto]
        RHO_cand = RHO_flat[mascara_aspecto]

        ag_cand = B_cand * H_cand
        ast_cand = RHO_cand * ag_cand

        phi_pn = phi * alpha * (0.85 * fc_kpa * (ag_cand - ast_cand) + fy_kpa * ast_cand)
        mascara_valida = phi_pn >= pu_kn

        if not np.any(mascara_valida):
            b_opt, h_opt, rho_opt = b_actual, h_actual, 0.025
        else:
            B_valid = B_cand[mascara_valida]
            H_valid = H_cand[mascara_valida]
            RHO_valid = RHO_cand[mascara_valida]
            ag_valid = ag_cand[mascara_valida]
            ast_valid = ast_cand[mascara_valida]

            vol_valid = ag_valid * altura_h
            perimetro_valid = 2.0 * (B_valid + H_valid)
            enc_valid = perimetro_valid * altura_h
            acero_kg_valid = ast_valid * altura_h * DENSIDAD_ACERO_KG_M3 * 1.15 * 1.25

            costo_valid = (
                vol_valid * costo_conc_m3 +
                acero_kg_valid * COSTO_ACERO_KG +
                enc_valid * COSTO_ENCOFRADO_M2
            )

            idx_opt = np.argmin(costo_valid)
            b_opt = float(B_valid[idx_opt])
            h_opt = float(H_valid[idx_opt])
            rho_opt = float(RHO_valid[idx_opt])

    ag_opt, vol_opt, enc_opt = calcular_geometria_columna(tipo, b_opt, h_opt, altura_h)
    acero_opt = calcular_acero_columna(ag_opt, altura_h, rho_opt)
    
    costo_opt = (
        vol_opt * costo_conc_m3 +
        acero_opt * COSTO_ACERO_KG +
        enc_opt * COSTO_ENCOFRADO_M2
    )

    co2_opt = (vol_opt * co2_conc_m3) + (acero_opt * CO2_ACERO_KG)

    ast_final = rho_opt * ag_opt
    if tipo == "circular":
        phi_pn_final = 0.75 * 0.85 * (0.85 * fc_kpa * (ag_opt - ast_final) + fy_kpa * ast_final)
    else:
        phi_pn_final = 0.65 * 0.80 * (0.85 * fc_kpa * (ag_opt - ast_final) + fy_kpa * ast_final)

    return {
        "b_opt_m": round(b_opt, 2),
        "h_opt_m": round(h_opt, 2),
        "cuantia_opt": round(rho_opt, 4),
        "area_opt_m2": round(ag_opt, 4),
        "volumen_opt_m3": round(vol_opt, 3),
        "encofrado_opt_m2": round(enc_opt, 2),
        "acero_opt_kg": round(acero_opt, 2),
        "costo_opt_usd": round(costo_opt, 2),
        "co2_opt_kg": round(co2_opt, 2),
        "phi_Pn_capacidad_kN": round(phi_pn_final, 1)
    }


def ejecutar_optimizacion_dataset(df_inicial: pd.DataFrame) -> pd.DataFrame:
    df = df_inicial.copy()
    resultados_opt = []

    for _, fila in df.iterrows():
        opt = optimizar_columna_individual(
            tipo_seccion=fila["tipo_seccion"],
            altura_h=fila["altura_H_m"],
            pu_kn=fila["carga_axial_Pu_kN"],
            fc_kg_cm2=int(fila["fc_kg_cm2"]),
            b_actual=fila["b_m"],
            h_actual=fila["h_m"]
        )
        resultados_opt.append(opt)

    df_opt = pd.DataFrame(resultados_opt)
    df_combinado = pd.concat([df.reset_index(drop=True), df_opt], axis=1)

    v_ini = df_combinado["volumen_inicial_m3"].values
    v_opt = df_combinado["volumen_opt_m3"].values
    c_ini = df_combinado["costo_inicial_usd"].values
    c_opt = df_combinado["costo_opt_usd"].values
    co2_ini = df_combinado["co2_inicial_kg"].values
    co2_opt = df_combinado["co2_opt_kg"].values

    df_combinado["ahorro_volumen_m3"] = np.round(v_ini - v_opt, 3)
    df_combinado["porc_ahorro_volumen"] = np.round(((v_ini - v_opt) / np.maximum(v_ini, 1e-6)) * 100.0, 2)
    df_combinado["ahorro_costo_usd"] = np.round(c_ini - c_opt, 2)
    df_combinado["porc_ahorro_costo"] = np.round(((c_ini - c_opt) / np.maximum(c_ini, 1e-6)) * 100.0, 2)
    df_combinado["ahorro_co2_kg"] = np.round(co2_ini - co2_opt, 2)

    return df_combinado
