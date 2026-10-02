"""
00_instrucciones_descarga.py

Imprime las instrucciones paso a paso para descargar manualmente
las ediciones del DENUE (nov-2023 y nov-2024) desde el portal del INEGI.
"""

URL_PORTAL = "https://www.inegi.org.mx/app/descarga/default.html"
URL_API_DENUE = "https://www.inegi.org.mx/app/api/denue/v1/consulta/"

SEPARADOR = "=" * 70
SUBRAYADO = "-" * 70


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

    imprimir_seccion(
        "1",
        "Descargar la edicion historica (nov-2023)",
        [
            f"Portal: {URL_PORTAL}",
            "",
            "Pasos:",
            "  a) Abre el portal en tu navegador.",
            "  b) En 'Fuente', selecciona: DENUE.",
            "  c) En 'Edicion', selecciona: 11/2023.",
            "  d) En 'Area geografica', selecciona: Campeche.",
            "  e) En 'Formato', selecciona: CSV.",
            "  f) Descarga el archivo ZIP (aprox. 600 KB).",
            "",
            "Guarda el ZIP en:  data/raw/descarga_2023/",
        ],
    )

    imprimir_seccion(
        "2",
        "Descargar la edicion actual (nov-2024)",
        [
            f"Portal: {URL_PORTAL}",
            "",
            "Pasos:",
            "  a) Repite el proceso anterior.",
            "  b) En 'Edicion', selecciona: 11/2024.",
            "  c) Descarga el ZIP.",
            "",
            "Guarda el ZIP en:  data/raw/descarga_2024/",
        ],
    )

    imprimir_seccion(
        "3",
        "Descomprimir los ZIP",
        [
            "Descomprime cada ZIP dentro de su carpeta correspondiente.",
            "",
            "Estructura esperada:",
            "  data/raw/descarga_2023/*.csv",
            "  data/raw/descarga_2024/*.csv",
        ],
    )

    imprimir_seccion(
        "4",
        "Ejecutar el procesamiento",
        [
            "Una vez descargados y descomprimidos los archivos,",
            "corre el siguiente script:",
            "",
            "  python etl/01_procesar_descarga.py",
        ],
    )

    imprimir_seccion(
        "5",
        "API del DENUE (alternativa)",
        [
            f"URL base: {URL_API_DENUE}",
            "",
            "Requiere token gratuito (ya configurado en .env).",
            "Se usa para consultas puntuales de cualquier edicion.",
        ],
    )

    print(SEPARADOR)
    print("  ADVERTENCIA SOBRE PESOS")
    print(SEPARADOR)
    print("  Los archivos CSV del DENUE pueden ser grandes.")
    print("  Verifica que tengas al menos 500 MB libres en disco.")
    print(SEPARADOR)


if __name__ == "__main__":
    main()