# Demografía de negocios en Campeche: la paradoja del PIB y el tejido empresarial

<p align="center">
  <a href="https://aremyesmeraldaortegon-creator.github.io/demografia-negocios-campeche/">
    <img src="https://img.shields.io/badge/🚀_ABRIR_ANÁLISIS_INTERACTIVO-Click_aquí-0066CC?style=for-the-badge&logo=plotly&logoColor=white" alt="Abrir análisis interactivo">
  </a>
</p>

---

## 📌 Resumen ejecutivo

Este proyecto analiza la evolución del **tejido empresarial de los 13 municipios de Campeche** entre noviembre 2022 y mayo 2025, usando **4 ediciones del DENUE** (Directorio Estadístico Nacional de Unidades Económicas) del INEGI. La pregunta central es: ¿qué tan dinámico es el tejido empresarial de Campeche, y cómo se relaciona con la paradoja de un PIB per cápita alto que no se refleja en la economía local?

**Los hallazgos principales:**
- **+13.8% de crecimiento aparente** en unidades económicas (de 41,638 a 47,408)
- **85% de los negocios son microempresas** (0-5 personas) — el tejido no se diversifica
- **El Censo Económico 2024 introduce un artefacto metodológico** que infla nacimientos y muertes
- **El efecto del Tren Maya es ambiguo** — el Grupo A (municipios con estaciones operativas) no muestra un dinamismo diferencial claro

**Conclusión:** La economía campechana **reemplaza más de lo que desarrolla**. El petróleo genera renta, no tejido productivo robusto.

---

## 🎯 Pregunta de investigación

> **¿Qué tan dinámico es el tejido empresarial de los 13 municipios de Campeche, y cómo se relaciona ese dinamismo con la paradoja de un PIB per cápita alto que no se refleja en la economía local?**

---

## 📖 1. Contexto: la paradoja del PIB campechano

Campeche figura entre los estados con **mayor PIB per cápita de México**, gracias a la extracción de hidrocarburos en la Sonda de Campeche. Sin embargo, ese indicador convive con una **economía local de escaso dinamismo** y niveles altos de rezago social.

La explicación es estructural: la actividad petrolera funciona como una **economía de enclave**:
- Es **intensiva en capital**, no en empleo
- Se concentra en **plataformas marinas**, lejos de los municipios
- Tiene **poco derrame** sobre el comercio y los servicios locales

**Genera renta, no necesariamente empleo ni dinamismo de base.**

El PIB per cápita, al dividir una producción extraordinariamente grande entre una población relativamente pequeña, produce una **cifra engañosa**: lee como "riqueza" lo que en realidad es extracción concentrada.

Para saber qué tan sana está la economía local conviene mirar un indicador distinto: **la demografía de los negocios** — cuántas unidades económicas nacen, mueren y sobreviven.

---

## 🔬 2. Metodología

### 2.1 Fuente de datos: el DENUE

El **DENUE** es un registro del INEGI que cataloga todas las unidades económicas activas del país. Cada registro incluye:
- Un identificador único (**CLEE**)
- El nombre del establecimiento
- El código de actividad económica (**SCIAN**)
- La ubicación geográfica
- La fecha de alta

**Analogía:** El CLEE es como el **CURP** de cada negocio. El SCIAN es como el **tipo de negocio** (restaurante, hotel, taller, etc.).

### 2.2 Las 4 ediciones del DENUE

| # | Edición | Tipo | Rol |
|---|---------|------|-----|
| 1 | **nov-2022** | Regular | Foto "antes" |
| 2 | **nov-2023** | Regular | Última foto pre-Tren Maya |
| 3 | **nov-2024** | **Exhaustiva** (Censos Económicos) | Primera foto post-Tren Maya |
| 4 | **may-2025** | Regular | Foto de mediano plazo |

**¿Por qué la edición nov-2024 es especial?**
Proviene de los **Censos Económicos 2024**, una actualización **exhaustiva** (no incremental) que revisa todos los negocios uno por uno. Esto re-codifica masivamente las CLEEs y genera un **"artefacto censal"**: parece que muchos negocios murieron y nacieron, pero en realidad solo cambiaron de número de identificación.

