"""
01_procesar_descarga.py

Procesa los CSV crudos del DENUE para Campeche, para todas las ediciones.

- Busca recursivamente el CSV dentro de data/raw/descarga_YYYY/
- Lo lee en chunks con pandas (utf-8 o latin-1)
- Filtra por cve_ent == "04" (Campeche)
- Guarda el resultado en data/raw/campeche_YYYY_MM.csv
- Reporta totales y desglose por municipio
"""

import sys
from pathlib import Path

import pandas as pd


# ============================================================
# Configuracion
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"

# Ediciones del DENUE: etiqueta YYYY_MM -> carpeta de descarga (por anio)
EDICIONES = {
    "2022_11": "2022",
    "2023_11": "2023",
    "2024_11": "2024",
    "2025_05": "2025",
}

CVE_ENT_CAMPECHE = "04"
CHUNKSIZE = 50_000

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


def buscar_csv(etiqueta: str) -> Path:
    """Busca recursivamente el CSV dentro de data/raw/descarga_YYYY/."""
    carpeta = DATA_RAW / f"descarga_{EDICIONES[etiqueta]}"
    if not carpeta.exists():
        raise FileNotFoundError(f"No existe la carpeta: {carpeta}")

    candidatos = [p for p in carpeta.rglob("*.csv") if "diccionario" not in str(p).lower()]
    if not candidatos:
        raise FileNotFoundError(f"No hay CSV en: {carpeta}")

    csv_path = max(candidatos, key=lambda p: p.stat().st_size)
    print(f"  CSV encontrado: {csv_path.relative_to(BASE_DIR)}")
    return csv_path


def leer_con_encoding(csv_path: Path, **kwargs) -> pd.DataFrame:
    """Intenta leer con utf-8 y si falla usa latin-1."""
    for enc in ("utf-8", "latin-1"):
        try:
            # Forzamos la lectura del primer chunk para detectar errores temprano
            next(pd.read_csv(csv_path, encoding=enc, **kwargs))
            return pd.read_csv(csv_path, encoding=enc, **kwargs)
        except (UnicodeDecodeError, StopIteration):
            print(f"  {enc} fallo, probando siguiente encoding...")
            continue
    raise ValueError(f"No se pudo leer {csv_path}")


def procesar_edicion(etiqueta: str) -> pd.DataFrame:
    """Lee, filtra y guarda el CSV de una edicion. Devuelve el DataFrame limpio."""
    print(f"\n[{etiqueta}] Procesando...")
    csv_path = buscar_csv(etiqueta)

    partes = []
    total_leidas = 0

    for chunk in leer_con_encoding(csv_path, chunksize=CHUNKSIZE, dtype=str, low_memory=False):
        total_leidas += len(chunk)

        chunk["cve_ent_norm"] = chunk["cve_ent"].astype(str).str.strip().str.zfill(2)
        filtrado = chunk[chunk["cve_ent_norm"] == CVE_ENT_CAMPECHE].copy()
        filtrado = filtrado.drop(columns=["cve_ent_norm"])
        partes.append(filtrado)

    if not partes:
        raise ValueError(f"No se encontraron registros para Campeche en {etiqueta}")

    df = pd.concat(partes, ignore_index=True)

    salida = DATA_RAW / f"campeche_{etiqueta}.csv"
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"  Total leidas: {total_leidas:,}")
    print(f"  Total Campeche: {len(df):,}")
    print(f"  Guardado en: {salida.relative_to(BASE_DIR)}")

    return df


def reportar_municipios(df: pd.DataFrame, etiqueta: str) -> None:
    """Imprime el desglose por municipio y advierte si alguno queda en 0."""
    print(f"\n  Desglose por municipio ({etiqueta}):")
    conteo = df["cve_mun"].value_counts().sort_index()

    for cve, nombre in MUNICIPIOS_CAMPECHE.items():
        n = int(conteo.get(cve, 0))
        alerta = "  <-- ATENCION: 0 registros" if n == 0 else ""
        print(f"    {cve} {nombre:<15} {n:>6,}{alerta}")


def main() -> None:
    print("=" * 70)
    print("  PROCESAMIENTO DENUE - CAMPECHE (multiedicion)")
    print("=" * 70)

    for etiqueta in EDICIONES:
        try:
            df = procesar_edicion(etiqueta)
            reportar_municipios(df, etiqueta)
        except Exception as e:
            print(f"\n  ERROR en {etiqueta}: {e}")
            sys.exit(1)

    print("\n" + "=" * 70)
    print("  PROCESAMIENTO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
