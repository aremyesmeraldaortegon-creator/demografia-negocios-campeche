"""
02_matching_demografia.py

Construye el panel de demografia de negocios de Campeche.

- Lee data/raw/campeche_2023.csv y campeche_2024.csv
- Normaliza fechas y claves textuales (nombre y ubicacion)
- Clasifica el sector turistico en 3 niveles (nucleo / ampliado / excluido)
- Clasifica la exposicion al Tren Maya (grupos A / B / C)
- Aplica el matching hibrido:
    1. Coincidencia por CLEE -> sobreviviente
    2. Si no hay match: regla de 3 variables (nombre, SCIAN, ubicacion).
       Si difieren <=1 -> sobreviviente; >=2 -> muerte + nacimiento
    3. Guarda fecha_alta normalizada como validacion auxiliar
- Guarda todo en data/denue.db (SQLite)
- Reporta totales y tasas por municipio, sector y grupo Tren Maya
"""

import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd


# ============================================================
# Configuracion
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "denue.db"

ANIOS = [2023, 2024]

MUNICIPIOS_CAMPECHE = {
    "001": "Calkini",
    "002": "Campeche",
    "003": "Carmen",
    "004": "Champoton",
    "005": "Hecelchakan",
    "006": "Hopelchen",
    "007": "Palizada",
    "008": "Tenabo",
    "009": "Escarcega",
    "010": "Calakmul",
    "011": "Candelaria",
    "012": "Seybaplaya",
    "013": "Dzitbalche",
}

# Grupos de exposicion al Tren Maya (ver seccion 1.3 del README)
GRUPO_TREN_MAYA = {
    "A": ["001", "002", "004", "005", "008", "009"],
    "B": ["003", "010", "011"],
    "C": ["006", "007", "012", "013"],
}

# Clasificacion del sector turistico por primeros 4 digitos del SCIAN
SCIAN_TURISMO = {
    "nucleo": ["7211", "7225", "5615"],
    "ampliado": ["7224", "7132", "7121"],
    "excluido": ["4871"],
}

COLUMNAS_UBICACION = [
    "cve_mun",
    "cve_loc",
    "tipo_vial",
    "nom_vial",
    "numero_ext",
    "tipo_asent",
    "nomb_asent",
    "cod_postal",
]

# Marcadores que vuelven a un nombre no informativo para el matching.
# Se excluyen del matching por nombre (pero no del matching por ubicacion).
GENERIC_MARKERS = [
    "sin nombre",
    "sin denominacion",
    "sin razon social",
    "sin giro",
    "sin numero",
    "sin nombre comercial",
    "anonimo",
    "no especificado",
    "no proporcionado",
    "no disponible",
]


