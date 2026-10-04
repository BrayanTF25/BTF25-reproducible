# Desarrollo y evidencias del paso 3 — BTF25

Fecha de elaboración: 3 de octubre de 2026. Destinatario: Claude, para auditoría y posterior integración de la tesis de Brayan Tafur. Este documento corresponde al paso 3 del algoritmo de seis pasos de cierre de observaciones; no al antiguo algoritmo de siete pasos.

## 1. Alcance y estado real

Se utilizaron los cinco XLSX originales disponibles, los parámetros exportados por la ejecución MATLAB y las salidas de ruido previamente calculadas en Python. Se efectuaron nuevos cálculos de tiempos y una síntesis de las pruebas de ruido existentes. No se ejecutó nuevamente el experimento de ruido en MATLAB y no se modificó el DOCX final.

| Subpaso / observación | Evidencia preparada | Estado |
|---|---|---|
| 3.1 / #21 | Percentiles por archivo, definición y cuantificación del jitter, interrupciones y hashes | Cálculo realizado y verificado |
| 3.2 / #37 | Modelo completo de MATLAB en precisión original y presentación a cuatro decimales | Contenido preparado para el anexo |
| 3.3 / #41 | Propuesta explícita de criterio práctico retrospectivo y aplicación a resultados existentes | Requiere aceptación del criterio; no cumple preinscripción retroactiva |
| 3.4 / #4 | Identificación de tres campos de índices y procedimiento de actualización | Pendiente en Word tras integrar la versión final |

**El paso 3 no puede declararse cerrado en su totalidad:** falta actualizar y verificar los índices en el documento integrado y decidir con el asesor si acepta el tratamiento exploratorio de #41. Tampoco se recalculó el estado de las 48 observaciones: el conteo 38/10/0 procede de la auditoría de Claude y no constituye una nueva auditoría realizada aquí.

## 2. Observación #21: tiempos, percentiles y jitter

### 2.1 Procedimiento ejecutado

Se leyó la columna A de cada XLSX original, convirtiendo tanto celdas numéricas como números almacenados como texto. Se excluyó únicamente el encabezado. Los vectores de tiempo coincidieron exactamente con los de la lectura previa validada del dataset; se verificó que todos los tiempos fueran finitos y que todas las diferencias fueran positivas.

Para cada archivo, Δt_i = t_(i+1) − t_i, en segundos. Los percentiles se calcularon con interpolación lineal (NumPy `percentile(method="linear")`, tipo 7): posición h=(n−1)p, interpolando entre los dos valores ordenados vecinos. Las tablas convierten segundos a milisegundos.

Se mantuvo la regla ya implementada: interrupción si Δt_i > 1,5 × mediana(Δt). Un intervalo igual al umbral pertenece al grupo continuo. En estos cinco archivos el umbral es aproximadamente 1,465500 ms. No se interpolaron las interrupciones para este cálculo.

Se distinguen tres indicadores para evitar llamar jitter a la duración de las brechas:

- Dispersión total: desviación estándar poblacional de todos los Δt, incluyendo interrupciones.
- Jitter continuo: desviación estándar poblacional de Δt de los intervalos que no cruzan una interrupción (`ddof=0`).
- Desviación RMS continua respecto de la mediana registrada: raíz de la media de (Δt − mediana global)^2 entre intervalos continuos. Su porcentaje es 100 × RMS / mediana global.

La mediana registrada es 0,977 ms. El intervalo nominal de 1/1024 Hz es 0,9765625 ms; ambos valores no son idénticos. La tabla describe marcas de tiempo registradas con resolución observada de aproximadamente un microsegundo: no constituye una medición independiente del jitter físico del reloj de adquisición ni justifica reemplazar automáticamente la frecuencia nominal por la inversa de la mediana.

### 2.2 Percentiles de todos los intervalos, incluyendo interrupciones (ms)

| Condición | P1 | P5 | P50 | P95 | P99 |
| --- | --- | --- | --- | --- | --- |
| Healthy | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Damaged_LR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Damaged_UR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Unbalanced_LR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Unbalanced_UR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |

### 2.3 Percentiles de los intervalos continuos (ms)

