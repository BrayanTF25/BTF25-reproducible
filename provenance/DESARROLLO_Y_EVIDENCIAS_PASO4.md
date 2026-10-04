# Desarrollo y evidencias del paso 4 — Observación #9

Tesis BTF25 — Brayan J. Tafur Falcón. Fecha: 3 de octubre de 2026.

Documento para compartir con Claude: contiene la resolución documental de la ruta 4a, la comprobación numérica del contraste y los textos para integrar después en la tesis. No requiere esperar una aprobación del asesor para preparar la redacción. La revisión del asesor se realizará sobre el trabajo entregado.

## 1. Decisión aplicada y alcance del cierre

Se adopta la **ruta 4a: reconocer expresamente que el contraste es exploratorio y que no se dispone de evidencia de preselección de la regla estadística antes de observar la prueba**.

No se crea una preinscripción retroactiva ni se inventan vuelos nuevos. El congelamiento de los parámetros del clasificador antes de predecir el conjunto de prueba y la preselección de una prueba estadística son requisitos distintos: el primero no demuestra el segundo. Un comentario del código o la existencia de un archivo de configuración tampoco acredita una fecha de preselección independiente.

El desarrollo del paso 4 por esta ruta queda preparado en su totalidad para la integración. **La observación #9 conserva el estado “parcial reconocido”**: documentar correctamente la limitación no satisface el requisito original de una regla elegida antes de ver los resultados. Su cierre confirmatorio requeriría la ruta 4b, con un protocolo prospectivo y nuevos datos adecuados.

## 2. Evidencias revisadas y nuevo cálculo

Se examinó `BTF25_codigo/run_pipeline.py`, en particular la generación de `block_indicators.csv`, el cálculo de `exploratory_contrast` y la enumeración de remuestreos. Se utilizaron las predicciones reales almacenadas en `BTF25_codigo/results/test_predictions.csv` y los resultados exportados en `BTF25_codigo/results/results.json`.

Se reconstruyeron los aciertos por bloque y registro desde las predicciones, sin reutilizar la función de contraste original. Después se enumeraron nuevamente los 32 patrones de signos y los 1 024 remuestreos de bloques. Los valores coincidieron con los resultados almacenados. Esta auditoría adicional se ejecutó en Python; no se debe afirmar que se volvió a ejecutar el contraste en MATLAB en este paso. La ejecución y equivalencia de los clasificadores en MATLAB corresponden al paso 2.

SHA-256 del CSV de predicciones auditado:

`a 8adebda72ded1420053b8a2af9b7a7efc43108bd8c56fea9e0e48f1654f3b84`

| Elemento | Valor verificado |
|---|---:|
| Fragmentos de prueba | 1 130 |
| Archivos / registros | 5, uno por condición |
| Bloques de prueba por registro | 2 |
| Bloques de prueba totales | 10 |
| Fragmentos por registro | 226 |
| BA de BTF25 | 70,575221 % |
| BA de RMS global | 58,628319 % |
| Diferencia BTF25 − RMS | 11,946903 puntos porcentuales |
| Patrones de inversión de signos | 32 |
| Patrones en la cola unilateral | 2 |
| Valor p condicional exploratorio | 0,0625 |
| Remuestreos de bloques enumerados | 1 024 |
| Percentiles 2,5 y 97,5 de la diferencia remuestreada | 9,513274–14,380531 pp |

**Correcciones de nomenclatura:** p=0,0625 no procede de McNemar. El código revisado tampoco utiliza 1 000 sorteos para ese intervalo: enumera 1 024 combinaciones ordenadas de remuestreo. No copiar las menciones antiguas “McNemar” o “bootstrap de 1 000” para describir este resultado.

## 3. Métrica e indicadores utilizados

La métrica principal es la exactitud balanceada binaria:

BA = 0,5 × (sensibilidad + especificidad).

Se considera falla cualquier clase distinta de Healthy. Ambos métodos se evalúan sobre exactamente los mismos fragmentos de prueba.

Para cada bloque b del registro c y método m, el indicador es q_(m,c,b)=número de clasificaciones binarias correctas / número de fragmentos evaluados en ese bloque. Al contener cada bloque una sola condición real, q es especificidad en Healthy y sensibilidad de esa condición en los registros con falla; **no es una exactitud balanceada calculada dentro de un bloque monoclase**.

Se agrega por registro sumando aciertos y tamaños de sus dos bloques. Se define d_c=q_(A,c)−q_(B,c). Para recuperar la diferencia global de BA, se asigna peso 0,5 al registro Healthy y se reparte el peso 0,5 restante entre los registros con falla de forma proporcional a sus fragmentos de prueba. Aquí todos tienen 226 fragmentos, por lo que cada registro con falla pesa 0,125. No se aplica una media simple de los cinco registros.

