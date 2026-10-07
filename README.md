# Demografía de negocios en Campeche: la paradoja del PIB y el tejido empresarial

## 🌐 Dashboard interactivo

👉 **[Ver dashboard en vivo](https://aremyesmeraldaortegon-creator.github.io/demografia-negocios-campeche/)**

Análisis de nacimientos, muertes y sobrevivencia de negocios en los 13 municipios de Campeche a partir del DENUE (nov-2023 vs. nov-2024), para explorar por qué un PIB per cápita alto no se refleja en el dinamismo de la economía local. La apertura del Tren Maya (dic-2023) se usa como experimento natural, no como foco principal.

---

## 0. Nota metodológica: por qué se hace así

Antes de presentar cualquier cifra, conviene explicar las tres decisiones metodológicas que estructuran todo el análisis. No son arbitrarias: cada una responde a una limitación concreta de la fuente de datos.

### 0.1 ¿Por qué comparar nov-2023 vs. nov-2024?

El Tren Maya se inauguró en diciembre de 2023. Nov-2023 es el último corte previo a la apertura, mientras que nov-2024 es el primer corte anual completo posterior y corresponde a los Censos Económicos 2024 (una actualización exhaustiva, no incremental). Comparar un año exacto entre ambas fotos aísla el efecto del Tren Maya de variaciones estacionales: cualquier diferencia entre las dos ediciones no puede atribuirse a la estacionalidad de la demanda, sino al cambio estructural en el tejido empresarial.

### 0.2 ¿Por qué un esquema híbrido para definir nacimiento/muerte?

El DENUE no es un panel longitudinal: no sigue al mismo negocio con un identificador perfectamente estable entre ediciones. Depender de un solo criterio produciría sesgos severos:

- Si solo se usa la CLEE, cualquier cambio administrativo del INEGI se leería como "muerte + nacimiento" aunque el negocio siga operando.
- Si solo se usa la llave compuesta (nombre + dirección + giro), cualquier cambio de nombre o mudanza mínima se leería como muerte.

Por eso se adopta el esquema híbrido, siguiendo la lógica del Estudio de Demografía de los Negocios (EDN) del INEGI:

1. Coincidencia por CLEE → sobreviviente.
2. Si no hay match: regla de 3 variables clave (nombre, SCIAN, ubicación). Si cambia ≤1 → sobreviviente; ≥2 → muerte + nacimiento.
3. Validación auxiliar con FECHA_ALTA.

Detalle operativo en `docs/metodologia.md`.

### 0.3 ¿Por qué estratificar el sector de servicios en 3 niveles?

Los giros que suelen agruparse como "servicios" no responden igual a los mismos estímulos. Meterlos todos en una sola bolsa introduce dos problemas:

1. **Circularidad causal.** El código SCIAN 4871 (transporte turístico terrestre) podría incluir al propio Tren Maya. Medir el efecto del Tren Maya incluyendo al Tren Maya en la muestra invalida el análisis.

2. **Heterogeneidad no controlada.** Museos (7121) y parques recreativos (7132) tienen dinámicas muy distintas a las de un hotel: muchos son públicos y su supervivencia no depende del mercado, sino del presupuesto gubernamental.

Por eso se trabaja con tres niveles:

| Nivel | SCIAN | Rol en el análisis |
|---|---|---|
| Núcleo | 7211, 7225, 5615 | Análisis principal |
| Ampliado | + 7224, 7132, 7121 | Análisis de robustez |
| Excluido | 4871 | Excluido por circularidad causal |

---

## 1. Contexto y objetivo

### 1.1 La paradoja del PIB campechano

Campeche encarna una de las paradojas económicas más marcadas de México: figura entre los estados con mayor **PIB per cápita** del país, gracias a la extracción de hidrocarburos en la Sonda de Campeche, y sin embargo ese indicador convive con una economía local de escaso dinamismo y con niveles altos de rezago social. La explicación es estructural: la actividad petrolera funciona como una **economía de enclave**. Es intensiva en capital, se concentra en plataformas marinas lejos de los municipios y tiene poco derrame sobre el comercio y los servicios que sostienen la vida económica cotidiana. Genera renta, no necesariamente empleo ni dinamismo de base.

El PIB per cápita, al dividir una producción extraordinariamente grande entre una población relativamente pequeña, produce una cifra engañosa: lee como "riqueza" lo que en realidad es extracción concentrada. Para saber qué tan sana está la economía *local* conviene mirar un indicador distinto: la **demografía de los negocios**, es decir, cuántas unidades económicas nacen, mueren y sobreviven.

### 1.2 ¿Por qué la demografía de los negocios?

El dinamismo de una economía local no se observa bien en la producción agregada, sino en el flujo de sus unidades económicas. Si los negocios nacen y sobreviven, el tejido productivo de base es saludable; si mueren más de los que nacen, la actividad económica se contrae aunque el PIB estatal siga alto por la renta petrolera. Medir nacimientos, muertes y sobrevivencia permite, por tanto, mirar *debajo* del PIB y observar el pulso real de los municipios.

El instrumento para hacerlo es el **Directorio Estadístico Nacional de Unidades Económicas (DENUE)** del INEGI, que al compararse entre dos ediciones (nov-2023 y nov-2024) revela las altas y las bajas del tejido empresarial. Este es el corazón del proyecto.

### 1.3 El Tren Maya como experimento natural (una hipótesis, no el eje)

Dentro de esta pregunta más amplia, la apertura del **Tren Maya** en diciembre de 2023 cumple un papel metodológico específico: funciona como un **experimento natural**. Se trata de un choque externo a la economía local, con fecha de inicio conocida y geografía discreta (un municipio está *conectado* si alberga una estación y *no conectado* si no), lo que permite explorar si el dinamismo empresarial difiere entre ambos grupos. Es una herramienta de identificación muy valiosa, pero **no es el foco principal**: es una de las posibles explicaciones del dinamismo diferencial, no la pregunta que estructura todo el análisis.

Dado que las estaciones se inauguraron por tramos en fechas distintas, la clasificación operativa distingue tres grupos según su **exposición real** durante la ventana de análisis (nov-2023 a nov-2024):

| Grupo | Municipios | Justificación |
|---|---|---|
| A. Conectados y expuestos | Calkiní, Campeche, Champotón, Hecelchakán, Tenabo, Escárcega | Estaciones operativas desde dic-2023 |
| B. Conectados, exposición marginal | Carmen, Calakmul, Candelaria | Estaciones del Tramo 7, abiertas hasta dic-2024 (después del corte nov-2024) |
| C. No conectados | Hopelchén, Palizada, Seybaplaya, Dzitbalché | Sin estación |

> Las fechas exactas de apertura de cada estación deben confirmarse contra la fuente oficial de FONATUR / Olmeca-Maya-Mexica antes de fijar esta clasificación como definitiva.

### 1.4 Pregunta central y objetivos

- **Pregunta central:** ¿qué tan dinámico es el tejido empresarial de los 13 municipios de Campeche, y cómo se relaciona ese dinamismo con la paradoja de un PIB per cápita alto que no se refleja en la economía local?
- **Objetivos específicos:**
  1. Medir nacimientos, muertes y sobrevivencia de unidades económicas entre nov-2023 y nov-2024 en todos los municipios y sectores.
  2. Comparar el sector de servicios frente al resto de la economía.
  3. Explorar, usando el Tren Maya como experimento natural, si los municipios conectados (grupo A) muestran un dinamismo diferencial frente a los no conectados.
  4. Relacionar los hallazgos con la paradoja del PIB: ¿el petróleo genera riqueza sin derrame en el tejido empresarial de base?

### 1.5 Hipótesis

- **Hipótesis principal:** el alto PIB per cápita de Campeche coexiste con un tejido empresarial de base frágil, visible en tasas de nacimiento modestas o en una sobrevivencia concentrada en los giros más básicos.
- **Hipótesis secundaria:** si el Tren Maya tuvo efecto, este debería concentrarse en el núcleo de servicios de los municipios del grupo A (conectados y expuestos), no en el conjunto de la economía ni en los municipios no conectados.

Ambas hipótesis pueden resultar verdaderas o falsas: el diseño no presupone un resultado, solo establece qué observar para poder distinguir el efecto del Tren Maya de la dinámica general de la paradoja.

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

La elección de estas dos ediciones no es arbitraria y se justifica en la sección 0.1: la edición de noviembre de 2023 es el último corte *previo* a la inauguración del Tren Maya (diciembre de 2023), mientras que la de noviembre de 2024 es el primer corte anual completo *posterior* y coincide con la actualización exhaustiva de los Censos Económicos 2024. Comparar exactamente un año entre ambas fotos permite aislar el efecto estructural del Tren Maya de las variaciones estacionales de la demanda.

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

El proceso de extracción, transformación y carga se organiza en la carpeta `etl/`. El detalle metodológico vive en `docs/metodologia.md`.

- **Extracción:** descarga masiva del DENUE para **ambas** ediciones (nov-2023 y nov-2024) desde el portal del INEGI. El API solo se usa para consultas puntuales de la edición vigente.
- **Procesamiento:** `etl/01_procesar_descarga.py` filtra los CSV crudos a Campeche (`cve_ent == "04"`) y genera `data/raw/campeche_YYYY.csv`.
- **Matching y clasificación:** `etl/02_matching_demografia.py` normaliza, clasifica (sector de servicios y grupo Tren Maya) y aplica el matching híbrido.
- **Almacenamiento:** base de datos SQLite (`data/denue.db`).

---

## 4. Demografía de negocios: panorama general

Notebook: `notebooks/01_panorama_general.ipynb`

Análisis agregado para todos los municipios y todos los giros. Calcula por municipio la tasa de supervivencia (`S / U23`), natalidad (`N / U24`), mortalidad (`M / U23`) y crecimiento neto (`(U24 - U23) / U23`), además de la distribución por sector de servicios y por tamaño (personal ocupado).

> **Nota:** `U23` = unidades económicas (negocios) en 2023; `U24` = unidades económicas en 2024.

---

## 5. Demografía de negocios: sector de servicios

Notebook: `notebooks/02_sector_servicios.ipynb`

Comparación del sector de servicios contra el resto de la economía, con desglose por nivel (núcleo, ampliado, excluido) y subsector (alojamiento, alimentos y bebidas, agencias de viajes, bares, parques, museos). Analiza el dinamismo diferencial por grupo de exposición al Tren Maya (A/B/C) y calcula el índice de dinamismo del sector de servicios. Exporta las tablas clave a `data/processed/`.

---

## 6. Hallazgos y conclusión

### 6.1 ¿Es el crecimiento un indicador de desarrollo?

La respuesta matizada es: **no necesariamente**. El crecimiento de +12.3% en el número de unidades económicas (de 41,783 a 46,923) esconde una realidad de **alta rotación empresarial** más que de desarrollo sostenido:

- Solo el **69.4%** de los negocios de 2023 sobrevivió a 2024 (28,984 de 41,783); el **30.6%** murió (12,799 negocios).
- El crecimiento neto (+5,140 unidades) se explica por **17,939 nacimientos**, no por el fortalecimiento de los negocios existentes.
- El **85.7%** de las unidades son microempresas (0-5 personas): el tejido productivo no se diversifica ni escala.
- El **índice de dinamismo del grupo A** (municipios con Tren Maya operativo) es **negativo (−0.0050)**, lo que sugiere que el Tren Maya no ha dinamizado los negocios existentes.

### 6.2 Conclusión clave: hay más "reemplazo" que "desarrollo"

El crecimiento neto positivo coexiste con una alta mortalidad y una base microempresarial: nacen muchos negocios y mueren casi tantos. La economía local **se reemplaza más de lo que se desarrolla**. Esta rotación es coherente con la paradoja del PIB campechano: la renta petrolera no se traduce en un tejido empresarial robusto y acumulativo, sino en un flujo constante de aperturas y cierres.

### 6.3 Otros hallazgos

- **Crecimiento generalizado pero desigual:** natalidad superior a mortalidad en 12 de los 13 municipios.
- **Dinamismo concentrado en municipios pequeños:** Calakmul (+29.1%), Dzitbalché (+28.3%) y Hopelchén (+25.7%) encabezan el crecimiento neto; Palizada es el único municipio en contracción.
- **El sector de servicios es minoritario y su dinamismo se concentra en el grupo B:** el índice de dinamismo del sector de servicios es +0.0127 a nivel global, positivo sobre todo en Carmen, Calakmul y Candelaria (grupo B).

> **Nota de interpretación:** parte del crecimiento observado puede reflejar la mejor cobertura de los Censos Económicos 2024, no solo nueva actividad económica. Los datos no permiten distinguir con certeza entre reemplazo puro, renovación positiva o artefacto censal.

---

## Dashboard interactivo

El proyecto incluye un dashboard web autocontenido, generado con Plotly y publicado en GitHub Pages.

- **URL pública:** `https://aremyesmeraldaortegon-creator.github.io/demografia-negocios-campeche/`
- **Archivo:** `docs/index.html` (autocontenido: incluye Plotly.js y el GeoJSON del mapa, sin dependencias externas).
- **Secciones:** KPIs, mapa coroplético de crecimiento neto por municipio, tasas por municipio, distribución por tamaño, sector de servicios, índice de dinamismo por grupo Tren Maya, top 5 y tabla completa con descarga de CSVs.

### Regenerar el dashboard

```bash
python dashboard/generar_dashboard.py
```

> Requiere `plotly` (ya en `requirements.txt`). Lee `data/denue.db` y el GeoJSON `dashboard/campeche_municipios.geojson`, y escribe `docs/index.html`.

### Publicar en GitHub Pages

1. Repositorio → **Settings** → **Pages**.
2. En *Source*, elegir **Deploy from a branch**.
3. Rama `main`, carpeta `/docs` → **Save**.

Tras unos minutos, el dashboard queda disponible en la URL pública (el repositorio debe ser público para GitHub Pages gratuito).

---

## Estructura del repositorio

```
demografia-negocios-campeche/
├── data/              # Datos crudos y base SQLite (ignorados por git)
├── dashboard/
│   ├── generar_dashboard.py        # Genera docs/index.html
│   └── campeche_municipios.geojson # GeoJSON de los 13 municipios
├── docs/
│   ├── index.html      # Dashboard (autocontenido)
│   └── metodologia.md  # Metodología detallada
├── etl/               # Scripts de extracción, transformación y carga
├── notebooks/
│   ├── 01_panorama_general.ipynb
│   └── 02_sector_servicios.ipynb
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

Los pasos de instalación han sido validados en Windows con Python 3.14.