| Condición | P1 | P5 | P50 | P95 | P99 |
| --- | --- | --- | --- | --- | --- |
| Healthy | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Damaged_LR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Damaged_UR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Unbalanced_LR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |
| Unbalanced_UR | 0.976000 | 0.976000 | 0.977000 | 0.977000 | 0.977000 |

Las dos tablas coinciden a seis decimales porque las interrupciones son aproximadamente el 0,20 % de los intervalos. P99 no alcanza a describir esa cola; su igualdad no demuestra ausencia de interrupciones.

### 2.4 Jitter y dispersión (ms, salvo el porcentaje)

| Condición | DE total ms | DE continua ms | RMS respecto mediana ms | RMS relativo % |
| --- | --- | --- | --- | --- |
| Healthy | 1.942136 | 0.000498 | 0.000677 | 0.069289 |
| Damaged_LR | 1.734617 | 0.000498 | 0.000677 | 0.069305 |
| Damaged_UR | 1.695472 | 0.000498 | 0.000677 | 0.069298 |
| Unbalanced_LR | 1.693470 | 0.000498 | 0.000677 | 0.069307 |
| Unbalanced_UR | 1.754747 | 0.000498 | 0.000677 | 0.069299 |

### 2.5 Conteos y brechas

| Condición | Muestras | Intervalos | Brechas | Intervalos continuos | Brecha mínima ms | Brecha máxima ms |
| --- | --- | --- | --- | --- | --- | --- |
| Healthy | 398945 | 398944 | 797 | 398147 | 33.311000 | 168.952000 |
| Damaged_LR | 399999 | 399998 | 799 | 399199 | 33.250000 | 77.934000 |
| Damaged_UR | 400000 | 399999 | 799 | 399200 | 33.060000 | 53.177000 |
| Unbalanced_LR | 400000 | 399999 | 799 | 399200 | 33.513000 | 70.107000 |
| Unbalanced_UR | 400000 | 399999 | 799 | 399200 | 33.222000 | 118.215000 |

**Corrección necesaria:** las interrupciones observadas no están todas entre 40 y 60 ms. El máximo en Healthy es 168,952 ms. El texto debe presentar el rango observado por archivo y conservar la segmentación ya implementada; no reducir la auditoría únicamente a brechas de 40–60 ms.

### 2.6 Texto propuesto para el apartado 5.1

> La auditoría de las marcas temporales mostró percentiles P1 y P5 de 0,976 ms y P50, P95 y P99 de 0,977 ms en los cinco registros. Estos valores se mantuvieron al excluir los intervalos identificados como interrupciones mediante el umbral de 1,5 veces la mediana de Δt. La desviación estándar de los intervalos continuos fue aproximadamente 0,000498 ms; este indicador describe la variación de las marcas de tiempo registradas. La dispersión que incluye interrupciones fue mayor, entre 1,693470 y 1,942136 ms. Se detectaron 797 interrupciones en Healthy y 799 en cada uno de los cuatro registros con falla. Sus rangos se detallan por archivo; se observó un máximo de 168,952 ms. Debido a su baja proporción, los percentiles hasta P99 no representan por sí solos la cola de interrupciones. El procesamiento mantuvo la separación de tramos continuos, sin interpolar las brechas.

### 2.7 Identidad de los archivos analizados

- `Healthy.xlsx` → Healthy
  - SHA-256: `9aee03af22b440bd701a2bf692cc2cf0178c33e1a76b1f41a1c0e06d5c857429`
- `Damaged Bottom Right Blade.xlsx` → Damaged_LR
  - SHA-256: `b638095ebe3cab60eecf0b51ba74f05a09a1d56005aabca0399d14b918e1f933`
- `Damaged Top Right Blade.xlsx` → Damaged_UR
  - SHA-256: `737c7084fe656b6d31f3d592737a90ffbb668ae95526ac0b4a0665cdc4d8c70e`
- `Unbalanced Bottom Right Blade.xlsx` → Unbalanced_LR
  - SHA-256: `48d9fb396202020a598022b885b513847df1f3a5f43fc2c3459557e2774b6d17`