### 2.3 Las tres decisiones metodológicas

#### Decisión 1: Comparar 4 ediciones (2022-2025)

**¿Por qué?** El Tren Maya se inauguró en diciembre de 2023. Comparar nov-2022 a may-2025 permite ver:
- **Antes** del Tren Maya (nov-2022, nov-2023)
- **Después** (nov-2024, may-2025)
- **Tendencias** en lugar de solo un snapshot

#### Decisión 2: Esquema híbrido para definir nacimiento/muerte

El DENUE **no es un panel longitudinal**: no sigue al mismo negocio con un identificador perfectamente estable entre ediciones. Depender de un solo criterio produciría **sesgos severos**:
- Si solo usas **CLEE**, cualquier cambio administrativo se lee como "muerte + nacimiento"
- Si solo usas **nombre + dirección + giro**, cualquier cambio de nombre se lee como muerte

Por eso se adopta el **esquema híbrido**, siguiendo la lógica del **Estudio de Demografía de los Negocios (EDN) del INEGI**:

1. **Coincidencia por CLEE** → sobreviviente
2. **Si no hay match:** comparar 3 variables (nombre, SCIAN, ubicación)
   - Si cambia **≤1 variable** → sobreviviente
   - Si cambian **≥2 variables** → muerte + nacimiento
3. **Refinamiento:** excluir del fuzzy los casos con nombre genérico (ej: "PESCADOR SIN NOMBRE")

#### Decisión 3: Estratificar el sector de servicios en 3 niveles

Los giros "turísticos" no responden igual. Se trabaja con:

| Nivel | SCIAN | Rol |
|-------|-------|-----|
| **Núcleo** | 7211, 7225, 5615 | Análisis principal (hoteles, restaurantes, agencias) |
| **Ampliado** | + 7224, 7132, 7121 | Análisis de robustez (bares, parques, museos) |
| **Excluido** | 4871 | Excluido por circularidad causal (transporte turístico) |

**¿Por qué excluir el 4871?** Porque podría incluir al **propio Tren Maya**. Medir su efecto incluyéndolo en la muestra invalida el análisis.

### 2.4 Fusión Calkiní-Dzitbalché

**Hallazgo metodológico:** Dzitbalché (013) **no existía como municipio en nov-2022**. Sus negocios estaban codificados bajo Calkiní (001). Verificación:
- Calkiní en 2022: 3,665 registros
- Calkiní + Dzitbalché en 2023: 2,676 + 994 = 3,670 ✓

**Decisión:** Fusionar Calkiní + Dzitbalché en una sola unidad ("Calkiní-Dzitbalché") para todas las comparaciones. Esto mantiene la consistencia de la serie 2022-2025.

---

## 📊 3. Los dos análisis

### Análisis 1: Snapshot 2023-2024 (dashboard principal)

Comparación puntual entre **nov-2023 y nov-2024** para medir nacimientos, muertes y supervivencia. Es el análisis base del proyecto.

**Notebook:** `notebooks/01_panorama_general.ipynb` y `notebooks/02_sector_servicios.ipynb`

### Análisis 2: Serie temporal 2022-2025 (dashboard de tendencias)

Análisis multianual con **4 ediciones**, 3 transiciones consecutivas y **tabla de cohortes**.

**Notebook:** `notebooks/03_tendencias.ipynb` y `notebooks/04_cohortes.ipynb`

---

## 🎯 4. Hallazgos principales

### Hallazgo 1: Estabilidad estructural del tejido microempresarial

**(a) Qué:** La proporción de microempresas (0-5 personas) se mantiene **estable en ~85%** durante los 4 años:
- nov-2022: 84.5%
- nov-2023: 84.4%
- nov-2024: 85.8%
- may-2025: 85.8%

**(b) De dónde:** Tablas `denue_2022_11`, `denue_2023_11`, `denue_2024_11`, `denue_2025_05` en `data/denue.db`. Campo `per_ocu` (personal ocupado).