### 3.1 Indicadores reconstruidos por registro

| Condición | n | Aciertos BTF25 | Aciertos RMS | q BTF25 % | q RMS % | d pp | Peso |
|---|---:|---:|---:|---:|---:|---:|---:|
| Healthy | 226 | 211 | 202 | 93.362832 | 89.380531 | 3.982301 | 0.500 |
| Damaged_LR | 226 | 153 | 166 | 67.699115 | 73.451327 | -5.752212 | 0.125 |
| Damaged_UR | 226 | 104 | 21 | 46.017699 | 9.292035 | 36.725664 | 0.125 |
| Unbalanced_LR | 226 | 100 | 54 | 44.247788 | 23.893805 | 20.353982 | 0.125 |
| Unbalanced_UR | 226 | 75 | 11 | 33.185841 | 4.867257 | 28.318584 | 0.125 |

BTF25 no supera a RMS en todas las condiciones: en Damaged_LR el indicador de aciertos es menor. Esta comparación por condición es distinta de comparar niveles de vibración frente a Healthy; no mezclar ambas afirmaciones.

## 4. Qué prueba produjo p=0,0625

El estadístico observado es T=Σ_c w_c d_c, que coincide con BA_A−BA_B=0,119469026549 en escala 0–1.

El código enumeró todos los vectores s=(s_1,…,s_5) con componentes −1 o +1 y calculó T_s=Σ_c w_c s_c d_c. La cola unilateral se calcula como:

p = número de patrones con T_s ≥ T_observado / 32.

Se utilizó tolerancia numérica 1e−14 en la comparación, tal como el código original. Se encontraron dos patrones en la cola, por lo que p=2/32=0,0625. Al ser enumeración completa, no se añade una corrección de Monte Carlo. La resolución de la distribución es 1/32=0,03125; es un contraste muy discreto.

### 4.1 Hipótesis y supuestos

La pregunta direccional de interés es si BTF25 presenta mayor BA que RMS, con diferencia positiva. En un diseño confirmatorio con una población y unidades independientes bien definidas, podría formularse H0: θ≤0 y H1: θ>0, donde θ es la diferencia de desempeño en esa población.

**En los datos actuales no se ha definido ni muestreado una población de vuelos independientes que permita sostener esa inferencia.** Para interpretar el valor p de las inversiones de signo se requeriría que, bajo la referencia nula, la distribución conjunta de las contribuciones por registro fuera invariante frente a las inversiones independientes de sus signos. Este supuesto es más fuerte que asumir simplemente que la media de la diferencia es cero. Agrupar por archivo reduce la pseudorreplicación por ventanas, pero no demuestra ese supuesto.

Hay un único archivo publicado por condición. Las condiciones son distintas, los métodos no se asignaron aleatoriamente y la independencia entre adquisiciones no queda demostrada por los archivos ni por la separación temporal. Por ello, se conserva p como una **medida exploratoria condicional a esos supuestos**, no como una prueba confirmatoria validada para nuevos vuelos.

La enumeración es exacta respecto de sus 32 patrones matemáticos; eso no convierte automáticamente en exacta o válida la inferencia sobre vuelos reales. No presentar los 1 130 fragmentos o los 10 bloques como1 130 o10 vuelos independientes.

### 4.2 Regla de decisión y margen práctico

El código existente utiliza dos condiciones conjuntas: p<0,05 y límite inferior del intervalo remuestreado de ΔBA>0,02. La segunda corresponde a un margen práctico de dos puntos porcentuales. Se conserva esta información para documentar lo realmente ejecutado, sin llamarla regla preinscrita.

Con estos resultados, p=0,0625 no satisface p<0,05, aunque el límite inferior condicional supera 0,02. En consecuencia, la propia regla almacenada no declaró superioridad.

El contraste de signos está centrado en diferencia cero: **no constituye una prueba específica de H0: θ≤0,02**. Además, el intervalo y el valor p proceden de esquemas de incertidumbre distintos. No afirmar que su conjunción constituye un contraste confirmatorio único del margen de dos puntos. El margen 0,02 carece aquí de justificación normativa o operacional independiente y debe etiquetarse como referencia práctica exploratoria.

## 5. Interpretación del remuestreo de bloques

Cada archivo aporta dos bloques de prueba. El código toma dos bloques con reemplazo entre esos dos bloques; hay cuatro elecciones ordenadas por archivo: (1,1),(1,2),(2,1),(2,2). Al combinar cinco archivos hay 4^5=1 024 elecciones ordenadas. Algunas producen el mismo estadístico, pero sus repeticiones conservan la multiplicidad del remuestreo.