- `Unbalanced Top Right Blade.xlsx` → Unbalanced_UR
  - SHA-256: `5997930f36c68e06d785a3abc18fd1ec7ed7b05225f0852ca327131c5ca03a90`

## 3. Observación #37: parámetros congelados completos

### 3.1 Procedencia e interpretación

El modelo se recuperó de `work_review_step2/frozen_parameters.json`, exportado por la ejecución MATLAB auditada en el paso 2. No se volvió a ajustar el modelo con los datos de prueba. El modelo declara 2 256 fragmentos de desarrollo, incluidos 449 Healthy. Los 3 386 fragmentos de la tabla de características corresponden a 2 256 de desarrollo más 1 130 de prueba; no son 3 386 de desarrollo.

Orden de las seis características: log10 de la energía de velocidad en X,Y,Z para la banda de referencia 10–100 Hz, seguido de log10 de la energía de velocidad en X,Y,Z para la banda de comparación 140–200 Hz. La energía se expresa numéricamente en (mm/s)^2 y se aplica el piso numérico 10⁻¹² antes del logaritmo. Orden de los prototipos: Damaged_LR, Damaged_UR, Unbalanced_LR, Unbalanced_UR; Healthy se resuelve en la etapa binaria.

Medianas y escalas corresponden a las normalizaciones robustas; las seis características están activas. `threshold_a` es el umbral del máximo valor absoluto normalizado, no una velocidad. `p95_v` y `p99_v` son umbrales del RMS global triaxial de velocidad en mm/s obtenidos del desarrollo sano. No son límites de aprobación normativos de ISO para el dron.

Los valores redondeados a cuatro decimales son solo para la presentación en el anexo. Para reproducir predicciones, utilizar el JSON de precisión original. Redondear antes de ejecutar puede cambiar decisiones cercanas a umbrales y no conserva necesariamente la equivalencia MATLAB/Python.

### 3.2 Presentación a cuatro decimales

```json
{
  "binary_normalization": {
    "median": [
      -1.6962,
      -2.8894,
      -2.8631,
      -1.0467,
      -1.6258,
      -1.7096
    ],
    "active": [
      true,
      true,
      true,
      true,
      true,
      true
    ],
    "scale": [
      0.2883,
      0.1569,
      0.1695,
      0.0998,
      0.1007,
      0.1021
    ]
  },
  "threshold_a": 3.3368,
  "p95_v": 0.4804,
  "p99_v": 0.5212,
  "multiclass_normalization": {
    "median": [
      -1.6926,
      -2.7024,
      -2.7454,
      -1.055,
      -1.5715,
      -1.7028
    ],
    "active": [
      true,
      true,
      true,
      true,
      true,
      true
    ],
    "scale": [
      0.6509,
      0.2615,
      0.2511,
      0.1428,
      0.2136,
      0.1594
    ]
  },
  "prototypes": [
    [
      1.0162,
      0.3143,
      0.4935,
      0.2991,
      1.351,
      0.8532
    ],
    [
      -1.0097,
      0.4023,
      -0.2279,
      -0.0434,
      0.4568,
      0.3194
    ],
    [
      0.3657,
      -0.0176,
      0.6028,
      0.0527,
      -0.4101,
      -0.2678
    ],
    [
      -0.7122,
      0.2981,
      -0.224,
      0.007,
      -0.2894,
      -0.3166
    ]
  ],
  "fit_count": 2256,
  "fit_healthy_count": 449,
  "class_order": [
    "Healthy",
    "Damaged_LR",
    "Damaged_UR",
    "Unbalanced_LR",
    "Unbalanced_UR"
  ]
}
```

### 3.3 JSON ejecutable con la precisión exportada

Guardar el siguiente bloque como `frozen_parameters.json` si Claude necesita reconstruir el archivo:

