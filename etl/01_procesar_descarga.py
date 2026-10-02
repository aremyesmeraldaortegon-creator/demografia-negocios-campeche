"""
01_procesar_descarga.py

Procesa los CSV crudos del DENUE para Campeche.

- Busca recursivamente el CSV dentro de data/raw/descarga_YYYY/conjunto_de_datos/
- Lo lee en chunks con pandas
- Filtra por cve_ent == "04" (Campeche)
- Guarda el resultado en data/raw/campeche_YYYY.csv
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

ANIOS = [2023, 2024]
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


def buscar_csv(anio: int) -> Path:
    """Busca recursivamente el CSV dentro de data/raw/descarga_YYYY/."""
    carpeta = DATA_RAW / f"descarga_{anio}"
    if not carpeta.exists():
        raise FileNotFoundError(f"No existe la carpeta: {carpeta}")

    candidatos = list(carpeta.rglob("*.csv"))
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
            primer_chunk = next(pd.read_csv(csv_path, encoding=enc, **kwargs))
            return pd.read_csv(csv_path, encoding=enc, **kwargs)
        except (UnicodeDecodeError, StopIteration):
            print(f"  {enc} fallo, probando siguiente encoding...")
            continue
    raise ValueError(f"No se pudo leer {csv_path}")


def procesar_anio(anio: int) -> pd.DataFrame:
    """Lee, filtra y guarda el CSV de un anio. Devuelve el DataFrame limpio."""
    print(f"\n[{anio}] Procesando...")
    csv_path = buscar_csv(anio)

    partes = []
    total_leidas = 0

    for chunk in leer_con_encoding(csv_path, chunksize=CHUNKSIZE, dtype=str, low_memory=False):
        total_leidas += len(chunk)

        chunk["cve_ent_norm"] = chunk["cve_ent"].astype(str).str.strip().str.zfill(2)
        filtrado = chunk[chunk["cve_ent_norm"] == CVE_ENT_CAMPECHE].copy()
        filtrado = filtrado.drop(columns=["cve_ent_norm"])
        partes.append(filtrado)

    if not partes:
        raise ValueError(f"No se encontraron registros para Campeche en {anio}")

    df = pd.concat(partes, ignore_index=True)

    salida = DATA_RAW / f"campeche_{anio}.csv"
    df.to_csv(salida, index=False, encoding="utf-8")
    print(f"  Total leidas: {total_leidas:,}")
    print(f"  Total Campeche: {len(df):,}")
    print(f"  Guardado en: {salida.relative_to(BASE_DIR)}")

    return df


def reportar_municipios(df: pd.DataFrame, anio: int) -> None:
    """Imprime el desglose por municipio y advierte si alguno queda en 0."""
    print(f"\n  Desglose por municipio ({anio}):")
    conteo = df["cve_mun"].value_counts().sort_index()

    for cve, nombre in MUNICIPIOS_CAMPECHE.items():
        n = int(conteo.get(cve, 0))
        alerta = "  <-- ATENCION: 0 registros" if n == 0 else ""
        print(f"    {cve} {nombre:<15} {n:>6,}{alerta}")


def main() -> None:
    print("=" * 70)
    print("  PROCESAMIENTO DENUE - CAMPECHE")
    print("=" * 70)

    for anio in ANIOS:
        try:
            df = procesar_anio(anio)
            reportar_municipios(df, anio)
        except Exception as e:
            print(f"\n  ERROR en {anio}: {e}")
            sys.exit(1)

    print("\n" + "=" * 70)
    print("  PROCESAMIENTO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
