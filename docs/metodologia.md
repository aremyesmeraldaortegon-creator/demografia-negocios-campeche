# Metodología detallada

Este documento describe el procedimiento operativo del análisis de demografía de negocios de Campeche. La versión resumida y las decisiones de fondo viven en la sección 0 del `README.md`.

## 1. Fuente de datos

Se comparan **cuatro ediciones** del DENUE (INEGI), descargadas por el portal de descarga masiva:

| Edición | Tipo | Archivo procesado |
|---------|------|-------------------|
| 11/2022 | regular | `data/raw/campeche_2022_11.csv` |
| 11/2023 | regular | `data/raw/campeche_2023_11.csv` |
| 11/2024 | exhaustiva (Censos Económicos) | `data/raw/campeche_2024_11.csv` |
| 05/2025 | regular | `data/raw/campeche_2025_05.csv` |

Todas se filtran a `cve_ent == "04"` (Campeche) mediante `etl/01_procesar_descarga.py`.

## 2. Preparación de datos (`etl/02_matching_demografia.py`)

Antes del matching se construyen las claves normalizadas:

- **`scian4`:** primeros 4 dígitos de `codigo_act` (SCIAN).
- **`nombre_norm`:** `nom_estab` en minúsculas, sin acentos ni puntuación.
- **`nombre_act_norm`:** `nombre_act` normalizado (para detectar nombres no informativos).
- **`ubicacion_norm`:** concatenación normalizada de municipio, localidad, vialidad, número exterior, asentamiento y código postal.
- **`fecha_alta_norm`:** `fecha_alta` homogeneizada a `YYYY-MM` (la fuente trae formatos mixtos como `2013 07` y `2013-07`).

### 2.1 Nombre informativo (`nombre_valido`)

Un nombre se considera **no informativo** y queda excluido del matching por nombre (aunque no del matching por ubicación) si cumple alguna de estas condiciones:

1. Está vacío.
2. Es igual al nombre de la actividad (`nom_estab == nombre_act`).
3. Contiene un marcador genérico: `"sin nombre"`, `"sin denominación"`, `"sin razón social"`, `"sin giro"`, `"sin número"`, `"sin nombre comercial"`, `"anónimo"`, `"no especificado"`, `"no proporcionado"` o `"no disponible"`.

> **Motivo:** el DENUE rellena el nombre de muchos establecimientos con el nombre de la actividad o con fórmulas genéricas ("TIENDA DE ABARROTES SIN NOMBRE"). Emparejar por estos nombres produce falsos sobrevivientes cuando dos negocios genéricos coinciden en SCIAN y ubicación.

## 3. Matching híbrido

El esquema sigue la lógica del Estudio de Demografía de los Negocios (EDN) del INEGI:

1. **Coincidencia por `clee`** → sobreviviente.
2. **Si no hay match por `clee`**, regla de 3 variables (`nombre`, `scian4`, `ubicacion_norm`). Si difieren ≤1 → sobreviviente; si difieren ≥2 → muerte (lado 2023) + nacimiento (lado 2024). Operativamente, dentro del mismo `scian4`, basta con que coincida el nombre **informativo** *o* la ubicación.
3. **Validación auxiliar con `fecha_alta`**: a cada sobreviviente se le conserva `fecha_alta_2023` y `fecha_alta_norm` (2024) para detectar re-registros sospechosos.

La asignación fuzzy es **uno a uno** (greedy por puntaje: coincidencia de nombre y ubicación vale más que una sola).

## 4. Clasificaciones auxiliares

### 4.1 Sector de servicios (3 niveles)

| Nivel | SCIAN (4 dígitos) | Rol |
|---|---|---|
| Núcleo | 7211, 7225, 5615 | Análisis principal |
| Ampliado | 7224, 7132, 7121 | Análisis de robustez |
| Excluido | 4871 | Excluido por circularidad causal |

El resto de los códigos se etiquetan como `resto`.

### 4.2 Exposición al Tren Maya

| Grupo | Municipios | Justificación |
|---|---|---|
| A. Conectados y expuestos | Calkiní-Dzitbalché, Campeche, Champotón, Hecelchakán, Tenabo, Escárcega | Estaciones operativas desde dic-2023 |
| B. Conectados, exposición marginal | Carmen, Calakmul, Candelaria | Estaciones del Tramo 7, abiertas hasta dic-2024 |
| C. No conectados | Hopelchén, Palizada, Seybaplaya | Sin estación |

