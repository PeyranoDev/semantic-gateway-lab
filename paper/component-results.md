# v0.6 — evaluación de componentes y réplica con semillas nuevas

Se completaron **1200 campañas**: 960 sobre cuatro mutantes aislados y 240
controles corregidos que observan todas las propiedades a la vez. Se mantienen
backend, contrato, presupuesto 120, profundidad ocho y corpus 64. Se usan 30
semillas nuevas (600–629) y ocho tratamientos fijados antes de la matriz.

**Hallazgo:** la biblioteca de tareas válidas mejora las fallas con historia bajo
el mismo mutador, pero perjudica la lectura fuera de alcance. Mutar el interior
de las tareas también mejora esas fallas respecto de sólo agregarles acciones.
Los resultados son del servicio y mutantes revisados; no se extrapolan a sistemas
independientes ni a superioridad frente a herramientas externas no ejecutadas.

## Resultados completos

Cada celda muestra detecciones/30 (media de llamadas con límite de 120).

| Tratamiento | Lectura ajena | Sobreventa | Confirmación sin pago | Reintegro repetido |
|---|---:|---:|---:|---:|
| Aleatorio | 30/30 (24.3) | 2/30 (118.3) | 3/30 (111.8) | 0/30 (120.0) |
| Warmup + aleatorio | 30/30 (48.3) | 1/30 (119.4) | 3/30 (114.2) | 0/30 (120.0) |
| Repetir tareas | 0/30 (120.0) | 0/30 (120.0) | 0/30 (120.0) | 0/30 (120.0) |
| Agregar sufijo | 26/30 (67.3) | 5/30 (115.9) | 1/30 (118.0) | 2/30 (118.8) |
| Mutar biblioteca aleatoria | 25/30 (41.5) | 2/30 (113.1) | 1/30 (116.3) | 0/30 (120.0) |
| Mutar tareas válidas | 8/30 (104.1) | 24/30 (71.2) | 18/30 (89.4) | 10/30 (101.4) |
| Feedback básico | 6/30 (109.0) | 12/30 (100.4) | 18/30 (86.2) | 10/30 (100.6) |
| Feedback enriquecido | 9/30 (107.2) | 22/30 (77.8) | 14/30 (94.4) | 10/30 (99.9) |

![Detección e incertidumbre descriptiva por tratamiento](figures/v06-detection.svg)

Los intervalos Wilson describen variación de búsqueda por semilla. Los ceros de
replay son un control de perturbación de tareas previamente válidas, no evidencia
de vencer a un fuzzer competitivo. random_bootstrap ejecuta warmup y luego
reinicia sin reutilizar sus tareas; mide ese procedimiento concreto.

## Separación de componentes

- **Biblioteca bajo mutación igual:** tareas válidas frente a programas aleatorios
  de las mismas longitudes da sobreventa 24/30 versus 2/30, confirmación sin pago
  18/30 versus 1/30 y reintegro 10/30 versus 0/30. En lectura ajena da 8/30 versus
  25/30. La calidad inicial cambia tanto warmup como fuentes/donantes de mutación.
- **Mutación completa frente a sufijo:** da sobreventa 24/30 versus 5/30,
  confirmación sin pago 18/30 versus 1/30 y reintegro 10/30 versus 2/30.
  La extensión funciona mejor en lectura, 26/30 versus 8/30. El contraste cambia
  la distribución de programas; no se presenta como un único operador aislado.
- **Warmup sin reutilización:** no mejora las tasas observadas; en lectura
  ambos motores aleatorios detectan 30/30 y el warmup suma exactamente 24 llamadas
  por detección. Para sobreventa pierde una detección por el menor presupuesto
  restante. Esto no representa todos los usos posibles del conocimiento de tareas.
- **Feedback enriquecido frente al básico:** sobreventa 22/30 versus 12/30,
  confirmación sin pago 14/30 versus 18/30, lectura 9/30 versus 6/30 y reintegro
  10/30 en ambos. Conservamos estos efectos mixtos.

