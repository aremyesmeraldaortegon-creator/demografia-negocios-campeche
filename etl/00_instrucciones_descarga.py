"""
00_instrucciones_descarga.py

Imprime las instrucciones paso a paso para descargar manualmente
las ediciones del DENUE desde el portal del INEGI.

Ediciones usadas en el proyecto:
  - 11/2022  (regular)
  - 11/2023  (regular)
  - 11/2024  (exhaustiva, Censos Economicos)
  - 05/2025  (regular)
"""

URL_PORTAL = "https://www.inegi.org.mx/app/descarga/default.html"
URL_API_DENUE = "https://www.inegi.org.mx/app/api/denue/v1/consulta/"

SEPARADOR = "=" * 70
SUBRAYADO = "-" * 70

EDICIONES = [
    ("11/2022", "2022", "regular"),
    ("11/2023", "2023", "regular"),
    ("11/2024", "2024", "exhaustiva (Censos Economicos)"),
    ("05/2025", "2025", "regular"),
]


def imprimir_titulo(texto):
    print(SEPARADOR)
    print(f"  {texto}")
    print(SEPARADOR)
    print()


def imprimir_seccion(numero, titulo, lineas):
    print(f"\n[{numero}] {titulo}")
    print(SUBRAYADO)
    for linea in lineas:
        print(f"  {linea}")
    print()


def main():
    imprimir_titulo("INSTRUCCIONES DE DESCARGA - DENUE (Campeche)")

    print("Este script NO descarga datos automaticamente.")
    print("Sigue los pasos manualmente desde tu navegador.\n")

    for i, (edicion, anio, tipo) in enumerate(EDICIONES, start=1):
        imprimir_seccion(
            str(i),
            f"Descargar la edicion {edicion} ({tipo})",
            [
                f"Portal: {URL_PORTAL}",
                "",
                "Pasos:",
                "  a) Abre el portal en tu navegador.",
                "  b) En 'Fuente', selecciona: DENUE.",
                f"  c) En 'Edicion', selecciona: {edicion}.",
                "  d) En 'Area geografica', selecciona: Campeche.",
                "  e) En 'Formato', selecciona: CSV.",
                "  f) Descarga el archivo ZIP.",
                "",
                f"Guarda y descomprime el ZIP en:  data/raw/descarga_{anio}/",
                "",
                "Estructura esperada:",
                f"  data/raw/descarga_{anio}/conjunto_de_datos/denue_inegi_04_.csv",
            ],
        )

    imprimir_seccion(
        str(len(EDICIONES) + 1),
        "Ejecutar el procesamiento",
        [
            "Una vez descargados y descomprimidos los archivos,",
            "corre el siguiente script:",
            "",
            "  python etl/01_procesar_descarga.py",
        ],
    )

    imprimir_seccion(
        str(len(EDICIONES) + 2),
        "API del DENUE (alternativa)",
        [
            f"URL base: {URL_API_DENUE}",
            "",
            "Requiere token gratuito (ya configurado en .env).",
            "Solo devuelve la edicion mas reciente; no sirve para",
            "reconstruir el panel historico.",
        ],
    )

    print(SEPARADOR)
    print("  ADVERTENCIA SOBRE PESOS")
    print(SEPARADOR)
    print("  Los archivos CSV del DENUE pueden ser grandes.")
    print("  Verifica que tengas al menos 1 GB libre en disco.")
    print(SEPARADOR)


if __name__ == "__main__":
    main()
