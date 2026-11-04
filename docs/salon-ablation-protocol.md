# v0.6 — separar conocimiento inicial, perturbación y feedback

Protocolo fijado antes de ejecutar esta matriz. Es un seguimiento diseñado después
de observar v0.5: conserva el backend, los cuatro mutantes y el contrato, y usa
30 semillas nuevas, 600–629. No es preregistro externo, evaluación ciega ni un
conjunto de defectos reservado.

## Preguntas

1. ¿Cuánto cambia la detección al mutar una biblioteca de tareas válidas en lugar
   de programas aleatorios de las mismas longitudes?
2. ¿La mutación del programa completo aporta frente a completar una tarea válida
   y solamente agregar acciones aleatorias al final?
3. ¿Qué efecto tiene ejecutar tareas válidas como warmup, cobrando sus llamadas,
   si luego se reinicia el estado y no se reutiliza esa biblioteca?
4. ¿Se reproduce el contraste de feedback básico/enriquecido en semillas nuevas?

## Tratamientos

| Motor | Biblioteca inicial | Generación después del warmup |
|---|---|---|
| random | ninguna | programas aleatorios independientes |
| random_bootstrap | ocho tareas válidas | programas aleatorios independientes |
| seed_replay | ocho tareas válidas | repetir una tarea válida sin cambios |
| seed_extend | ocho tareas válidas | tarea válida completa + sufijo aleatorio |
| mutation_unseeded | ocho programas aleatorios con longitudes iguales | seis mutaciones genéricas |
| sequence_uniform | ocho tareas válidas | seis mutaciones genéricas, sin corpus |
| sequence_enabled | ocho tareas válidas | mismas mutaciones, corpus básico |
| sequence_enriched | ocho tareas válidas | mismas mutaciones, corpus enriquecido |

La biblioteca aleatoria se crea una vez por semilla, usando un RNG independiente
y un identificador fijo. No se filtran programas por éxito ni por resultados del
oráculo. Se publican los programas de las 30 bibliotecas y sus hashes.
Las bibliotecas válidas y aleatorias tienen longitudes 3,4,3,2,3,4,3,2.

Todos los motores salvo random ejecutan primero los ocho programas de su
biblioteca. Estas llamadas consumen presupuesto. Cada episodio reinicia la
fixture y hace commits SQL normales: el warmup no conserva estado entre episodios.
Por ello random_bootstrap mide el warmup cobrado y descartado, no todos los usos
posibles del conocimiento de tareas. seed_replay es un control de perturbación:
las tareas legítimas ya se verificaron y su repetición desde fixture limpia no
está diseñada para generar ataques.

seed_extend elige una tarea y agrega entre una y las acciones que permita la
profundidad ocho, con operaciones, actores y recursos uniformes. No cambia el
interior de la tarea. No se presenta como RESTler, AFLNet ni una reproducción de
ninguno de esos sistemas. Es una referencia interna para un generador simple
que ya dispone de tareas válidas.

Los cuatro motores originales conservan exactamente su comportamiento para
una semilla y propiedad iguales. Una prueba compara todos sus campos semánticos
contra v0.5. Los seis operadores, el corpus 64 y la elección guiada del 80% se
mantienen. Presupuesto 120 llamadas y profundidad ocho para todos.

## Matriz y controles

4 mutantes × 8 motores × 30 semillas = 960 campañas con una propiedad objetivo
por mutante. fixed × 8 motores × 30 semillas = 240 controles. Total 1200.

El control fixed usa ANY: verifica todas las propiedades del oráculo en una
única campaña por motor/semilla, evitando repetir cuatro streams idénticos
bajo distintos objetivos. Se exige que no aparezca ninguna discrepancia.
Se mantienen fuera del presupuesto las comprobaciones explícitas de tareas y
testigos conocidos. Se miden aparte autenticación, controles, minimización,
replay posterior y revalidación de los dos testigos por campaña detectada.

## Contrastes fijados

Los seis pares están declarados en analysis.py antes de la matriz:

1. mutation_unseeded → sequence_uniform: biblioteca válida bajo mutación igual.
2. seed_extend → sequence_uniform: perturbación interna frente a sufijo únicamente.
3. seed_replay → sequence_uniform: control de perturbación, no competidor externo.
4. random → random_bootstrap: warmup cobrado que después no se reutiliza.
5. random_bootstrap → sequence_uniform: reutilización de tareas más mutación.
6. sequence_enabled → sequence_enriched: réplica del cambio de proyección.

No se atribuye el contraste 5 solamente a los operadores: también cambia la
reutilización de tareas. El contraste 1 cambia la calidad de la biblioteca tanto
en warmup como en generación, manteniendo sus longitudes y el controlador.
El contraste 2 cambia el mecanismo de perturbación y sus distribuciones;
no es una comparación con idéntica distribución de todos los programas.

## Análisis fijado y límites

Cada ausencia de detección queda censurada en 120 llamadas. Se informan tasa
de detección, Wilson descriptivo y media del costo con límite. Para cada par y
propiedad se calcula derecha menos izquierda y se remuestrean 30 pares de
semillas, con reemplazo, 5000 veces. Los intervalos percentiles 2,5–97,5% describen
variación por semilla dentro de este backend; no incertidumbre entre empresas.
No se aplican pruebas de significancia ni se seleccionan solamente pares favorables.
Los contrastes son 24 por las cuatro propiedades y se publican todos.

El esquema usa las mismas etiquetas de semilla para bloquear tratamientos;
los motores consumen RNG de forma distinta y no generan necesariamente los
mismos argumentos a cada índice de llamada. No se suman las fases históricas
como una sola muestra. No se comparan coberturas finales de campañas que se
detienen en momentos diferentes. Se registra si una detección ocurrió en warmup.

Los testigos originales y minimizados se reejecutan exactamente desde fixtures
limpias. El manifiesto identifica fuentes, contrato, configuración y datos por
SHA-256. Las correcciones de infraestructura/contrato, si fueran necesarias,
se documentan y exigen repetir la matriz sin modificar sus parámetros.

Esta evaluación no implementa RESTler, no prueba seguridad, no evalúa LLM/MCP,
ni aporta sistemas de otro autor. La literatura y la evaluación externa siguen
siendo necesarias para cualquier afirmación de novedad o superioridad externa.