> **Fusión Calkiní-Dzitbalché:** la edición 11/2022 no codifica a Dzitbalché (013) como municipio separado; sus negocios aparecen bajo Calkiní (001). Para mantener una serie municipal consistente entre ediciones, Dzitbalché se fusiona con Calkiní en una sola unidad "Calkiní-Dzitbalché" (`cve_mun 013 → 001`) en todas las ediciones.

## 5. Persistencia

Los resultados se guardan en `data/denue.db` (SQLite) con las tablas:

- `denue_2022_11`, `denue_2023_11`, `denue_2024_11`, `denue_2025_05`: datos preparados (con claves normalizadas y clasificaciones, y con la fusión Calkiní-Dzitbalché).
- Transiciones consecutivas: `t_2022_11__2023_11_{sobrevivientes,nacimientos,muertes}`, `t_2023_11__2024_11_*`, `t_2024_11__2025_05_*`.
- `cohortes`: un registro por `clee` con su presencia en cada edición (`en_YYYY_MM`) y su `cohorte` (primera edición donde aparece).

> Se conservan las tablas `denue_2023`, `denue_2024`, `sobrevivientes`, `nacimientos` y `muertes` como snapshot de compatibilidad 2023→2024 para los notebooks 01/02.

### Verificación de consistencia

```
Por cada transicion (e1 -> e2):
Sobrevivientes + Muertes   == unidades de e1
Sobrevivientes + Nacimientos == unidades de e2
```

## 6. Resultados (nov-2023 vs nov-2024)

| Indicador | Valor |
|---|---|
| Unidades 2023 | 41,783 |
| Unidades 2024 | 46,923 |
| Sobrevivientes | 28,984 (CLEE 25,958 + fuzzy 3,026) |
| Nacimientos | 17,939 |
| Muertes | 12,799 |

> **Registro de cambio:** el conteo original (30,130 sobrevivientes) se corrigió aplicando la exclusión de nombres genéricos descrita en la sección 2.1, lo que eliminó 1,146 matches fuzzy espurios.

## 7. Análisis

El análisis se realiza en notebooks que leen de `data/denue.db` (con fallback automático: si la base no existe, se regenera ejecutando `etl/02_matching_demografia.py`):

- **`notebooks/01_panorama_general.ipynb`**: panorama agregado por municipio y sector, distribución por tamaño y verificación de consistencia.
- **`notebooks/02_sector_servicios.ipynb`**: sector de servicios (núcleo vs resto, niveles y subsectores), grupos de exposición al Tren Maya e índice de dinamismo; exporta tablas a `data/processed/`.
- **`notebooks/03_tendencias.ipynb`**: serie temporal 2022–2025 y el artefacto censal de 2024.
- **`notebooks/04_cohortes.ipynb`**: supervivencia de largo plazo por cohorte, sector y grupo Tren Maya.

### 7.1 Métricas

**Glosario de variables:**

- `S` = Sobrevivientes (negocios presentes en ambas ediciones).
- `M` = Muertes (negocios solo en 2023).
- `N` = Nacimientos (negocios solo en 2024).
- `U23` = Unidades económicas en 2023.
- `U24` = Unidades económicas en 2024.

| Métrica | Fórmula |
|---|---|
| Tasa de supervivencia | `S / U23` |
| Tasa de natalidad | `N / U24` |
| Tasa de mortalidad | `M / U23` |
| Crecimiento neto | `(U24 - U23) / U23` |
| Índice de dinamismo del sector de servicios | `(N_núcleo / N_total) - (M_núcleo / M_total)` |

### 7.2 Hallazgos preliminares

- Crecimiento neto positivo y generalizado (+12.3%), con natalidad superior a mortalidad en 12 de los 13 municipios.
- Mayor crecimiento neto en municipios pequeños: Calakmul (+28.4%), Hopelchén (+26.0%) y Carmen (+21.2%).
- Palizada es el único municipio en contracción.
- El 85.7% de las unidades son microempresas (0-5 personas), coherente con la paradoja del PIB campechano.
- El índice de dinamismo del sector de servicios es +0.0127 a nivel global y se concentra en el grupo B (+0.0186).
- **Alta rotación empresarial:** solo el 69.4% de los negocios de 2023 sobrevivió a 2024 (28,984 de 41,783) y el 30.6% murió (12,799). El crecimiento neto se explica por nacimientos, no por fortalecimiento del tejido existente.

