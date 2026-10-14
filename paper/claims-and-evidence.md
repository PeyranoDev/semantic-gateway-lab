# Afirmaciones y evidencia que necesita el paper

| Afirmación delimitada | Evidencia disponible | Límite |
|---|---|---|
| Nuestra proyección global de herramientas pierde distinciones de autorización | Contraejemplo de documentos y test HTTP de confirmación en salones | No refuta los métodos completos de EPA ni es un nuevo teorema formal |
| Mutar tareas válidas puede facilitar fallas con historia en estas condiciones | v0.2, cancelación en Aoristo v0.3 y salones v0.5; ablation v0.6 separa componentes | Biblioteca y reglas diseñadas dentro del proyecto; falta referencia externa |
| Feedback más rico tiene costos y beneficios dependientes de la propiedad | Comparaciones de proyección con mutador/planificador iguales en v0.2, v0.3 y v0.5 | No concluir eficiencia general ni cobertura total desde campañas con parada temprana |
| Errores HTTP pueden acompañar escrituras de negocio | Testigos de invitaciones en Aoristo y parche con rollback | Hecho del caso; tiene antecedentes en checkers de efectos tras fallos |
| El caso público conserva las observaciones históricas seleccionadas | 150 replays exactos y manifiesto de extracción | Equivalencia finita de observaciones; no equivalencia del backend completo |
| La mitigación corrige los casos revisados | Controles, campañas acotadas, rollback y concurrencia específicos | No demostrar seguridad general o compatibilidad de despliegue productivo |

## Unidad experimental

Las semillas varían la búsqueda dentro de un sistema. Los testigos son resultados
de campañas, no sistemas adicionales. Los testigos original y minimizado no
duplican la cantidad de defectos. Las dos versiones corregidas de Aoristo son
ensambles relacionados, y TurnoSalon fue creado por este mismo proyecto.

Las fases históricas se describen separadamente porque cambian dominios,
tratamientos y presupuestos. Las nuevas semillas de v0.6 son frescas respecto
de v0.5, pero reutilizan el backend y errores revisados. No se las llama defectos
reservados ni una prueba confirmatoria independiente.

## Afirmaciones que la evidencia actual no autoriza

- Superioridad frente a RESTler, AFLNet u otros fuzzers no ejecutados.
- Novedad de generar secuencias, mutarlas o comprobar autorización con un oráculo.
- Seguridad formal o ausencia universal de fallas en una versión corregida.
- Generalización independiente a empresas o implementaciones de otros autores.
- Evaluación de comportamiento de LLMs, prompt injection o transporte MCP.

## Cierre antes de enviar

Comparación externa ejecutada y/o alcance de artículo de artefacto/estudio
exploratorio acordado; lectura completa de antecedentes de pruebas con EPA;
revisión externa de políticas/oráculo; narrativa y tablas sin duplicación de
unidades; figuras reproducibles; referencias y formato de la sede seleccionada.
