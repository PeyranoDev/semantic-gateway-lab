# Próximo trabajo después de v0.6

## Completado

- Benchmarks de documentos v0.1/v0.2, con ablaciones y datos históricos conservados.
- Caso Aoristo v0.3 y extracción pública original/corregida v0.4.
- Segundo negocio de salones v0.5, con HTTP/SQL, rollback y concurrencia específicos.
- Evaluación de componentes v0.6: biblioteca inicial, mutación, extensión y feedback,
  semillas frescas, contrastes por semilla, revalidación y figuras reproducibles.
- Revisión bibliográfica focalizada y reorganización del manuscrito alrededor
  de una contribución empírica delimitada. Ver paper/claims-and-evidence.md.

## Prioridades para fortalecer el paper

1. **Comparación externa ejecutada.** Implementar el protocolo preparado en
   external-baseline-protocol.md usando un commit de RESTler fijado, la misma
   API/oráculo y costos comparables. seed_extend es sólo un baseline interno.
2. **Independencia.** Evaluar un backend de otro autor con licencia revisada y
   política de negocio definida antes de medir; o conseguir revisión externa
   del contrato/oráculo. Los servicios actuales siguen siendo del mismo proyecto.
3. **Literatura cercana completa.** Obtener y leer el artículo completo de
   Enabledness-based Testing of Object Protocols y los antecedentes de criterios
   de cobertura con EPA. La auditoría distingue fuentes completas y resúmenes.
4. **Objetivo editorial.** Seleccionar tipo de artículo/sede y ajustar alcance,
   extensión, referencias y figuras. La contribución restante debe evaluarse
   contra esos antecedentes; no se declara novedad de fuzzing con estado.

## Preguntas secundarias, con protocolos propios

- Exploración con presupuesto completo, sin parada en primera falla, para comparar
  cobertura y fragmentación de corpus de forma interpretable.
- Estrategia híbrida que combine exploración amplia y tareas con historia;
  no ajustar ni anunciar un ganador usando las matrices ya observadas.
- Aprobaciones ligadas a generación/versionado, cambios de política y revocación.
- Esquema Alembic real y carreras adicionales del backend original. Las pruebas
  concretas de rollback/cancelación no demuestran durabilidad o seguridad general.
- Integración de un agente y transporte MCP como evaluación separada, si el
  objetivo editorial requiere ese alcance. Actualmente no se mide ninguno.

La revisión del PR privado de mitigación de Aoristo y cualquier despliegue
productivo son decisiones de mantenimiento separadas del cierre científico.