> **Nota de interpretación:** la edición nov-2024 está ligada a los Censos Económicos 2024 (actualización exhaustiva), por lo que parte del crecimiento observado puede deberse a una mejor cobertura censal y no solo a nueva actividad económica.

### 7.3 Limitaciones e interpretación crítica

**Crecimiento bruto vs. desarrollo sostenido.** El crecimiento neto (+12.3%) no equivale a desarrollo empresarial. Un +12.3% es compatible con un tejido que se *reemplaza*: se abren muchos negocios y se cierran casi tantos. La evidencia de esto es que solo el 69.4% de las unidades de 2023 sobrevivió a 2024 y que el crecimiento neto se debe a 17,939 nacimientos, no a la expansión de los negocios existentes. Un indicador de desarrollo debería mostrar sobrevivencia alta y escalamiento (más unidades grandes); aquí se observa lo contrario: sobrevivencia del 69.4% y un tejido dominado por microempresas (85.7% con 0-5 personas).

**Posible artefacto de cobertura censal.** La edición nov-2024 está ligada a los Censos Económicos 2024, una actualización *exhaustiva* (no incremental) que tiende a capturar más unidades que una edición intermedia. Parte del crecimiento observado —y parte de los "nacimientos"— puede reflejar mejor cobertura más que creación real de negocios. Esto es especialmente relevante en Carmen (grupo B), que muestra la mayor tasa de entrada.

**Reemplazo, renovación o artefacto: no son distinguibles con estos datos.** Con solo dos cortes (nov-2023 y nov-2024) no es posible separar con certeza el *reemplazo puro* (cierre y apertura de giros similares), la *renovación positiva* (negocios que cierran para reabrir mejor capitalizados) del *artefacto censal*. La interpretación de "más reemplazo que desarrollo" es, por tanto, una hipótesis robusta pero no una medición causal definitiva.

## 8. Diseño multianual (2022–2025)

La expansión a cuatro ediciones introduce tres consideraciones nuevas.

### 8.1 Matching consecutivo y cohortes

- Se emparejan **ediciones consecutivas** (2022→2023, 2023→2024, 2024→2025) con el mismo esquema híbrido (CLEE + regla de 3 variables + validación con `fecha_alta`).
- Las **cohortes** se definen por `clee`: la *cohorte* de un negocio es la primera edición en la que aparece. Esto permite medir la supervivencia de largo plazo (p. ej. la cohorte 2022 y cuánto de ella sigue en 2025).

### 8.2 Ruptura metodológica de 2024 (artefacto censal)

La edición 11/2024 proviene de los Censos Económicos (actualización *exhaustiva*), mientras 11/2022, 11/2023 y 05/2025 son regulares. Esto contamina las dos transiciones adyacentes:

| Transición | Ventana | Naturaleza | Efecto |
|---|---|---|---|
| 2022→2023 | 12m | regular→regular | **limpia** |
| 2023→2024 | 12m | regular→exhaustiva | nacimientos inflados (mejor cobertura) |
| 2024→2025 | 6m | exhaustiva→regular | muertes infladas + ventana corta |

La **tasa de supervivencia** lo confirma: 99.1% (2022→2023), **69.4%** (2023→2024) y 97.5% (2024→2025). La caída a 69.4% es la re-codificación masiva de CLEEs del censo, no un colapso real.

### 8.3 Ventanas temporales desiguales

Las transiciones no miden lo mismo: 12 meses (2022→2023), 12 meses (2023→2024) y **6 meses** (2024→2025, por usar la edición de mayo 2025). Al graficar tasas, se anota la ventana real de cada transición (no se asumen "años").

### 8.4 Resultados clave de la expansión

- 66,991 CLEEs únicos; **35.9% presentes en las 4 ediciones**.
- Cohorte 2022 (41,638) → **62.2% sobrevive a 2025**.
- El artefacto censal 2024 explica la mayor parte de la rotación anormal observada en la transición 2023→2024.
