# Evidencia de ejecución y comparación MATLAB — Paso 2

**Proyecto:** BTF25 para el DJI Mini 2 evaluado  
**Ejecución:** MATLAB R2024b (24.2.0.2712019)  
**Fecha local reportada por el paquete:** 3 de octubre de 2026

## Resultado de la auditoría

Se ejecutó el archivo `BTF25_paso2_completo.m` con los cinco archivos XLSX originales. El paquete de salida incluyó el código, parámetros congelados, hashes de entradas, manifiesto de segmentos, características, predicciones, matrices de confusión, métricas y pruebas numéricas.

Comparé esos CSV con la referencia Python entregada previamente:

- Los **5 hashes SHA-256** de los XLSX coinciden con la referencia.
- El manifiesto contiene **3,998 segmentos**. Los identificadores, filas inicial/final, tamaños, tiempos de inicio y fin, particiones y bloques coinciden con Python; las pequeñas diferencias en tiempos son inferiores a `1.2×10⁻¹³ s`.
- Las características de **3 386 fragmentos totales (2 256 de desarrollo y 1 130 de prueba)** coinciden. La máxima diferencia absoluta fue menor que `6.1×10⁻¹⁴` en las características y `1.3×10⁻¹⁴` en `v_rms`.
- Para las **1,130 ventanas de prueba**, las predicciones binarias de BTF25 y RMS, la clasificación multiclase y el nivel de velocidad coinciden exactamente con Python.
- El mayor error absoluto en `score_a` fue `1.65×10⁻¹²`, menor que la tolerancia acordada de `1×10⁻¹¹`.
- El registro de MATLAB reportó **28 pruebas numéricas aprobadas**.

## Métricas reproducidas

| Método | n | Exactitud | Exactitud balanceada | F1 macro | Kappa |
|---|---:|---:|---:|---:|---:|
| BTF25 binario | 1,130 | 0.56903 | 0.70575 | 0.55189 | 0.23404 |
| RMS binario | 1,130 | 0.40177 | 0.58628 | 0.40060 | 0.08451 |
| BTF25 multiclase | 1,130 | 0.41858 | 0.41858 | 0.39414 | 0.27323 |

Las matrices de confusión y métricas coinciden con la referencia Python. En binario, BTF25 obtuvo sensibilidad `0.47788` y especificidad `0.93363`; RMS obtuvo sensibilidad `0.27876` y especificidad `0.89381`.

## Estado y alcance

**La ejecución MATLAB y la comparación cruzada con Python quedaron verificadas en esta auditoría.** El archivo `comparacion_local.json` del ZIP se generó antes de esta revisión y por eso todavía dice `full_feature_score_manifest_comparison: pending_review_of_exported_csv` y `step2_closed: false`. La comparación posterior descrita arriba resuelve ese pendiente técnico.

Esto documenta la ruta **2a: ejecución en MATLAB y comprobación frente a Python**. La aceptación formal de la redacción del OE2 y de la implementación como evidencia de la observación #39 corresponde al asesor. Estos resultados no constituyen una nueva evaluación estadística de superioridad; reproducen la evaluación ya calculada.

## Archivos fuente

- Paquete recibido: `20261003_170729_RESULTADOS_PASO2_PARA_REVISAR.zip`.
- MATLAB: `BTF25_paso2_completo.m`.
- Evidencia clave: `estado.json`, `comparacion_local.json`, `manifest.csv`, `features.csv`, `test_predictions.csv`, `metricas_matlab.csv`, matrices binarias y multiclase, `input_hashes.csv` y `pruebas_numericas.csv`.
