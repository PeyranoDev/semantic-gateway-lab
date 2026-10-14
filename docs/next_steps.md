# Próximo ciclo de investigación

## Primera lectura

1. Ejecutar tests, demo y análisis acotado siguiendo README.
2. Leer `paper/results.md` junto a los CSV y manifiestos.
3. Reproducir una traza de destinatario incorrecto y otra de aprobación.
4. Revisar el caso de aprobación reutilizada: el test dirigido detecta el mutante,
   pero su descubrimiento aleatorio requiere una secuencia considerablemente más rara.

## Prioridad científica

No agregar otra capa de seguridad todavía. Primero decidir si el paper estudia
la pérdida de información de las abstracciones o la eficiencia del algoritmo de
exploración. Este laboratorio permite investigar ambas, pero sus resultados no
justifican afirmar que más predicados siempre mejoran el fuzzing.

## Siguiente experimento propuesto (no implementado ni medido)

Mantener las tres estrategias entregadas como baseline congelado. Incorporar,
en una nueva versión, mutaciones de secuencias y argumentos que conserven parte
de las relaciones necesarias para avanzar en un flujo. Aplicar el mismo motor
de mutación a `enabled` y `enriched`, para no confundir el efecto de abstracción
con mejores parámetros. Aislar el tamaño del corpus y la longitud de replay.

Agregar ablaciones por familia de predicados: destinatario, propietario,
departamento y aprobación. Comparar cobertura con un presupuesto fijo completo,
además del modo actual de primera falla. Separar cobertura de rapidez de detección.
Agregar una implementación independiente del servicio antes de generalizar.

## Fase con agentes reales

Implementar un adaptador que traduzca llamadas estructuradas de uno o dos modelos
en Action; la autoridad seguirá proveniendo de sesiones autenticadas. Medir tareas
legítimas, tareas adversariales, costos y llamadas por separado del fuzzing offline.
Agregar transporte MCP real y versionarlo antes de afirmar compatibilidad.

No exponer razonamientos internos como requisito de auditoría: conservar acciones,
parámetros, fuentes, identidades, decisiones y efectos observables. Definir un
modelo de amenazas concreto para datos externos y aprobaciones humanas.

## Antes de enviar el paper

Leer completos los trabajos cercanos citados; comprobar la novedad específica.
Auditar independientemente el oráculo. Usar defectos reservados diseñados por otra
persona y más de un backend. Congelar semillas, presupuestos y análisis antes del
experimento siguiente. Publicar negativos, intervalos, limitaciones y artefactos.
Solicitar revisión de alguien con experiencia en métodos formales para cualquier
afirmación de preservación de propiedades o prueba de seguridad.
