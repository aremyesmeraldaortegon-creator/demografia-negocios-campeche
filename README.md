# Demografía de negocios en Campeche

Análisis de nacimientos, muertes y sobrevivencia de negocios en los 13 municipios de Campeche, comparando el DENUE (nov-2023 vs. nov-2024), con foco en el sector turístico y el Tren Maya.

---

## 0. Nota metodológica: por qué se hace así

Antes de presentar cualquier cifra, conviene explicar las tres decisiones metodológicas que estructuran todo el análisis. No son arbitrarias: cada una responde a una limitación concreta de la fuente de datos.

### 0.1 ¿Por qué comparar nov-2023 vs. nov-2024?

El Tren Maya se inauguró en diciembre de 2023. Nov-2023 es el último corte previo a la apertura, mientras que nov-2024 es el primer corte anual completo posterior y corresponde a los Censos Económicos 2024 (una actualización exhaustiva, no incremental). Comparar un año exacto entre ambas fotos aísla el efecto del Tren Maya de variaciones estacionales: cualquier diferencia entre las dos ediciones no puede atribuirse a la estacionalidad del turismo, sino al cambio estructural en el tejido empresarial.

### 0.2 ¿Por qué un esquema híbrido para definir nacimiento/muerte?

El DENUE no es un panel longitudinal: no sigue al mismo negocio con un identificador perfectamente estable entre ediciones. Depender de un solo criterio produciría sesgos severos:

- Si solo se usa la CLEE, cualquier cambio administrativo del INEGI se leería como "muerte + nacimiento" aunque el negocio siga operando.
- Si solo se usa la llave compuesta (nombre + dirección + giro), cualquier cambio de nombre o mudanza mínima se leería como muerte.

Por eso se adopta el esquema híbrido, siguiendo la lógica del Estudio de Demografía de los Negocios (EDN) del INEGI:

1. Coincidencia por CLEE → sobreviviente.
2. Si no hay match: regla de 3 variables clave (nombre, SCIAN, ubicación). Si cambia ≤1 → sobreviviente; ≥2 → muerte + nacimiento.
3. Validación auxiliar con FECHA_ALTA.

Detalle operativo en `docs/metodologia.md`.

### 0.3 ¿Por qué estratificar el sector turístico en 3 niveles?

Los giros que suelen etiquetarse como "turismo" no responden igual al fenómeno. Meterlos todos en una sola bolsa introduce dos problemas:

1. **Circularidad causal.** El código SCIAN 4871 (transporte turístico terrestre) podría incluir al propio Tren Maya. Medir el efecto del Tren Maya incluyendo al Tren Maya en la muestra invalida el análisis.

2. **Heterogeneidad no controlada.** Museos (7121) y parques recreativos (7132) tienen dinámicas muy distintas a las de un hotel: muchos son públicos y su supervivencia no depende del mercado turístico, sino del presupuesto gubernamental.

Por eso se trabaja con tres niveles:

| Nivel | SCIAN | Rol en el análisis |
|---|---|---|
| Núcleo | 7211, 7225, 5615 | Análisis principal |
| Ampliado | + 7224, 7132, 7121 | Análisis de robustez |
| Excluido | 4871 | Excluido por circularidad causal |

---

## 1. Contexto y objetivo

*[Borrador — por completar]*

La paradoja del PIB campechano: Campeche tiene uno de los PIB per cápita más altos del país por la actividad petrolera, pero eso no se refleja necesariamente en el dinamismo de su economía local. Mi objetivo es explorar esta paradoja a través de la demografía de los negocios, usando como "experimento natural" la apertura del Tren Maya en diciembre de 2023.

- **Pregunta central:** ¿cómo cambió el tejido empresarial de los municipios de Campeche tras la apertura del Tren Maya?
- **Objetivos específicos:**
  - Medir nacimientos, muertes y sobrevivencia de unidades económicas entre dos ediciones del DENUE.
  - Comparar el sector turístico frente al resto de la economía.

---

## 2. Fuente de datos

