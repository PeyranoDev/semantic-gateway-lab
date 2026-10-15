# Próximo trabajo después de v0.8

## Completado

- Benchmarks de documentos v0.1/v0.2, con ablaciones y datos históricos conservados.
- Caso Aoristo v0.3 y extracción pública original/corregida v0.4.
- Segundo negocio de salones v0.5, con HTTP/SQL, rollback y concurrencia específicos.
- Evaluación de componentes v0.6: biblioteca inicial, mutación, extensión y feedback,
  semillas frescas, contrastes por semilla, revalidación y figuras reproducibles.
- Revisión bibliográfica focalizada y reorganización del manuscrito alrededor
  de una contribución empírica delimitada. Ver paper/claims-and-evidence.md.

- Evaluación v0.8: 900 campañas, dos presupuestos, resultado mixto del portfolio,
  892 replays, 810 pares de recuperación idénticos y archivo RESTler preservado.

## Prioridades para fortalecer el paper

1. **Comparación externa principal.** El piloto oficial v0.7 ya se ejecutó:
   60 campañas, 44.808 llamadas y 31 testigos revalidados. Ver
   paper/restler-pilot-results.md. Validar ahora una configuración con dependencias
   de workflows y más estrategias, con alcance del ciclo legítimo comprobado,
   antes de congelar una matriz mayor. seed_extend sigue siendo sólo interno.
2. **Independencia.** OWASP crAPI quedó identificado y versionado como candidato;
   ver docs/independent-backend-candidate.md. Falta construirlo, validar fixtures,
   fijar imágenes/dependencias y revisar su contrato/oráculo antes de medir.
   Sus desafíos son públicos: sería independencia de implementación, no de defectos
   desconocidos. Los sistemas efectivamente medidos siguen siendo del proyecto.
3. **Literatura cercana completa.** Obtener y leer el artículo completo de
   Enabledness-based Testing of Object Protocols y los antecedentes de criterios
   de cobertura con EPA. La auditoría distingue fuentes completas y resúmenes.
4. **Objetivo editorial.** Seleccionar tipo de artículo/sede y ajustar alcance,
   extensión, referencias y figuras. La contribución restante debe evaluarse
   contra esos antecedentes; no se declara novedad de fuzzing con estado.

## Preguntas secundarias, con protocolos propios

- Exploración con presupuesto completo, sin parada en primera falla, para comparar
  cobertura y fragmentación de corpus de forma interpretable.
- La combinación fija de exploración y tareas con historia tiene protocolo v0.8.
  Cualquier cambio posterior de proporciones debe llevar nuevo protocolo y datos;
  no seleccionar retrospectivamente una proporción ganadora.
- Aprobaciones ligadas a generación/versionado, cambios de política y revocación.
- Esquema Alembic real y carreras adicionales del backend original. Las pruebas
  concretas de rollback/cancelación no demuestran durabilidad o seguridad general.
- Integración de un agente y transporte MCP como evaluación separada, si el
  objetivo editorial requiere ese alcance. Actualmente no se mide ninguno.

La revisión del PR privado de mitigación de Aoristo y cualquier despliegue
productivo son decisiones de mantenimiento separadas del cierre científico.