**(c) Cómo:** Para cada edición, contar unidades económicas por rango de `per_ocu`, dividir "0-5 personas" entre el total × 100.

**(d) Por qué:** Refuerza la **paradoja del PIB campechano**. Ni siquiera con la apertura del Tren Maya (dic-2023) el tejido empresarial escala a empresas medianas o grandes. La economía local sigue atrapada en microescala.

**(e) Limitaciones:** La categoría "0-5 personas" agrupa micronegocios muy heterogéneos (desde puestos informales hasta pequeñas empresas formales). No distingue entre ambos.

---

### Hallazgo 2: Artefacto censal de 2024 (transición anómala)

**(a) Qué:** La **tasa de supervivencia cae a 69.4%** en 2023→2024, mientras que en 2022→2023 es **99.0%** y en 2024→2025 es **97.5%**.

| Transición | Ventana | Sobrevivientes | Nacimientos | Muertes | Tasa supervivencia |
|-----------|---------|---------------|-------------|---------|-------------------|
| 2022→2023 | 12 meses | 41,242 | 541 | 396 | **99.0%** |
| 2023→2024 | 12 meses | 28,984 | 17,939 | 12,799 | **69.4%** ⚠️ |
| 2024→2025 | **6 meses** | 45,752 | 1,656 | 1,171 | **97.5%** |

**(b) De dónde:** Tablas `t_2022_11__2023_11`, `t_2023_11__2024_11`, `t_2024_11__2025_05` en `data/denue.db`.

**(c) Cómo:** S / U_base × 100 para cada transición.

**(d) Por qué:** La edición nov-2024 viene de los **Censos Económicos 2024** (actualización exhaustiva), que **re-codifica masivamente las CLEEs**. Esto genera falsos "nacimientos + muertes" que el matching híbrido solo rescata parcialmente. **NO es un colapso real de negocios.**

**(e) Limitaciones:** Los datos no permiten distinguir con certeza entre (i) cierre real, (ii) re-codificación administrativa, (iii) mejor cobertura censal. Además, la transición 2024→2025 cubre solo **6 meses** (no 12), lo que distorsiona las tasas comparativas.

---

### Hallazgo 3: Cohortes con supervivencia desigual

**(a) Qué:** La **cohorte 2022** sobrevive **62.2%** a 2025 (2.5 años). La **cohorte 2023** solo **35.4%** a 2025 (1.5 años). La **cohorte 2024** sobrevive **90.2%** a 2025 (6 meses).

**(b) De dónde:** Tabla `cohortes` en `data/denue.db`.

**(c) Cómo:** Para cada CLEE nacido en año X, verificar si aparece en cada edición posterior. Calcular % de supervivientes / total cohorte.

**(d) Por qué:** La cohorte 2023 tiene supervivencia **anormalmente baja** porque nació **justo antes del Censo Económico 2024**. Al re-codificar CLEEs, muchos aparecen como "muertos" en 2024 aunque sigan operando. La cohorte 2024 (post-censo) no sufre este efecto.

**(e) Limitaciones:** Las cohortes tienen **ventanas temporales muy distintas** (2.5 años, 1.5 años, 6 meses). Comparar directamente no es justo.

---

### Hallazgo 4: Efecto ambiguo del Tren Maya en el sector servicios

**(a) Qué:** El **índice de dinamismo del sector servicios** en el Grupo A (Tren Maya operativo desde dic-2023):

| Transición | Global | Grupo A | Grupo B | Grupo C |
|-----------|--------|---------|---------|---------|
| 2022→2023 | +0.0256 | +0.0018 | +0.0233 | +0.0005 |
| 2023→2024 | +0.0127 | **−0.0045** | +0.0186 | −0.0014 |
| 2024→2025 | −0.0159 | **+0.0053** | −0.0192 | −0.0020 |

**(b) De dónde:** Cálculo a partir de tablas `nacimientos` y `muertes`, filtradas por `sector_servicios` y `grupo_tren`.

