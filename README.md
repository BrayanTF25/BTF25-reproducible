# BTF25 reproducible — versión 1.0.0

Clasificación binaria y multiclase de vibraciones en cinco registros del DJI Mini 2. BTF25 se compara con RMS global. Resultados de prueba: 1 130 fragmentos, BA BTF25 70,5752 %, RMS 58,6283 %, contraste exploratorio p=0,0625. La prueba es inversión de signos por cinco registros; no es McNemar. El remuestreo enumera 1 024 combinaciones de bloques.

## Estructura

- `python/`: implementación evaluada, configuración y pruebas.
- `matlab/BTF25_paso2_completo.m`: implementación realmente ejecutada por el autor en R2024b.
- `evidence/python/` y `evidence/matlab/`: salidas conservadas, separadas por implementación.
- `provenance/`: metadatos Figshare y auditorías.
- `SHA256SUMS.txt`: integridad del contenido del paquete, excluye su propio archivo y `.git`.

## Obtener datos

Descargar `Data.zip` desde https://doi.org/10.6084/m9.figshare.28765640.v1 o https://ndownloader.figshare.com/files/53550002 y extraer los cinco XLSX en una carpeta. Conservar nombres originales. Licencia CC0 1.0 confirmada por API. Los nombres y SHA-256 esperados constan en `python/source_inventory.csv` y `evidence/python/input_hashes.csv`. No se requiere acceso a Scopus para descargar los datos públicos.

## Python

Entorno original de ejecución: Python 3.12; versiones instaladas en `python/environment_executed.txt`. Dependencias mínimas en requirements.txt y versiones concretas en requirements-lock.txt.

Desde la carpeta `python`:

```bash
python -m pip install -r requirements-lock.txt
python test_rules.py
python run_pipeline.py --input "RUTA_A_LOS_CINCO_XLSX"
```

Las salidas nuevas se guardan en `python/results/`; las evidencias archivadas permanecen en `evidence/python/`. La ejecución completa lee los XLSX sin caché y puede tardar varios minutos. No usar parámetros redondeados para reproducir decisiones.

## MATLAB

Se verificó MATLAB R2024b (24.2.0.2712019), Signal Processing Toolbox y Java habilitado. No se promete compatibilidad con versiones anteriores no ensayadas.

1. Abrir `matlab` como Current Folder.
2. Escribir `BTF25_paso2_completo` en Command Window.
3. Elegir la carpeta con los cinco XLSX.
4. El script crea `BTF25_salida_FECHA_HORA` en esa carpeta y conserva sus CSV/JSON y pruebas.

Este script no recibe argumentos. El código queda copiado junto a sus resultados y sus hashes se registran. Las decisiones binarias, multiclase y niveles coincidieron con Python en la auditoría del paso 2; diferencias numéricas quedaron bajo 10^-11. Los experimentos de ruido y el contraste exploratorio archivados proceden de Python. Las banderas de cierre internas de la salida MATLAB preceden a la auditoría externa posterior; consultar la auditoría para la comparación completa.

## Método y alcance

Fragmentos continuos de 500 muestras a frecuencia nominal 1024 Hz, sin interpolar brechas. Interrupción si Δt > 1,5 veces su mediana. Desarrollo [10,250) s en cuatro bloques; prueba [252,372) s en dos bloques. La guarda temporal no acredita vuelos independientes. Descriptor de velocidad con Hann periódica y operador espectral Butterworth, bandas 10–100 y 140–200 Hz; no equivale a filtfilt sobre el registro ni es un límite normativo de ISO para el dron. Ajuste en desarrollo, modelo congelado y evaluación en prueba. Seis características y prototipos completos en frozen_parameters.json.

Sensibilidad BTF25 47,7876 %: la mejora descriptiva no demuestra superioridad estadística confirmatoria. Solo hay un registro por condición. Los intervalos por bloques son condicionales, y los supuestos del contraste de signos no se han demostrado. El criterio de degradación >5 pp bajo ruido es retrospectivo, según documentación del paso 3.

## Licencia y cita

Código de este paquete: MIT. Datos externos: CC0 1.0. Consultar THIRD_PARTY_NOTICES.md. Citar dataset y software por separado. El DOI de Figshare identifica únicamente el conjunto de datos. El software se identifica por su versión 1.0.0, su etiqueta v1.0.0 y su DOI propio, que se asigna al archivarlo en Zenodo.

## Publicación

Este repositorio es la publicación pública de la versión 1.0.0 del paquete. El release v1.0.0 se archiva en Zenodo como software, con el autor, la versión y la licencia indicados en CITATION.cff y .zenodo.json. Los scripts complementarios de la tesis (apartados J.7 a J.9 del Anexo J) no forman parte de este paquete.