```json
{
  "binary_normalization": {
    "median": [
      -1.6961802655297666,
      -2.889406226514298,
      -2.8630859685651466,
      -1.0467387221802835,
      -1.6258130373971145,
      -1.7095977406475589
    ],
    "active": [
      true,
      true,
      true,
      true,
      true,
      true
    ],
    "scale": [
      0.2882681524832248,
      0.15691703652275896,
      0.1695127761669122,
      0.09977652045271035,
      0.10065468866960801,
      0.10212790299597936
    ]
  },
  "threshold_a": 3.3368315996445954,
  "p95_v": 0.4803740159608693,
  "p99_v": 0.5212226405451932,
  "multiclass_normalization": {
    "median": [
      -1.6926405817399177,
      -2.7023971730649254,
      -2.745394588863592,
      -1.05499159602192,
      -1.5714674581369945,
      -1.7027637697245814
    ],
    "active": [
      true,
      true,
      true,
      true,
      true,
      true
    ],
    "scale": [
      0.6509436174910467,
      0.26151075083593706,
      0.2511110010054308,
      0.14280354329010606,
      0.21355717628764237,
      0.15939252055907827
    ]
  },
  "prototypes": [
    [
      1.016215997415066,
      0.31432289065733066,
      0.4935336421681137,
      0.29911921361748894,
      1.3509723691041962,
      0.853242412995094
    ],
    [
      -1.009664737478668,
      0.40234874107507856,
      -0.22793403466778767,
      -0.04339423910627335,
      0.4568064431340732,
      0.3193637267064628
    ],
    [
      0.36573550522060283,
      -0.017641855652096555,
      0.6028309310510044,
      0.05272496091836611,
      -0.41010683808879445,
      -0.2678040250933794
    ],
    [
      -0.7121953288225809,
      0.2980774825812153,
      -0.22398372085500334,
      0.007025280182138317,
      -0.2893649563347089,
      -0.31656363960929046
    ]
  ],
  "fit_count": 2256,
  "fit_healthy_count": 449,
  "class_order": [
    "Healthy",
    "Damaged_LR",
    "Damaged_UR",
    "Unbalanced_LR",
    "Unbalanced_UR"
  ]
}
```

### 3.4 Configuración asociada

```json
{
  "fs_hz": 1024,
  "n_samples": 500,
  "highpass_hz": 10,
  "lowpass_hz": 409.6,
  "butterworth_order": 4,
  "gap_factor": 1.5,
  "numeric_energy_floor": 1e-12,
  "scale_floor": 1e-12,
  "reference_band_hz": [
    10,
    100
  ],
  "comparison_band_hz": [
    140,
    200
  ],
  "development_intervals_s": [
    [
      10,
      70
    ],
    [
      70,
      130
    ],
    [
      130,
      190
    ],
    [
      190,
      250
    ]
  ],
  "test_intervals_s": [
    [
      252,
      312
    ],
    [
      312,
      372
    ]
  ],
  "class_order": [
    "Healthy",
    "Damaged_LR",
    "Damaged_UR",
    "Unbalanced_LR",
    "Unbalanced_UR"
  ]
}
```

La configuración describe el operador espectral implementado; no debe presentarse como una aplicación de `filtfilt` sobre el registro completo. La guarda de dos segundos separa desarrollo de prueba, pero no crea vuelos independientes.

## 4. Observación #41: robustez bajo ruido

### 4.1 Corrección de la propuesta de Claude

Los resultados de ruido ya se habían observado. Por tanto, una regla elegida ahora no puede llamarse “preinscrita”, “previamente seleccionada” o confirmatoria para estas mismas salidas. Se propone un criterio práctico retrospectivo que debe quedar explícitamente etiquetado y ser revisado por el asesor. Superar un umbral de cinco puntos porcentuales no equivale a significación estadística.

Propuesta de regla: para cada método calcular D(SNR)=BA_sin_ruido−media_de_BA_con_ruido(SNR), en puntos porcentuales. Se considera degradación práctica según este criterio si D(SNR)>5,00 pp; la igualdad no lo activa. El nivel de referencia propuesto es 20 dB y se muestran también 30,15 y 10 dB para describir el comportamiento completo.

No se ha documentado una justificación externa del margen de cinco puntos: es un margen práctico propuesto, no normativo. Su aprobación depende del asesor. Si exige una regla seleccionada antes de observar resultados, la solución requiere una nueva evaluación planificada antes de ejecutarla; este documento no demuestra ese requisito.

### 4.2 Evidencia disponible