**(c) Cómo:** Índice = (N_núcleo / N_total) − (M_núcleo / M_total) para cada transición y grupo.

**(d) Por qué:** Sugiere que el efecto del Tren Maya puede ser **transitorio** o que los municipios se afectan en **momentos distintos**. El Grupo A muestra una aparente recuperación tardía en 2024→2025, pero el Grupo B invierte el patrón (positivo → negativo).

**(e) Limitaciones críticas:** La transición 2024→2025 es de **solo 6 meses** (no 12) y es **post-censal**, así que las "muertes" están infladas por el artefacto. **Interpretar con mucha cautela.**

---

## ⚠️ 5. Limitaciones generales

1. **Ventana temporal corta:** Solo 2.5 años (nov-2022 a may-2025). Los efectos del Tren Maya pueden requerir más tiempo.

2. **Artefacto censal 2024:** La edición exhaustiva re-codifica CLEEs y distorsiona las transiciones que la involucran.

3. **Dependencia de datos oficiales:** El análisis depende del DENUE. Si el INEGI tiene errores, se arrastran.

4. **Matching fuzzy con limitaciones:** Aunque refinamos para excluir nombres genéricos, el fuzzy matching sigue teniendo falsos positivos/negativos.

5. **"Sector servicios" es amplio:** No distingue entre un hotel boutique y una taquería.

6. **Ventanas temporales desiguales:** 12m, 12m y 6m — las tasas no son directamente comparables.

---

## 🔧 6. Cómo reproducir el proyecto

### Requisitos

- Python 3.10+
- Token del INEGI (gratuito, para consultas puntuales vía API)

### Instalación

```bash
git clone https://github.com/aremyesmeraldaortegon-creator/demografia-negocios-campeche.git
cd demografia-negocios-campeche
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env         # y llena tu INEGI_TOKEN
```

### Pipeline

1. **Descargar los datos crudos** (manual desde el portal del INEGI):
   ```
   python etl/00_instrucciones_descarga.py
   ```
   Seguir las instrucciones para descargar las 4 ediciones del DENUE para Campeche.

2. **Procesar los CSV:**
   ```
   python etl/01_procesar_descarga.py
   ```

3. **Matching y construcción de la base SQLite:**
   ```
   python etl/02_matching_demografia.py
   ```

4. **Análisis exploratorio** (abrir los notebooks):
   ```
   jupyter lab notebooks/
   ```

5. **Regenerar el dashboard:**
   ```
   python dashboard/generar_dashboard.py
   python dashboard/generar_tendencias.py
   ```

---

## 📂 7. Estructura del repositorio

```
demografia-negocios-campeche/
├── data/                          # Datos crudos y base SQLite (ignorados por git)
├── dashboard/
│   ├── generar_dashboard.py       # Genera docs/index.html (snapshot)
│   ├── generar_tendencias.py      # Genera docs/tendencias.html (multianual)
│   └── campeche_municipios.geojson
├── docs/
│   ├── index.html                 # Dashboard principal (snapshot 2023-2024)
│   ├── tendencias.html            # Dashboard multianual (2022-2025)
│   └── metodologia.md             # Metodología detallada
├── etl/
│   ├── 00_instrucciones_descarga.py
│   ├── 01_procesar_descarga.py
│   └── 02_matching_demografia.py
├── notebooks/
│   ├── 01_panorama_general.ipynb
│   ├── 02_sector_servicios.ipynb
│   ├── 03_tendencias.ipynb
│   └── 04_cohortes.ipynb
├── README.md
├── .env.example
├── .gitignore
└── requirements.txt
```

---

## 📚 8. Fuentes y referencias

- **DENUE (INEGI):** https://www.inegi.org.mx/programas/denue/
- **Estudio de Demografía de los Negocios (EDN) del INEGI:** Metodología oficial del matching
- **Censos Económicos 2024:** https://www.inegi.org.mx/programas/ce/2024/
- **SCIAN:** https://www.inegi.org.mx/scian/

---

## ✍️ Autor

**Aremy Esmeralda Ortega**  
Proyecto de análisis de datos — 2026