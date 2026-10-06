# Metodología detallada

Este documento describe el procedimiento operativo del análisis de demografía de negocios de Campeche. La versión resumida y las decisiones de fondo viven en la sección 0 del `README.md`.

## 1. Fuente de datos

Se comparan dos ediciones del DENUE (INEGI), descargadas por el portal de descarga masiva:

| Foto | Edición | Archivo procesado |
|------|---------|-------------------|
| Antes | nov-2023 | `data/raw/campeche_2023.csv` |
| Después | nov-2024 | `data/raw/campeche_2024.csv` |

Ambas se filtran a `cve_ent == "04"` (Campeche) mediante `etl/01_procesar_descarga.py`.

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
| A. Conectados y expuestos | Calkiní, Campeche, Champotón, Hecelchakán, Tenabo, Escárcega | Estaciones operativas desde dic-2023 |
| B. Conectados, exposición marginal | Carmen, Calakmul, Candelaria | Estaciones del Tramo 7, abiertas hasta dic-2024 |
| C. No conectados | Hopelchén, Palizada, Seybaplaya, Dzitbalché | Sin estación |

## 5. Persistencia

Los resultados se guardan en `data/denue.db` (SQLite) con las tablas:

- `denue_2023`, `denue_2024`: datos preparados (con claves normalizadas y clasificaciones).
- `sobrevivientes`: negocios presentes en ambas ediciones (con `tipo_match` = `clee` o `fuzzy`).
- `nacimientos`: negocios solo en 2024.
- `muertes`: negocios solo en 2023.

### Verificación de consistencia

```
Sobrevivientes + Muertes   == unidades 2023
Sobrevivientes + Nacimientos == unidades 2024
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