Fuente: `BTF25_codigo/results/noise_robustness.csv`. Diez realizaciones por nivel SNR, mismas 1 130 ventanas de prueba y parámetros previamente congelados. La fuente corresponde a la implementación Python: no atribuir estas pruebas a MATLAB sin evidencia de ejecución equivalente. No se repitieron aquí las perturbaciones; se recalculó su resumen desde el CSV existente. Los mínimos y máximos son rangos entre realizaciones, no intervalos de confianza. Las realizaciones sintéticas no constituyen diez vuelos independientes.

Valores basales: BTF25 70,575221 % y RMS 58,628319 % de exactitud balanceada binaria.

| Método | SNR dB | Realizaciones | BA media % | BA mínima % | BA máxima % | Caída media pp | Realizaciones caída >5pp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BTF25 | 30 | 10 | 71.067478 | 70.464602 | 71.681416 | -0.492257 | 0 |
| RMS | 30 | 10 | 58.467920 | 58.075221 | 58.794248 | 0.160398 | 0 |
| BTF25 | 20 | 10 | 74.646018 | 72.676991 | 76.714602 | -4.070796 | 0 |
| RMS | 20 | 10 | 58.633850 | 57.688053 | 59.734513 | -0.005531 | 0 |
| BTF25 | 15 | 10 | 52.461283 | 51.493363 | 53.982301 | 18.113938 | 10 |
| RMS | 15 | 10 | 56.648230 | 55.918142 | 58.185841 | 1.980088 | 0 |
| BTF25 | 10 | 10 | 50.000000 | 50.000000 | 50.000000 | 20.575221 | 10 |
| RMS | 10 | 10 | 45.757743 | 44.192478 | 46.681416 | 12.870575 | 10 |

Una caída negativa representa aumento de la métrica. A 20 dB, BTF25 aumenta en promedio 4,070796 pp y RMS cambia +0,005531 pp, por lo que ninguno activa el criterio propuesto. BTF25 sí supera la caída de cinco pp a 15 y 10 dB; RMS lo supera a 10 dB. La mejora con ruido a 20 dB no demuestra una mejora general en operación real ni invalida el deterioro a menores SNR.

### 4.3 Texto propuesto para la tesis

> La robustez se examinó mediante perturbaciones gaussianas sintéticas en cuatro niveles de SNR, con diez realizaciones por nivel y parámetros congelados. Como criterio práctico retrospectivo se consideró una disminución mayor de cinco puntos porcentuales en la exactitud balanceada media respecto del caso sin ruido. Este criterio fue establecido después de disponer de los resultados y no se interpreta como preinscripción ni como una prueba de significación estadística. A 20 dB, BTF25 obtuvo una exactitud balanceada media de 74,646018 %, frente a 70,575221 % sin ruido, por lo que no se observó degradación según el criterio propuesto. A 15 y 10 dB, el desempeño medio disminuyó a 52,461283 % y 50,000000 %, respectivamente. La evaluación describe la respuesta a las perturbaciones sintéticas implementadas y no acredita robustez frente a todos los mecanismos de ruido de la adquisición o de nuevos vuelos.

## 5. Observación #4: índices de Word

La inspección del DOCX disponible detectó tres campos de índice: `TOC \h \o "1-3"`, `TOC \h \t "TablaTitulo,1"` y `TOC \h \t "FiguraTitulo,1"`. Su existencia no acredita que sus páginas o entradas estén actualizadas.

Procedimiento pendiente después de que Claude integre todos los pasos:

1. Abrir en Microsoft Word la versión final integrada y guardarla con un nombre de versión final.
2. Pulsar Ctrl+A y después F9; en equipos con teclas especiales puede ser Fn+F9. Si Word pregunta, elegir “Actualizar toda la tabla”.
3. Hacer clic dentro de cada índice (contenido, tablas y figuras) y seleccionar “Actualizar tabla” / “Actualizar toda la tabla”, para comprobar que los tres se actualizan.
4. Revisar que se incluyan todos los títulos y que los estilos TablaTitulo y FiguraTitulo se apliquen correctamente. Si falta alguna entrada, corregir su estilo y actualizar otra vez.
5. Revisar referencias cruzadas y comprobar que no haya mensajes de referencia perdida. Actualizar los campos en encabezados/pies si existen referencias allí.
6. Guardar y exportar un PDF. Comparar las páginas indicadas en los índices con las páginas reales de sus secciones, tablas y figuras, incluido el esquema de números romanos/arábigos que utilice la tesis.
7. Conservar DOCX y PDF verificados como evidencia del cierre de #4.