La biblioteca aleatoria no fue filtrada: 20 de sus 25 detecciones de lectura,
una de sobreventa y la única de confirmación sin pago ocurren durante warmup.
Esas llamadas cuentan. Por eso no se atribuyen todos sus hallazgos a mutación.

## Contrastes por semilla

Se publican los **24 contrastes fijados**. Delta de llamadas = derecha menos
izquierda; un valor negativo favorece a la derecha en esfuerzo limitado.
El porcentaje de detección es una diferencia en puntos porcentuales, no un
incremento relativo. Intervalos percentiles con 5000 remuestreos de los 30 pares.

| Propiedad | Izquierda → derecha | Delta llamadas | Bootstrap 95% | Delta detección (pp) |
|---|---|---:|---:|---:|
| CONFIRM_PAYMENT | mutation_unseeded → sequence_uniform | -26.97 | [-40.70, -11.87] | +56.7 |
| CONFIRM_PAYMENT | seed_extend → sequence_uniform | -28.60 | [-41.37, -16.03] | +56.7 |
| CONFIRM_PAYMENT | seed_replay → sequence_uniform | -30.63 | [-42.13, -19.73] | +60.0 |
| CONFIRM_PAYMENT | random → random_bootstrap | 2.40 | [0.00, 5.60] | +0.0 |
| CONFIRM_PAYMENT | random_bootstrap → sequence_uniform | -24.80 | [-36.07, -14.10] | +50.0 |
| CONFIRM_PAYMENT | sequence_enabled → sequence_enriched | 8.13 | [-3.33, 19.00] | -13.3 |
| BOOKING_SCOPE | mutation_unseeded → sequence_uniform | 62.60 | [41.67, 81.87] | -56.7 |
| BOOKING_SCOPE | seed_extend → sequence_uniform | 36.77 | [20.70, 52.10] | -60.0 |
| BOOKING_SCOPE | seed_replay → sequence_uniform | -15.93 | [-28.13, -5.87] | +26.7 |
| BOOKING_SCOPE | random → random_bootstrap | 24.00 | [24.00, 24.00] | +0.0 |
| BOOKING_SCOPE | random_bootstrap → sequence_uniform | 55.73 | [42.10, 67.73] | -73.3 |
| BOOKING_SCOPE | sequence_enabled → sequence_enriched | -1.80 | [-5.40, 0.80] | +10.0 |
| REFUND_REPLAY | mutation_unseeded → sequence_uniform | -18.63 | [-30.13, -8.93] | +33.3 |
| REFUND_REPLAY | seed_extend → sequence_uniform | -17.40 | [-28.73, -7.33] | +26.7 |
| REFUND_REPLAY | seed_replay → sequence_uniform | -18.63 | [-29.33, -8.70] | +33.3 |
| REFUND_REPLAY | random → random_bootstrap | 0.00 | [0.00, 0.00] | +0.0 |
| REFUND_REPLAY | random_bootstrap → sequence_uniform | -18.63 | [-29.70, -8.90] | +33.3 |
| REFUND_REPLAY | sequence_enabled → sequence_enriched | -0.73 | [-11.50, 9.43] | +0.0 |
| SLOT_CAPACITY | mutation_unseeded → sequence_uniform | -41.87 | [-57.07, -25.17] | +73.3 |
| SLOT_CAPACITY | seed_extend → sequence_uniform | -44.67 | [-56.60, -31.43] | +63.3 |
| SLOT_CAPACITY | seed_replay → sequence_uniform | -48.77 | [-60.00, -36.50] | +80.0 |
| SLOT_CAPACITY | random → random_bootstrap | 1.07 | [0.00, 2.93] | -3.3 |
| SLOT_CAPACITY | random_bootstrap → sequence_uniform | -48.13 | [-59.84, -36.57] | +76.7 |
| SLOT_CAPACITY | sequence_enabled → sequence_enriched | -22.57 | [-34.73, -11.87] | +33.3 |

