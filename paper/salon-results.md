# TurnoSalon v0.5 — segundo dominio ejecutable

Se creó un backend de reservas para una red de salones: clientes, empleados,
sucursales, turnos de capacidad limitada, cobros con crédito simulado,
cancelaciones y reintegros. Usa FastAPI, sesiones firmadas y SQLite con
conexiones independientes, transacciones BEGIN IMMEDIATE y commits reales.

**Resultado:** el procedimiento ejecuta este segundo negocio y detecta las
cuatro fallas deliberadas en algunas semillas. La versión corregida no presenta
discrepancias observadas en su matriz. Los resultados conservan fallas de búsqueda
y no muestran una ventaja universal del feedback enriquecido.

Es un backend nuevo creado dentro del proyecto. Amplía la transferencia técnica
a otro contrato y persistencia; no equivale a un segundo sistema productivo
independiente ni a descubrimiento de vulnerabilidades desconocidas.

## Diseño y controles

Se mantuvieron el generador de v0.3 byte por byte, el algoritmo de campaña
excepto su descripción del módulo, los seis operadores, corpus 64, profundidad 8,
presupuesto de 120 llamadas y cuatro motores. Se implementaron otro dominio,
ocho tareas válidas (24 llamadas), observación y un oráculo separado del backend.

El protocolo y la configuración quedaron en el commit
[92ccf1f](https://github.com/PeyranoDev/semantic-gateway-lab/commit/92ccf1fa331801668336db1dd406178d8569d7cc)
antes de ejecutar la matriz. No se ajustó el generador tras observar resultados.
Una prueba de determinismo usa dos campañas pequeñas de lectura con semilla
9123; no se utilizó para seleccionar las semillas 400–419 ni para ajustar motores.
Este congelamiento operativo no es preregistro externo ni evaluación ciega.

Cuatro mutantes aislados omiten un control cada uno. En cada variante pasan los
ocho programas legítimos y cuatro comprobaciones explícitas de testigos conocidos:
60 comprobaciones en total. Esos testigos no se incorporan al corpus inicial.
Los programas legítimos se mutan para producir operaciones repetidas, omitidas,
reordenadas o con actores/recursos diferentes.

640 campañas: 320 sobre mutantes (una propiedad correspondiente por variante)
y 320 sobre fixed (las cuatro propiedades). 20 semillas por motor/propiedad.
Sólo el par sequence_enabled/sequence_enriched aísla la proyección de feedback.
random también cambia la inicialización y la reutilización de programas.

## Resultados

Cada celda indica **detecciones/20 (media de llamadas con límite de 120)**.
Los casos no detectados consumen 120 llamadas y permanecen en la media.

| Falla deliberada | Random | Mutación sin corpus | Corpus básico | Corpus enriquecido |
|---|---:|---:|---:|---:|
| Lectura de reservas ajenas | 19/20 (29.9) | 6/20 (102.5) | 8/20 (102.5) | 8/20 (103.3) |
| Sobreventa del turno | 2/20 (112.0) | 16/20 (69.8) | 7/20 (112.8) | 10/20 (99.6) |
| Confirmación sin pago | 0/20 (120.0) | 13/20 (87.0) | 13/20 (86.7) | 11/20 (92.4) |
| Reintegro repetido | 0/20 (120.0) | 9/20 (88.8) | 6/20 (106.3) | 6/20 (110.2) |

Se detectan 134 de las 320 campañas con mutantes. Todos los testigos originales
y minimizados se reejecutan: **268 revalidaciones exactas** de respuesta y estado SQL.
Las secuencias minimizadas tienen 1 llamada para lectura ajena, 2 para cupo,
2 para confirmación sin pago y 5 para reintegro repetido. La minimización elimina
acciones; no reclama una búsqueda global de la secuencia más corta.

fixed completa **320 campañas y 38.400 llamadas de búsqueda** sin discrepancias
de decisión, efecto o salida, ni otros errores del oráculo. Las cuatro propiedades
reutilizan las mismas semillas/motores; los controles no son réplicas independientes.

La mutación de tareas válidas ayuda a alcanzar fallas con historia: reintegro
repetido 9/20 versus 0/20 para random, confirmación sin pago 13/20 versus 0/20,
sobreventa 16/20 versus 2/20. Random encuentra más lecturas ajenas, 19/20 versus
6/20. El par de feedback es mixto: enriquecido encuentra sobreventa en 10/20
versus 7/20, pero confirmación sin pago en 11/20 versus 13/20. En reintegro y
lectura empatan las tasas, con diferencias de esfuerzo. No se reclama
significancia estadística ni superioridad general; paired.json conserva las
comparaciones por semilla y summary.json incluye intervalos Wilson descriptivos.

## Costos y procedencia

| Variante | Búsqueda | Minimización | Replay tras minimizar | Revalidación | HTTP total |
|---|---:|---:|---:|---:|---:|
| confirm_unpaid | 7721 | 172 | 74 | 176 | 8181 |
| fixed | 38400 | 0 | 0 | 0 | 38438 |
| read_scope | 6764 | 132 | 41 | 147 | 7122 |
| refund_replay | 8504 | 764 | 105 | 224 | 9635 |
| slot_capacity | 7884 | 143 | 70 | 163 | 8298 |

El total incluye además 4 llamadas de autenticación y 34 llamadas de controles
por variante: **71,674 ejecuciones HTTP**. No incluye llamadas de
la suite de contratos ni del smoke TCP; sus costos se mantienen fuera de la matriz.
No se suman estas llamadas a estudios anteriores como si fueran una sola muestra.

Python 3.12.15; SQLite 3.45.1. Persistencia en archivo,
modo WAL y transacciones que serializan escritores. Campañas sobre HTTP ASGI
en proceso. El smoke TCP levanta el servidor y completa crear → reservar →
pagar → confirmar → cancelar → reintegrar con autenticación real por HTTP.

- [Ejecución medida](https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38617622189).
- [Código y comandos](../case_studies/salon/README.md).
- [Protocolo congelado](../docs/salon-protocol.md).
- [Matriz y testigos](../results/salon-v05/).
- SHA-256 de configuración: 47b02cd63c24184faf595cc99bf3b416bb0478f0d3c14bec150ee81e52b6aae5.
- SHA-256 del JSONL descomprimido: 2a96ad220fc8f5c63dd0fe6c647e43b2563a72a6d580cb47ebe3f693f7f0dedb.

El manifiesto publica hashes del backend, generador, campaña, oráculo,
adaptador, contrato, pruebas, configuración y dependencias pertinentes.
python -m scripts.analyze_salon verifica matriz, hashes, costos y oráculo offline.
python -m scripts.replay_salon reproduce todos los testigos archivados por HTTP.
Las ejecuciones siguientes de CI verifican la evidencia archivada; una matriz
nueva completa queda disponible mediante workflow_dispatch y no la sobrescribe.

## Pruebas de negocio y límites

Pasan **19 pruebas nuevas** y **113 pruebas de la suite completa** con dependencias.
Dos solicitudes simultáneas sobre el último cupo, con conexiones SQL independientes,
devuelven 200/409 y dejan ocupación uno. Dos reintegros simultáneos devuelven
200/409 y acreditan una sola vez. Un fallo inyectado después de escribir saldo,
marca de reintegro y movimiento devuelve 500 y revierte las tres escrituras.
También se comprueban alcance por cliente/sucursal, roles, sesiones manipuladas
o vencidas, creación y rechazo de campos de identidad/precio, y pagos repetidos.

Un test adicional construye dos estados con las mismas herramientas habilitadas
globalmente, pero distinta decisión para confirmar una reserva concreta. El
feedback enriquecido los distingue; eso demuestra información perdida por esta
proyección particular, no una mejora universal de búsqueda.

El dinero es simulado. El dominio de campañas usa cuatro reservas provisionadas;
la creación se verifica aparte. SQLite serializa escritores y no representa las
carreras de PostgreSQL. No se evalúan integración bancaria, LLM, MCP, tráfico
productivo, políticas externas, defectos reservados ni sistemas de otro autor.
Las 20 semillas varían la búsqueda, no el negocio ni la independencia del sistema.