No se ha efectuado aquí esa actualización ni la verificación visual de paginación. La tarea debe hacerse sobre la versión final integrada, pues añadir texto después vuelve a cambiar páginas.

## 6. Código reproducible de la auditoría temporal

La nueva auditoría de tiempos se ejecutó en Python. No se afirma que este nuevo cálculo se haya ejecutado en MATLAB. El código siguiente reproduce las definiciones y tablas con los originales usando NumPy, pandas y openpyxl. Colocar los cinco archivos en `datos`, guardar como `auditar_tiempos_paso3.py` y ejecutar con Python. No usa los valores redondeados del modelo.

```python
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from openpyxl import load_workbook

archivos = {
    'Healthy.xlsx': 'Healthy',
    'Damaged Bottom Right Blade.xlsx': 'Damaged_LR',
    'Damaged Top Right Blade.xlsx': 'Damaged_UR',
    'Unbalanced Bottom Right Blade.xlsx': 'Unbalanced_LR',
    'Unbalanced Top Right Blade.xlsx': 'Unbalanced_UR',
}
resultados = []
for nombre, condicion in archivos.items():
    ruta = Path('datos') / nombre
    wb = load_workbook(ruta, read_only=True, data_only=True)
    try:
        t = np.array([float(fila[0]) for fila in wb.worksheets[0].iter_rows(
            min_row=2, max_col=1, values_only=True)], dtype=float)
    finally:
        wb.close()
    if len(t) < 2 or not np.isfinite(t).all():
        raise ValueError(f'Tiempos ausentes o inválidos: {nombre}')
    dt = np.diff(t)
    if not (dt > 0).all():
        raise ValueError(f'Tiempos duplicados o no crecientes: {nombre}')
    mediana = np.median(dt)
    continuo = dt <= 1.5 * mediana
    regular = dt[continuo]
    brechas = dt[~continuo]
    rms = np.sqrt(np.mean((regular-mediana)**2))
    fila = dict(condition=condicion, filename=nombre,
        sha256=hashlib.sha256(ruta.read_bytes()).hexdigest(),
        samples=len(t), intervals=len(dt), gaps=len(brechas),
        continuous_intervals=len(regular), gap_threshold_ms=1500*mediana,
        gap_min_ms=1000*brechas.min() if len(brechas) else np.nan,
        gap_max_ms=1000*brechas.max() if len(brechas) else np.nan,
        jitter_std_all_ms=1000*np.std(dt, ddof=0),
        jitter_std_continuous_ms=1000*np.std(regular, ddof=0),
        jitter_rms_continuous_ms=1000*rms,
        jitter_rms_continuous_percent=100*rms/mediana)
    for grupo, valores in [('all', dt), ('continuous', regular)]:
        for p, valor in zip([1,5,50,95,99], np.percentile(
            valores, [1,5,50,95,99], method='linear')):
            fila[f'p{p}_{grupo}_ms'] = 1000*valor
    resultados.append(fila)
pd.DataFrame(resultados).to_csv('percentiles_y_jitter.csv', index=False)
```

## 7. Instrucción para Claude

Audita este documento como evidencia del paso 3. Verifica especialmente las definiciones de jitter, unidades, orden de características/prototipos, uso de precisión original y condición retrospectiva de la regla de ruido. Conserva las propuestas para la integración posterior, una vez completados los seis pasos. No presentes #41 como preinscrita y no declares #4 cerrada sin DOCX/PDF actualizado y verificado. Distingue cálculo realizado, texto propuesto, aprobación pendiente y tarea pendiente. Si el asesor requiere que también los nuevos cálculos de tiempos o ruido se ejecuten en MATLAB, señala esa exigencia como una comprobación adicional; no atribuyas a MATLAB una ejecución en Python.
