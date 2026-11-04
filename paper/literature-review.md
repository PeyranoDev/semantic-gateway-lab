# Revisión focalizada y auditoría de posición — 14 de octubre de 2026

Esta revisión usa fuentes primarias y distingue textos consultados de metadatos.
No es una revisión sistemática ni acredita que todas las publicaciones relevantes
fueran encontradas. Las decisiones sobre nuestra contribución son interpretaciones
de este proyecto, no resultados atribuidos a los autores citados.

## Trabajos más cercanos

| Trabajo | Fuente primaria y alcance consultado | Solapamiento establecido | Consecuencia para este paper |
|---|---|---|---|
| RESTler, ICSE 2019 [9] | PDF de los autores; algoritmo, dependencias y evaluación | Generación de secuencias con dependencias y respuestas como feedback | La generación con estado ya tiene antecedentes; falta comparación ejecutada |
| Checking Security Properties of Cloud Service REST APIs, ICST 2020 [11] | PDF de los autores; reglas y checkers | Reglas de namespace de usuario, jerarquía, efectos tras fallos y recursos eliminados | Lectura ajena y efectos de operaciones fallidas no constituyen por sí solos novedad |
| AFLNet, ICST 2020 [10] | PDF del autor; diseño y ejemplos de protocolo | Mutación de secuencias y guía por estados derivados de respuestas | La mutación de secuencias tampoco se presenta como invento del proyecto |
| RESTTESTGEN, STVR 2022 [12] | Preprint del autor y página de publicación | Escenarios nominales/de error y oráculos sobre una API descrita por OpenAPI | Las tareas válidas y los oráculos tienen antecedentes; aquí se estudia su combinación concreta |
| Mass assignment, ICSE 2023 [13] | Abstract de arXiv y registro institucional | Secuencias de ataque y oráculo específico de vulnerabilidad | Revisar el texto completo antes de discutir diferencias detalladas |
| Enabledness-based Testing of Object Protocols, TOSEM 2021 [14] | Resumen de los autores publicado en JAIIO 2022 | Guía de pruebas mediante criterios de cobertura de EPAs extendidas | Distinguir la proyección usada aquí de los métodos completos; falta lectura del artículo extenso |

Las fuentes [9]–[11] se consultaron en sus PDFs primarios; [12] tiene un manuscrito
de autor con fechas de plantilla antiguas, por lo que año/DOI se toman del registro
editorial de 2022. No se copian números de rendimiento de otros artículos como
comparaciones con nuestras campañas.

## Fuentes y verificaciones

- [9] https://patricegodefroid.github.io/public_psfiles/icse2019.pdf
- [10] https://mboehme.github.io/paper/ICST20.AFLNet.pdf
- [11] https://patricegodefroid.github.io/public_psfiles/icst2020.pdf
- [12] https://michelepasqua.github.io/publications/pdfs/STVR22.pdf y
  https://profs.scienze.univr.it/~ceccato/papers/2022/stvr2022.html
- [13] https://arxiv.org/abs/2301.01261 y https://iris.univr.it/handle/11562/1107429
- [14] DOI https://doi.org/10.1145/3415153; resumen de los autores:
  https://revistas.unlp.edu.ar/JAIIO/article/download/18418/18081/82202
- [3]–[4] metadatos y relación con Contractor.NET verificados en
  https://lafhis.dc.uba.ar/contractor/contractor.net-web/. El enlace de PDF de
  2013 devuelve 404; no se marca el artículo completo como leído en esta ronda.
- [5]–[7] títulos, autores y abstracts de arXiv verificados. Se mantienen como
  contexto de agentes; no se comparan sus garantías ni se replican sus números.

El editor de [14] respondió 403 y la fuente institucional disponible contiene
solamente un resumen de una página. El artículo completo sigue pendiente.
Behaviour abstraction adequacy criteria for API call protocol testing,
DOI 10.1002/stvr.1593, también requiere lectura completa; se identificó como
antecedente adicional sin atribuirle resultados no consultados.

## Posición adoptada

El aporte que intentamos sostener es un estudio comparativo reproducible de
pruebas de autorización e historia, con controles que separan biblioteca inicial,
forma de perturbación y feedback observacional. La implementación publica
contrato, oráculo, errores deliberados, testigos y costos de todas las etapas,
y conecta las pruebas con discrepancias y mitigaciones de un backend existente.

La literatura muestra solapamientos sustanciales. Se retiraría cualquier reclamo
de ser el primer fuzzer con estado, el primero que comprueba autorización, o una
refutación general de EPAs. La originalidad restante debe juzgarse sobre el
diseño experimental, los artefactos y sus hallazgos, y sigue abierta a revisión.

## Estado de las comparaciones externas

RESTler oficial sí fue ejecutado en el piloto v0.7: dos estrategias, checkers
nativos desactivados y alcance limitado de flujos válidos. Los resultados y límites
están en paper/restler-pilot-results.md. AFLNet, RESTTESTGEN y EvoMaster siguen sin
comparación ejecutada. seed_extend es una referencia interna, no un sustituto de
estas herramientas. Ninguno de estos experimentos agrega un servicio independiente.

## Revisión adicional del 15 de octubre de 2026

[15] EnFuzz estudia combinar estrategias diversas y sincronizar entradas
interesantes. Consultamos el artículo de USENIX, especialmente las secciones 3–4.
Nuestra combinación v0.8 comparte presupuesto entre dos generadores internos; no
implementa la sincronización de semillas ni reproduce EnFuzz. Combinar motores no
es una contribución novedosa por sí sola.

[16] EcoFuzz formula la asignación de energía como exploración y explotación y
propone un planificador adaptativo. Consultamos la introducción y la configuración
de evaluación del artículo de USENIX. En v0.8 elegimos una distribución fija y
observable por cantidad de solicitudes. No la llamamos bandit ni EcoFuzz.

[17] Klees y colaboradores estudian errores de evaluación de fuzzers y proponen
criterios de comparación experimental. Consultamos la ficha del autor y la introducción del preprint,
incluyendo sus advertencias sobre presupuesto, semillas y conteo de defectos. Incorporamos presupuesto comparable, múltiples semillas y
publicación de todos los resultados. Las semillas repetidas no resuelven la falta
de diversidad independiente de defectos y sistemas.

Esta es una revisión dirigida, no sistemática; los rendimientos de estos trabajos
no se comparan numéricamente con nuestras campañas. El protocolo v0.8 declara de
antemano qué sería una mejora amplia y qué se informará como una compensación.

[18] Barabanov y colaboradores describen análisis de especificaciones OpenAPI
para identificar posibles casos IDOR/BOLA. Se verificaron metadatos y abstract;
la lectura completa sigue pendiente. Es otro antecedente que impide presentar
como nueva la mera generación de pruebas de autorización desde una especificación.
No se atribuyen precisión ni resultados comparativos no replicados.

Se evaluó la elegibilidad de OWASP crAPI como futura implementación independiente;
ver docs/independent-backend-candidate.md. Es un candidato documentado y versionado,
no un tercer sistema ya evaluado ni un conjunto de defectos desconocidos.