# ============================================================
# Normalizacion y clasificacion
# ============================================================
def normalizar_texto(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    s = str(valor).lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def normalizar_fecha_alta(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    s = str(valor).strip()
    s = re.sub(r"\s+", "-", s)
    m = re.match(r"(\d{4})-(\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}"
    return s


def clasificar_turismo(scian4):
    if scian4 in SCIAN_TURISMO["nucleo"]:
        return "nucleo"
    if scian4 in SCIAN_TURISMO["ampliado"]:
        return "ampliado"
    if scian4 in SCIAN_TURISMO["excluido"]:
        return "excluido"
    return "resto"


def clasificar_grupo_tren(cve_mun):
    for grupo, municipios in GRUPO_TREN_MAYA.items():
        if cve_mun in municipios:
            return grupo
    return None


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["scian4"] = df["codigo_act"].str[:4]
    df["nombre_norm"] = df["nom_estab"].map(normalizar_texto)
    df["nombre_act_norm"] = df["nombre_act"].map(normalizar_texto)
    df["ubicacion_norm"] = (
        df[COLUMNAS_UBICACION]
        .fillna("")
        .astype(str)
        .apply(lambda fila: " ".join(fila), axis=1)
        .map(normalizar_texto)
    )
    df["fecha_alta_norm"] = df["fecha_alta"].map(normalizar_fecha_alta)
    df["sector_turismo"] = df["scian4"].map(clasificar_turismo)
    df["grupo_tren"] = df["cve_mun"].map(clasificar_grupo_tren)

    nombre_vacio = df["nombre_norm"] == ""
    nombre_igual_act = df["nombre_norm"] == df["nombre_act_norm"]
    patron_generico = "|".join(re.escape(m) for m in GENERIC_MARKERS)
    nombre_generico = df["nombre_norm"].str.contains(patron_generico, regex=True, na=False)
    df["nombre_valido"] = ~(nombre_vacio | nombre_igual_act | nombre_generico)
    return df


# ============================================================
# Matching hibrido
# ============================================================
def match_fuzzy(u24: pd.DataFrame, u23: pd.DataFrame):
    """Devuelve pares (posicion_24, posicion_23) con regla de 3 variables."""
    a = u24[["clee", "scian4", "nombre_norm", "nombre_valido", "ubicacion_norm"]].reset_index(drop=True)
    b = u23[["clee", "scian4", "nombre_norm", "nombre_valido", "ubicacion_norm"]].reset_index(drop=True)

    a_nom = a[a["nombre_valido"]]
    b_nom = b[b["nombre_valido"]]
    a_ubic = a[a["ubicacion_norm"] != ""]
    b_ubic = b[b["ubicacion_norm"] != ""]

    cn = a_nom[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(
        columns={"index": "i24"}
    )
    bn = b_nom[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(
        columns={"index": "i23"}
    )
    cn = cn.merge(bn, on=["scian4", "nombre_norm"], suffixes=("_24", "_23"))
    cn["nombre_eq"] = 1
    cn["ubic_eq"] = (cn["ubicacion_norm_24"] == cn["ubicacion_norm_23"]).astype(int)

    cu = a_ubic[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(
        columns={"index": "i24"}
    )
    bu = b_ubic[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(
        columns={"index": "i23"}
    )
    cu = cu.merge(bu, on=["scian4", "ubicacion_norm"], suffixes=("_24", "_23"))
    cu["ubic_eq"] = 1
    cu["nombre_eq"] = (cu["nombre_norm_24"] == cu["nombre_norm_23"]).astype(int)

    cands = pd.concat(
        [cn[["i24", "i23", "nombre_eq", "ubic_eq"]],
         cu[["i24", "i23", "nombre_eq", "ubic_eq"]]],
        ignore_index=True,
    )
    cands = cands.drop_duplicates(subset=["i24", "i23"])
    cands["score"] = cands["nombre_eq"] + cands["ubic_eq"]
    cands = cands.sort_values(["score", "i24", "i23"], ascending=[False, True, True])

    usados_24 = set()
    usados_23 = set()
    pares = []
    for fila in cands.itertuples(index=False):
        if fila.i24 in usados_24 or fila.i23 in usados_23:
            continue
        usados_24.add(fila.i24)
        usados_23.add(fila.i23)
        pares.append((fila.i24, fila.i23))
    return pares


# ============================================================
# Resumen
# ============================================================
def reportar(df23, df24, sobrevivientes, nacimientos, muertes):
    total_23 = len(df23)
    total_24 = len(df24)
    sobrevivientes_n = len(sobrevivientes)
    nacimientos_n = len(nacimientos)
    muertes_n = len(muertes)

    print("=" * 70)
    print("  RESULTADOS DEL MATCHING")
    print("=" * 70)
    print(f"  Unidades 2023:        {total_23:>8,}")
    print(f"  Unidades 2024:        {total_24:>8,}")
    print(f"  Sobrevivientes:       {sobrevivientes_n:>8,}")
    print(f"  Nacimientos:          {nacimientos_n:>8,}")
    print(f"  Muertes:              {muertes_n:>8,}")
    print()
    print("  Verificacion de consistencia:")
    print(f"    Sobrevivientes + Muertes  = {sobrevivientes_n + muertes_n:,} (debe ser {total_23:,})")
    print(f"    Sobrevivientes + Nacim.   = {sobrevivientes_n + nacimientos_n:,} (debe ser {total_24:,})")
    print()

    tipo_match = sobrevivientes["tipo_match"].value_counts()
    print("  Sobrevivientes por tipo de match:")
    for tipo, n in tipo_match.items():
        print(f"    {tipo:<8} {n:>8,}")
    print()

    print("=" * 70)
    print("  POR MUNICIPIO")
    print("=" * 70)
    print(f"  {'cve':<4} {'municipio':<14} {'U23':>7} {'U24':>7} {'N':>6} {'M':>6} {'S':>6} {'t.ent%':>7} {'t.sal%':>7} {'grupo':>6}")
    for cve, nombre in MUNICIPIOS_CAMPECHE.items():
        u23 = int((df23["cve_mun"] == cve).sum())
        n = int((nacimientos["cve_mun"] == cve).sum())
        m = int((muertes["cve_mun"] == cve).sum())
        s = int((sobrevivientes["cve_mun"] == cve).sum())
        u24 = int((df24["cve_mun"] == cve).sum())
        t_ent = 100 * n / u23 if u23 else 0
        t_sal = 100 * m / u23 if u23 else 0
        grupo = df24.loc[df24["cve_mun"] == cve, "grupo_tren"].iloc[0] if u24 else "?"
        print(f"  {cve:<4} {nombre:<14} {u23:>7,} {u24:>7,} {n:>6,} {m:>6,} {s:>6,} {t_ent:>7.1f} {t_sal:>7.1f} {grupo:>6}")

    print()
    print("=" * 70)
    print("  POR SECTOR TURISTICO (solo sobrevivientes/nacimientos/muertes por nivel)")
    print("=" * 70)
    print(f"  {'nivel':<10} {'N':>7} {'M':>7} {'S':>7}")
    for nivel in ["nucleo", "ampliado", "excluido", "resto"]:
        n = int((nacimientos["sector_turismo"] == nivel).sum())
        m = int((muertes["sector_turismo"] == nivel).sum())
        s = int((sobrevivientes["sector_turismo"] == nivel).sum())
        print(f"  {nivel:<10} {n:>7,} {m:>7,} {s:>7,}")

    print()
    print("=" * 70)
    print("  POR GRUPO TREN MAYA")
    print("=" * 70)
    print(f"  {'grupo':<6} {'N':>7} {'M':>7} {'S':>7}")
    for grupo in ["A", "B", "C"]:
        n = int((nacimientos["grupo_tren"] == grupo).sum())
        m = int((muertes["grupo_tren"] == grupo).sum())
        s = int((sobrevivientes["grupo_tren"] == grupo).sum())
        print(f"  {grupo:<6} {n:>7,} {m:>7,} {s:>7,}")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("  MATCHING DEMOGRAFIA DE NEGOCIOS - CAMPECHE")
    print("=" * 70)

    df23 = preparar(pd.read_csv(DATA_RAW / "campeche_2023.csv", dtype=str))
    df24 = preparar(pd.read_csv(DATA_RAW / "campeche_2024.csv", dtype=str))

    # 1. Match por CLEE
    clee_comunes = set(df23["clee"]) & set(df24["clee"])
    surv_clee_24 = df24[df24["clee"].isin(clee_comunes)].copy()
    surv_clee_24["tipo_match"] = "clee"
    surv_clee_24["fecha_alta_2023"] = surv_clee_24["clee"].map(
        df23.set_index("clee")["fecha_alta_norm"]
    )

    u23 = df23[~df23["clee"].isin(clee_comunes)].reset_index(drop=True)
    u24 = df24[~df24["clee"].isin(clee_comunes)].reset_index(drop=True)

    # 2. Match por regla de 3 variables (nombre, SCIAN, ubicacion)
    pares = match_fuzzy(u24, u23)
    i24_match = [p[0] for p in pares]
    i23_match = [p[1] for p in pares]
    mask24 = u24.index.isin(i24_match)
    mask23 = u23.index.isin(i23_match)

    surv_fuzzy_24 = u24[mask24].copy()
    surv_fuzzy_24["tipo_match"] = "fuzzy"
    fecha_2023 = {p[0]: u23.iloc[p[1]]["fecha_alta_norm"] for p in pares}
    surv_fuzzy_24["fecha_alta_2023"] = surv_fuzzy_24.index.map(fecha_2023)

    nacimientos = u24[~mask24].copy()
    muertes = u23[~mask23].copy()

    sobrevivientes = pd.concat([surv_clee_24, surv_fuzzy_24], ignore_index=True)

    # 3. Persistencia en SQLite
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        df23.to_sql("denue_2023", con, if_exists="replace", index=False)
        df24.to_sql("denue_2024", con, if_exists="replace", index=False)
        sobrevivientes.to_sql("sobrevivientes", con, if_exists="replace", index=False)
        nacimientos.to_sql("nacimientos", con, if_exists="replace", index=False)
        muertes.to_sql("muertes", con, if_exists="replace", index=False)

    print(f"\n  Base de datos guardada en: {DB_PATH.relative_to(BASE_DIR)}")
    print()

    reportar(df23, df24, sobrevivientes, nacimientos, muertes)

    print("\n" + "=" * 70)
    print("  MATCHING COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