Los percentiles 2,5 y 97,5 se obtuvieron con interpolación lineal:

- BA de BTF25: 68,307522–72,842920 %.
- BA de RMS: 55,839325–61,417312 %.
- Diferencia: 9,513274–14,380531 puntos porcentuales.

Estos límites son condicionales a los archivos y sus bloques observados; no son intervalos que acrediten generalización a nuevos vuelos. Hay solo dos bloques por archivo, y no se ha demostrado independencia entre ellos. La incertidumbre que refleja este remuestreo es limitada y su cobertura nominal no está validada para una población operacional.

El intervalo positivo y p>0,05 no deben “resolverse” seleccionando otro contraste: describen procedimientos diferentes. El remuestreo modifica los bloques dentro de cada archivo; las inversiones de signo modifican las contribuciones entre registros. El primero no corrige las limitaciones del segundo.

## 6. Textos para integrar en la tesis

Los títulos siguientes identifican el destino temático. Claude debe localizar las secciones correspondientes en la tesis actual y ajustar su numeración, sin inventar nuevos resultados.

### 6.1 Diseño estadístico / metodología

> La exactitud balanceada binaria se utilizó como métrica principal de comparación entre BTF25 y RMS global, aplicados sobre los mismos fragmentos de prueba. Se calculó por bloque la proporción de clasificaciones correctas; al tratarse de bloques de una sola condición, este indicador correspondió a la especificidad en Healthy y a la sensibilidad en los registros con falla. Los indicadores se agregaron por archivo y se ponderaron para reconstruir la diferencia de exactitud balanceada. El contraste se presentó como exploratorio, dado que no se dispuso de evidencia de selección previa de la regla estadística antes de observar las salidas de prueba. Se enumeraron 32 inversiones de signo de las cinco contribuciones por archivo y se obtuvo un valor p unilateral condicional a la invariancia de signos bajo la referencia nula. La existencia de un único archivo por condición y la ausencia de evidencia de independencia entre adquisiciones limitaron su interpretación a los registros analizados.

### 6.2 Resultados / contraste estadístico

> BTF25 alcanzó una exactitud balanceada de 70,58 %, frente a 58,63 % del RMS global, con una diferencia descriptiva de 11,95 puntos porcentuales en 1 130 fragmentos de prueba. La enumeración de 32 patrones de inversión de signos por archivo produjo dos valores al menos tan grandes como el estadístico observado, obteniéndose p=0,0625. Bajo la referencia exploratoria de 0,05, no se cumplió el criterio de rechazo. Los percentiles del remuestreo de bloques situaron la diferencia entre 9,51 y 14,38 puntos porcentuales; estos límites fueron condicionales a los archivos y bloques disponibles y no se interpretaron como evidencia confirmatoria sobre nuevos vuelos.

### 6.3 Discusión de la hipótesis

> La diferencia observada favoreció descriptivamente a BTF25 en la métrica principal, pero no permitió afirmar superioridad estadística confirmatoria. El valor p exploratorio no cumplió la referencia de 0,05 y dependió de supuestos de invariancia de signos que no pudieron verificarse con un único archivo por condición. El intervalo condicional positivo no eliminó esas restricciones, pues se obtuvo mediante otro esquema de remuestreo. Tampoco se interpretó la ausencia de rechazo como equivalencia entre los métodos o como demostración de que BTF25 carece de utilidad. Los resultados se circunscribieron a los registros y condiciones analizados.

### 6.4 Limitación explícita de la observación #9

> No se dispuso de un registro fechado que acreditara la selección de la prueba y de su regla de decisión antes de observar los resultados del conjunto de prueba. En consecuencia, el análisis estadístico se reconoció como exploratorio y retrospectivo. La fijación de los parámetros del clasificador a partir del desarrollo se distinguió de la preselección del procedimiento inferencial. La evaluación confirmatoria de superioridad quedó pendiente de un protocolo definido previamente y de nuevas adquisiciones con unidades independientes adecuadas.

### 6.5 Conclusión vinculada al objetivo de comparación

> En los registros de prueba del DJI Mini 2 evaluado, BTF25 presentó mayor exactitud balanceada que RMS global, con una diferencia descriptiva de 11,95 puntos porcentuales. El análisis exploratorio obtuvo p=0,0625 y no respaldó una afirmación confirmatoria de superioridad. El resultado tampoco acreditó equivalencia entre los métodos ni generalización a nuevos vuelos.

### 6.6 Recomendación final