### 2.1 El DENUE y la lógica de las dos "fotos"

El **Directorio Estadístico Nacional de Unidades Económicas (DENUE)** es un registro del INEGI que cataloga todas las unidades económicas activas del país: negocios, locales, oficinas, plantas y establecimientos de cualquier tamaño, desde un puesto de comida hasta una sucursal bancaria. Cada registro incluye, entre otros campos, un identificador de establecimiento, una clave única de identificación (**CLEE**), el nombre del establecimiento, el código de actividad económica (**SCIAN**), la ubicación geográfica exacta (municipio, localidad, coordenadas) y la **fecha de alta**.

Para estudiar la *demografía* de los negocios —es decir, cuántos nacen, cuántos mueren y cuántos sobreviven en un período— no basta con una sola fotografía de la economía: se necesitan dos observaciones del mismo directorio en momentos distintos del tiempo. Cada edición del DENUE es una "foto" estática del tejido empresarial en una fecha de corte; la comparación entre dos fotos es lo que permite detectar las altas (nacimientos) y las bajas (muertes).

Este proyecto compara dos ediciones:

| Foto | Período | Edición / vía de acceso |
|------|---------|-------------------------|
| Antes (histórica) | nov-2023 | Edición 11/2023, descarga masiva |
| Después (actual) | nov-2024 | Edición 11/2024, descarga masiva |

La elección de estas dos ediciones no es arbitraria y se justifica en la sección 0.1: la edición de noviembre de 2023 es el último corte *previo* a la inauguración del Tren Maya (diciembre de 2023), mientras que la de noviembre de 2024 es el primer corte anual completo *posterior* y coincide con la actualización exhaustiva de los Censos Económicos 2024. Comparar exactamente un año entre ambas fotos permite aislar el efecto estructural del Tren Maya de las variaciones estacionales del turismo.

### 2.2 ¿Por qué descarga masiva y no la API?

El INEGI ofrece dos vías de acceso programático al DENUE: una **API de consulta** y el **portal de descarga masiva**. Elegir entre ambas no es un detalle técnico menor, sino una decisión que condiciona la viabilidad misma del análisis, por dos razones.

**Primera razón: la API no permite consultar ediciones históricas.** El endpoint de consulta del API (`https://www.inegi.org.mx/app/api/denue/v1/consulta/`, que requiere un token gratuito) devuelve únicamente la **edición más reciente** del DENUE, es decir, la ligada a los Censos Económicos vigentes. No expone un parámetro para indicar "dame la edición de noviembre de 2023". En consecuencia, por API solo es posible obtener la foto "después" (nov-2024) y jamás la foto "antes" (nov-2023), lo que haría imposible el estudio de nacimientos, muertes y sobrevivencia.

**Segunda razón: la comparabilidad entre fotos.** Aun cuando se pudiera obtener una edición histórica por otra vía, mezclar métodos de extracción (una foto por API y otra por descarga masiva) introduciría diferencias de formato, de estructura de columnas y de filtros aplicados que contaminarían el matching entre ediciones. El portal de **descarga masiva** (`https://www.inegi.org.mx/app/descarga/default.html`) sí permite seleccionar explícitamente la **Edición** (por ejemplo, 11/2023 o 11/2024), además de la entidad federativa y el formato de salida. Al obtener *ambas* ediciones por esta vía, se garantiza que las dos fotos compartan el mismo esquema y los mismos criterios, condición necesaria para que la comparación sea válida.

Por lo tanto, la regla de este proyecto es: **descarga masiva para reconstruir el panel histórico (ambas ediciones) y API solo para consultas puntuales de la edición vigente** (por ejemplo, validar el giro de un establecimiento concreto o explorar una localidad específica).

### 2.3 Procedimiento de descarga masiva

Los archivos crudos se obtienen manualmente desde el portal de descarga masiva del INEGI. El proceso, repetido para cada una de las dos ediciones, es el siguiente:

