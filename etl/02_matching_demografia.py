"""
02_matching_demografia.py

Construye el panel de demografia de negocios de Campeche para multiples
ediciones (2022-2025) con matching consecutivo y analisis de cohortes.

- Lee data/raw/campeche_YYYY_MM.csv
- Normaliza fechas y claves textuales (nombre y ubicacion)
- Fusiona Calkini + Dzitbalche (cve_mun 013 -> 001)
- Clasifica el sector de servicios (3 niveles) y el grupo Tren Maya (A/B/C)
- Empareja ediciones consecutivas con el esquema hibrido
- Construye la tabla de cohortes (presencia por edicion)
- Guarda todo en data/denue.db (SQLite)
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

# Ediciones en orden cronologico
EDICIONES = ["2022_11", "2023_11", "2024_11", "2025_05"]

# Fusion municipal: Dzitbalche (013) se funde con Calkini (001)
FUSION_MUN = {"013": "001"}

MUNICIPIOS_CAMPECHE = {
    "001": "Calkiní-Dzitbalché",
    "002": "Campeche",
    "003": "Carmen",
    "004": "Champotón",
    "005": "Hecelchakán",
    "006": "Hopelchén",
    "007": "Palizada",
    "008": "Tenabo",
    "009": "Escárcega",
    "010": "Calakmul",
    "011": "Candelaria",
    "012": "Seybaplaya",
}

# Grupos de exposicion al Tren Maya (Dzitbalche quedo absorbido en Calkini)
GRUPO_TREN_MAYA = {
    "A": ["001", "002", "004", "005", "008", "009"],
    "B": ["003", "010", "011"],
    "C": ["006", "007", "012"],
}

# Clasificacion del sector de servicios por primeros 4 digitos del SCIAN
SCIAN_SERVICIOS = {
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


def clasificar_sector(scian4):
    if scian4 in SCIAN_SERVICIOS["nucleo"]:
        return "nucleo"
    if scian4 in SCIAN_SERVICIOS["ampliado"]:
        return "ampliado"
    if scian4 in SCIAN_SERVICIOS["excluido"]:
        return "excluido"
    return "resto"


def clasificar_grupo_tren(cve_mun):
    for grupo, municipios in GRUPO_TREN_MAYA.items():
        if cve_mun in municipios:
            return grupo
    return None


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Fusion municipal: Dzitbalche -> Calkini (antes de cualquier clave/ubicacion)
    df["cve_mun"] = df["cve_mun"].map(lambda m: FUSION_MUN.get(m, m))
    df["municipio"] = df["cve_mun"].map(MUNICIPIOS_CAMPECHE)

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
    df["sector_servicios"] = df["scian4"].map(clasificar_sector)
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
def match_fuzzy(u_sig: pd.DataFrame, u_base: pd.DataFrame):
    """Devuelve pares (posicion_sig, posicion_base) con la regla de 3 variables."""
    a = u_sig[["clee", "scian4", "nombre_norm", "nombre_valido", "ubicacion_norm"]].reset_index(drop=True)
    b = u_base[["clee", "scian4", "nombre_norm", "nombre_valido", "ubicacion_norm"]].reset_index(drop=True)

    a_nom = a[a["nombre_valido"]]
    b_nom = b[b["nombre_valido"]]
    a_ubic = a[a["ubicacion_norm"] != ""]
    b_ubic = b[b["ubicacion_norm"] != ""]

    cn = a_nom[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(columns={"index": "i_sig"})
    bn = b_nom[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(columns={"index": "i_base"})
    cn = cn.merge(bn, on=["scian4", "nombre_norm"], suffixes=("_sig", "_base"))
    cn["nombre_eq"] = 1
    cn["ubic_eq"] = (cn["ubicacion_norm_sig"] == cn["ubicacion_norm_base"]).astype(int)

    cu = a_ubic[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(columns={"index": "i_sig"})
    bu = b_ubic[["scian4", "nombre_norm", "ubicacion_norm"]].reset_index().rename(columns={"index": "i_base"})
    cu = cu.merge(bu, on=["scian4", "ubicacion_norm"], suffixes=("_sig", "_base"))
    cu["ubic_eq"] = 1
    cu["nombre_eq"] = (cu["nombre_norm_sig"] == cu["nombre_norm_base"]).astype(int)

    cands = pd.concat(
        [cn[["i_sig", "i_base", "nombre_eq", "ubic_eq"]],
         cu[["i_sig", "i_base", "nombre_eq", "ubic_eq"]]],
        ignore_index=True,
    )
    cands = cands.drop_duplicates(subset=["i_sig", "i_base"])
    cands["score"] = cands["nombre_eq"] + cands["ubic_eq"]
    cands = cands.sort_values(["score", "i_sig", "i_base"], ascending=[False, True, True])

    usados_sig = set()
    usados_base = set()
    pares = []
    for fila in cands.itertuples(index=False):
        if fila.i_sig in usados_sig or fila.i_base in usados_base:
            continue
        usados_sig.add(fila.i_sig)
        usados_base.add(fila.i_base)
        pares.append((fila.i_sig, fila.i_base))
    return pares


def emparejar(df_base: pd.DataFrame, df_sig: pd.DataFrame):
    """Empareja dos ediciones consecutivas con el esquema hibrido."""
    clee_comunes = set(df_base["clee"]) & set(df_sig["clee"])

    surv_clee = df_sig[df_sig["clee"].isin(clee_comunes)].copy()
    surv_clee["tipo_match"] = "clee"
    surv_clee["fecha_alta_base"] = surv_clee["clee"].map(
        df_base.set_index("clee")["fecha_alta_norm"]
    )

    u_base = df_base[~df_base["clee"].isin(clee_comunes)].reset_index(drop=True)
    u_sig = df_sig[~df_sig["clee"].isin(clee_comunes)].reset_index(drop=True)

    pares = match_fuzzy(u_sig, u_base)
    i_sig = [p[0] for p in pares]
    i_base = [p[1] for p in pares]
    mask_sig = u_sig.index.isin(i_sig)
    mask_base = u_base.index.isin(i_base)

    surv_fuzzy = u_sig[mask_sig].copy()
    surv_fuzzy["tipo_match"] = "fuzzy"
    fecha_base = {p[0]: u_base.iloc[p[1]]["fecha_alta_norm"] for p in pares}
    surv_fuzzy["fecha_alta_base"] = surv_fuzzy.index.map(fecha_base)

    nacimientos = u_sig[~mask_sig].copy()
    muertes = u_base[~mask_base].copy()

    sobrevivientes = pd.concat([surv_clee, surv_fuzzy], ignore_index=True)
    return sobrevivientes, nacimientos, muertes


# ============================================================
# Cohorte
# ============================================================
def construir_cohortes(datos: dict):
    """Construye la tabla de presencia de cada CLEE en cada edicion."""
    sets = {ed: set(df["clee"]) for ed, df in datos.items()}
    todas = set().union(*sets.values())
    filas = []
    for clee in todas:
        fila = {"clee": clee}
        for ed in EDICIONES:
            fila[f"en_{ed}"] = int(clee in sets[ed])
        fila["cohorte"] = next((ed for ed in EDICIONES if clee in sets[ed]), None)
        filas.append(fila)
    cohortes = pd.DataFrame(filas)

    # atributos desde la primera aparicion (diccionario, O(N))
    attr = {}
    for ed in EDICIONES:
        d = datos[ed][["clee", "sector_servicios", "grupo_tren", "cve_mun"]].drop_duplicates("clee")
        for fila in d.itertuples(index=False):
            if fila.clee not in attr:
                attr[fila.clee] = (fila.sector_servicios, fila.grupo_tren, fila.cve_mun)
    cohortes["sector_servicios"] = cohortes["clee"].map(lambda c: attr[c][0] if c in attr else None)
    cohortes["grupo_tren"] = cohortes["clee"].map(lambda c: attr[c][1] if c in attr else None)
    cohortes["cve_mun"] = cohortes["clee"].map(lambda c: attr[c][2] if c in attr else None)
    return cohortes


# ============================================================
# Reporte
# ============================================================
def reportar(datos, transiciones, cohortes):
    print("=" * 70)
    print("  UNIDADES POR EDICION")
    print("=" * 70)
    for ed in EDICIONES:
        print(f"    {ed}: {len(datos[ed]):,}")

    print()
    print("=" * 70)
    print("  UNIDADES POR MUNICIPIO (fusionados)")
    print("=" * 70)
    munis = sorted(MUNICIPIOS_CAMPECHE)
    encabezado = "  " + "".join(f"{ed:>11}" for ed in EDICIONES)
    print(f"  {'cve':<4}{'municipio':<20}{encabezado}")
    for cve in munis:
        nombre = MUNICIPIOS_CAMPECHE[cve]
        fila = f"  {cve:<4}{nombre:<20}"
        for ed in EDICIONES:
            n = int((datos[ed]["cve_mun"] == cve).sum())
            fila += f"{n:>11,}"
        print(fila)

    print()
    print("=" * 70)
    print("  TRANSICIONES (Sobrevivientes / Nacimientos / Muertes)")
    print("=" * 70)
    for i in range(len(EDICIONES) - 1):
        e1, e2 = EDICIONES[i], EDICIONES[i + 1]
        s, n, m = transiciones[(e1, e2)]
        total_base = len(datos[e1])
        print(f"    {e1} -> {e2}: S={len(s):,}  N={len(n):,}  M={len(m):,}  "
              f"(S+M={len(s)+len(m):,} vs base {total_base:,})")

    print()
    print("=" * 70)
    print("  COHORTES (presencia en las 4 ediciones)")
    print("=" * 70)
    total = len(cohortes)
    en_todas = int((cohortes[[f"en_{ed}" for ed in EDICIONES]].sum(axis=1) == len(EDICIONES)).sum())
    print(f"    Total CLEEs unicos: {total:,}")
    print(f"    Presentes en las 4 ediciones: {en_todas:,} ({100*en_todas/total:.1f}%)")
    for i, ed in enumerate(EDICIONES):
        cohorte = cohortes[cohortes["cohorte"] == ed]
        sobrevive_ultima = int(cohorte[f"en_{EDICIONES[-1]}"].sum()) if len(cohorte) else 0
        print(f"    Cohorte {ed}: {len(cohorte):,} -> sobreviven en {EDICIONES[-1]}: "
              f"{sobrevive_ultima:,} ({100*sobrevive_ultima/len(cohorte):.1f}%)" if len(cohorte) else f"    Cohorte {ed}: 0")


# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("  MATCHING MULTIEDICION - CAMPECHE (2022-2025)")
    print("=" * 70)

    # 1. Leer y preparar cada edicion
    datos = {}
    for ed in EDICIONES:
        ruta = DATA_RAW / f"campeche_{ed}.csv"
        datos[ed] = preparar(pd.read_csv(ruta, dtype=str))
        print(f"  {ed}: {len(datos[ed]):,} registros preparados")

    # 2. Emparejar ediciones consecutivas
    transiciones = {}
    for i in range(len(EDICIONES) - 1):
        e1, e2 = EDICIONES[i], EDICIONES[i + 1]
        s, n, m = emparejar(datos[e1], datos[e2])
        transiciones[(e1, e2)] = (s, n, m)
        print(f"  Transicion {e1}->{e2}: S={len(s):,} N={len(n):,} M={len(m):,}")

    # 3. Cohorte
    cohortes = construir_cohortes(datos)
    print(f"  Cohortes: {len(cohortes):,} CLEEs unicos")

    # 4. Persistencia en SQLite
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        for ed in EDICIONES:
            datos[ed].to_sql(f"denue_{ed}", con, if_exists="replace", index=False)
        for (e1, e2), (s, n, m) in transiciones.items():
            s.to_sql(f"t_{e1}__{e2}_sobrevivientes", con, if_exists="replace", index=False)
            n.to_sql(f"t_{e1}__{e2}_nacimientos", con, if_exists="replace", index=False)
            m.to_sql(f"t_{e1}__{e2}_muertes", con, if_exists="replace", index=False)
        cohortes.to_sql("cohortes", con, if_exists="replace", index=False)

        # Tablas de compatibilidad con el snapshot 2023-2024 (notebooks 01/02)
        datos["2023_11"].to_sql("denue_2023", con, if_exists="replace", index=False)
        datos["2024_11"].to_sql("denue_2024", con, if_exists="replace", index=False)
        s, n, m = transiciones[("2023_11", "2024_11")]
        s.to_sql("sobrevivientes", con, if_exists="replace", index=False)
        n.to_sql("nacimientos", con, if_exists="replace", index=False)
        m.to_sql("muertes", con, if_exists="replace", index=False)

    print(f"\n  Base de datos guardada en: {DB_PATH.relative_to(BASE_DIR)}")
    print()

    reportar(datos, transiciones, cohortes)

    print("\n" + "=" * 70)
    print("  MATCHING COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