> Para una evaluación confirmatoria se recomienda definir y registrar, antes de analizar nuevas adquisiciones, la métrica principal, la dirección de la hipótesis, el margen de relevancia si corresponde, la unidad independiente, el procedimiento estadístico, las exclusiones y la regla de decisión. El diseño deberá incorporar repeticiones de adquisición independientes y separar efectivamente desarrollo y prueba. No deberá dividirse nuevamente un registro ya observado para denominarlo prueba nueva e independiente.

## 7. Texto para el cuadro de observaciones

| Campo | Texto preparado |
|---|---|
| Observación | #9 — Regla estadística previamente seleccionada |
| Estado propuesto | Parcialmente levantada: limitación reconocida |
| Acción ejecutada | Se documentó el carácter exploratorio y retrospectivo del contraste; se verificaron su estadístico, ponderaciones, 32 inversiones de signo y p=0,0625; se distinguió la preselección de la regla del congelamiento del clasificador. |
| Evidencia | Desarrollo y evidencias del paso 4, código y CSV de predicciones auditados, redacción propuesta para metodología, resultados, discusión y limitaciones. |
| Limitación restante | No existe evidencia de preselección anterior al conocimiento de las salidas de prueba; el diseño no contiene nuevas adquisiciones independientes suficientes para una evaluación confirmatoria. |
| Ruta futura de cierre | Protocolo prospectivo registrado y nuevos datos con unidades independientes, con tamaño de muestra justificado antes de evaluar. |

No incrementar automáticamente el conteo de observaciones levantadas. Este paso prepara la solución documental de 4a; no satisface4b y no modifica por sí solo el Excel o el DOCX.

## 8. Comprobación reproducible del valor p

Código Python autocontenido para verificar el estadístico y la cola desde el CSV de predicciones. No reajusta el clasificador y no calcula un contraste alternativo.

```python
from pathlib import Path
from itertools import product
import numpy as np
import pandas as pd

ruta = Path('test_predictions.csv')
f = pd.read_csv(ruta)
requeridas = {'class_id', 'pred_a', 'pred_b'}
if not requeridas.issubset(f.columns):
    raise ValueError('Faltan columnas del CSV de predicciones')
if set(f.class_id.unique()) != {0,1,2,3,4}:
    raise ValueError('Se requieren las cinco condiciones')
y = (f.class_id.to_numpy() > 0).astype(int)
f['acierto_a'] = (f.pred_a.to_numpy() == y).astype(int)
f['acierto_b'] = (f.pred_b.to_numpy() == y).astype(int)
g = f.groupby('class_id', sort=True).agg(
    n=('class_id','size'), a=('acierto_a','sum'), b=('acierto_b','sum'))
d = ((g.a-g.b)/g.n).to_numpy()
w = np.r_[0.5, 0.5*g.n.iloc[1:].to_numpy()/g.n.iloc[1:].sum()]
observado = float(w @ d)
estadisticos = np.array([float(w @ (d*np.array(signos)))
                        for signos in product([-1,1], repeat=5)])
cola = int(np.sum(estadisticos >= observado-1e-14))
p = cola/len(estadisticos)
print('Delta BA:', observado)
print('Delta BA, puntos porcentuales:', 100*observado)
print('Patrones:', len(estadisticos), 'Cola:', cola, 'p:', p)
assert abs(observado-0.11946902654867257) < 1e-12
assert len(estadisticos) == 32 and cola == 2 and p == 0.0625
```

Salida verificada: ΔBA=0,119469026549; diferencia=11,9469026549 pp; patrones=32; cola=2; p=0,0625.

## 9. Fuente metodológica consultada en este paso

American Statistical Association. The ASA Statement on p-Values: Context, Process, and Purpose (2016). DOI: https://doi.org/10.1080/00031305.2016.1154108

Declaración institucional: https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf

Se consultó para apoyar la interpretación: el valor p no es la probabilidad de que una hipótesis sea verdadera y no mide por sí solo la importancia de un efecto. Esta declaración no valida específicamente el contraste de cinco registros de la tesis ni proporciona un margen normativo de dos puntos porcentuales. No se atribuye a este paso una consulta de los libros de Good o Edgington y Onghena ni de otras referencias todavía no verificadas.

## 10. Instrucción para Claude

Audita este contenido como desarrollo completo de la ruta 4a del paso 4. Conserva las cifras y verifica su coherencia con los archivos del proyecto. Cuando se integren todos los pasos, sustituye cualquier referencia a McNemar para este p, corrige el número de remuestreos a 1 024 y elimina afirmaciones de preinscripción o superioridad confirmatoria. Mantén la observación #9 como parcial reconocida y no solicites ahora un visto bueno del asesor: prepara el contenido para que revise la tesis ya integrada. No inventes una fecha de registro, nuevos vuelos, independencia entre bloques, tamaño muestral confirmatorio o documentación de preselección que no exista.