1. Abrir el portal de descarga masiva en `https://www.inegi.org.mx/app/descarga/default.html`.
2. En el campo **Fuente**, seleccionar **DENUE**.
3. En el campo **Edición**, elegir la versión deseada: **11/2023** para la foto histórica o **11/2024** para la foto actual.
4. En el campo **Área geográfica**, seleccionar **Campeche**.
5. En el campo **Formato**, elegir **CSV**.
6. Descargar el archivo `.zip` resultante.
7. Descomprimir el `.zip` dentro de la carpeta correspondiente (`data/raw/descarga_2023/` o `data/raw/descarga_2024/`).

El `.zip` contiene, además del archivo de datos, un diccionario de datos y un archivo de metadatos. La estructura resultante, ya presente en este repositorio, es:

```
data/raw/
├── descarga_2023/
│   ├── denue_04_1123_csv.zip
│   ├── conjunto_de_datos/denue_inegi_04_.csv
│   ├── diccionario_de_datos/denue_diccionario_de_datos.csv
│   └── metadatos/metadatos_denue.txt
└── descarga_2024/
    ├── denue_04_1124_csv.zip
    ├── conjunto_de_datos/denue_inegi_04_.csv
    ├── diccionario_de_datos/denue_diccionario_de_datos.csv
    └── metadatos/metadatos_denue.txt
```

El sufijo `04_` en el nombre del archivo corresponde a la clave de entidad federativa de Campeche (`cve_ent = 04`). Como verificación adicional, el script `etl/01_procesar_descarga.py` localiza recursivamente el CSV dentro de `data/raw/descarga_YYYY/` y filtra los registros por `cve_ent == "04"` antes de generar el archivo procesado `data/raw/campeche_YYYY.csv`.

---

## 3. Extracción y almacenamiento (ETL)

*[Borrador — por completar]*

El proceso de extracción, transformación y carga (ETL) se organiza en la carpeta `etl/`. El detalle metodológico vive en `docs/metodologia.md`.

- **Extracción:** consultas al API del DENUE para la foto actual; descarga masiva para la foto histórica.
- **Almacenamiento:** base de datos SQLite (`data/`).
- **Transformación:** limpieza, normalización de giros (SCIAN) y clasificación del sector turístico.

---

## 4. Demografía de negocios: panorama general

*[Borrador — por completar]*

Notebook: `notebooks/01_panorama_general.ipynb`

Análisis agregado para todos los municipios y todos los giros: nacimientos, muertes y sobrevivencia por municipio, tasas de entrada y salida, y distribución por sector y tamaño de establecimiento.

---

## 5. Demografía de negocios: sector turístico

*[Borrador — por completar]*

Notebook: `notebooks/02_sector_turistico.ipynb`

Comparación del sector turístico contra el resto de los sectores, usando los niveles núcleo y ampliado, y desglose por subsector (hoteles, restaurantes, agencias de viajes). Se analiza el dinamismo diferencial en los municipios conectados por el Tren Maya.

---

## 6. Hallazgos y conclusión

*[Borrador — por completar]*

Resumen de los resultados principales y su relación con la paradoja del PIB campechano. Pendiente de redactar una vez terminado el análisis.

---

## Estructura del repositorio

```
demografia-negocios-campeche/
├── data/              # Datos crudos y base SQLite (ignorados por git)
├── docs/
│   └── metodologia.md # Metodología detallada
├── etl/               # Scripts de extracción, transformación y carga
├── notebooks/
│   ├── 01_panorama_general.ipynb
│   └── 02_sector_turistico.ipynb
├── README.md
├── .env.example       # Variables de entorno de ejemplo
├── .gitignore
└── requirements.txt   # Dependencias del proyecto
```

> **Nota:** el archivo `.env` (sin `.example`) contiene el token del INEGI y está ignorado por git vía `.gitignore`.

## Instalación

```bash
git clone <url-del-repo>   # reemplazar por la URL real una vez publicado
cd demografia-negocios-campeche
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # y llena tu INEGI_TOKEN
```

*Pasos de instalación pendientes de validar.*