![Contrastes de esfuerzo con incertidumbre por semilla](figures/v06-paired-effort.svg)

Por ejemplo, mutar tareas válidas frente a extenderlas reduce el esfuerzo
limitado de sobreventa en 44,67 llamadas (intervalo descriptivo −56,60 a −31,43),
pero lo aumenta para lectura ajena en 36,77 (20,70 a 52,10). En feedback,
enriquecido reduce sobreventa en 22,57 (−34,74 a −11,87), mientras el contraste
de confirmación es +8,13 (−3,33 a 19,00). No se realizan pruebas de significancia
ni selección de contrastes favorables. No son intervalos entre empresas;
los intervalos degenerados tampoco demuestran ausencia de diferencias universales.

## Controles, costos y revalidación

292 campañas detectan el objetivo. Los 584 testigos originales/minimizados
se reejecutan con igualdad exacta de respuesta y estado SQL. fixed completa
240 campañas y **28800 llamadas de búsqueda** sin discrepancias de ninguna
propiedad. ANY evita duplicar cuatro veces el mismo stream de control.

| Variante | Búsqueda | Minimización | Replay tras minimizar | Revalidación | HTTP total |
|---|---:|---:|---:|---:|---:|
| confirm_unpaid | 25506 | 364 | 116 | 288 | 26312 |
| fixed | 28800 | 0 | 0 | 0 | 28838 |
| read_scope | 18653 | 654 | 134 | 552 | 20031 |
| refund_replay | 27020 | 1110 | 160 | 338 | 28666 |
| slot_capacity | 25082 | 369 | 136 | 327 | 25952 |

La matriz principal consume 125061 llamadas de búsqueda y 129799 llamadas HTTP
en todas sus etapas, incluidos 4 logins y 34 llamadas de controles por variante.
La suite de tests y replays adicionales de CI están fuera de esos conteos.
Python 3.12.14; SQLite 3.53.1. Las versiones de runtime
difieren de la fase v0.5; no se comparan sus tiempos como resultados equivalentes.

## Reparación del verificador y trazabilidad

El verificador inicial comparaba una tupla de Wilson con su representación JSON
como lista. Se congeló una conversión tupla→lista y un test de roundtrip, y se
repitieron las 1200 campañas completas sin modificar los motores o parámetros.
La primera corrida se conserva en results/salon-v06/intermediate/attempt1 y
no se suma como otra muestra independiente. repair-verification.json comprueba
los 1200 resultados semánticos entre intentos, omitiendo solamente elapsed_s.
Ver docs/v06-validation-repair.md.

Configuración SHA-256: 2294a82ca0d039bed2cf68732b140afeca0d49d6d1943c9a828fa9314aa99e92.
JSONL principal SHA-256: fdb0b94608359844810464a72cb2f42cb04a49653d28b87a025d12aff4d7ccfa.
Código corregido congelado: 6f9f0b359cde92dc1bd694ea1a279fc04e02173f.

## Reproducir

    python -m pip install -r backends/salon/requirements.lock
    python -m unittest discover -s tests -v
    python -m scripts.analyze_salon_ablation
    python -m scripts.replay_salon_ablation
    python -m scripts.check_salon_repair
    python -m integrations.salon_ablation.run --out results/local-ablation

Para las figuras: instalar paper/requirements-figures.txt y ejecutar
python -m scripts.plot_salon_ablation. Código, fuente y configuración se verifican
por hashes; ninguna corrida nueva sobrescribe una carpeta no vacía.

## Qué queda pendiente

La comparación con RESTler sigue sin ejecutar; seed_extend es una referencia
interna y no se llama RESTler. El protocolo externo está preparado, y la revisión
focalizada identificó antecedentes de secuencias, security checkers y pruebas
guiadas por EPA. Falta revisión completa de esas fuentes, evaluación externa y
un sistema o contrato revisado independientemente. Esta fase mejora la separación
de componentes dentro de un caso conocido; no prueba seguridad ni generalización.
