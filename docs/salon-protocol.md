# TurnoSalon v0.5 — protocolo congelado antes de la matriz

## Pregunta y alcance

¿Puede el procedimiento de v0.3 ejecutar tareas y encontrar violaciones de
autorización e historia en otro negocio y otra persistencia?

Este backend fue creado para el estudio. Tiene API FastAPI, autenticación,
repositorios SQL y transacciones SQLite con commits. Es un caso sintético
ejecutable, del mismo autor; no es otro producto en producción, una evaluación
independiente ni un conjunto de defectos reservado.

Dos salones, dos clientes, dos empleados, dos turnos de capacidad uno y cuatro
reservas draft. Importes enteros en centavos y saldos sintéticos de 5000.
No se conecta a bancos ni proveedores de pagos.

## Contrato

Clientes: reservas propias en su sucursal. Empleados: reservas de su sucursal.
Identidad, rol y sucursal se resuelven desde SQL usando una sesión firmada.

- Reservar requiere draft y cupo disponible; ocupa exactamente un lugar.
- Pagar requiere reserva sin pago; solamente su cliente puede pagar.
  Se debita el precio de SQL, nunca un importe elegido por el cliente.
- Confirmar requiere empleado y reserva totalmente pagada.
- Cancelar requiere reserved o confirmed; libera un lugar exactamente una vez.
- Reintegrar requiere empleado, reserva cancelada, pago y ausencia de reintegro.
  Se acredita una vez al cliente y se registra en el libro de movimientos.
- Denegaciones no modifican estado. Listados y lecturas conservan el alcance.

La creación de reservas está implementada y probada por HTTP, pero la matriz
usa cuatro identificadores de reservas provisionadas. Esta limitación evita
hacer pasar pruebas de un dominio finito por exploración general de recursos.

## Diseño fijado

Cuatro mutantes aislados: read_scope, slot_capacity, confirm_unpaid y refund_replay.
Cada uno omite un control. Control fixed: todos los controles habilitados.
Se comprueba primero que los ocho programas legítimos pasan en las cinco variantes.
Los cuatro testigos conocidos son comprobaciones aparte; no son semillas de búsqueda.

Motores: random, sequence_uniform, sequence_enabled, sequence_enriched.
El generador se copia byte por byte de v0.3. El algoritmo de campaña se conserva,
salvo la descripción del módulo y los imports relativos que resuelven el nuevo
dominio. No consulta etiquetas de mutantes. Reutiliza Corpus de fuzzlab.feedback.
Sólo cambian contrato, dominio finito, programas legítimos, observación y oráculo.

Mismas reglas de v0.3: seis operadores genéricos, corpus 64, profundidad 8,
120 llamadas por campaña, selección guiada 80%, programas válidos como bootstrap.
El par enabled/enriched cambia sólo la proyección del estado.
La referencia random también cambia bootstrap y selección; no aísla un único factor.

20 semillas 400–419, sin piloto de búsqueda ni selección de semillas por éxito:
4 mutantes × 4 motores × 20 semillas = 320 campañas de detección.
fixed × 4 propiedades × 4 motores × 20 semillas = 320 controles.
Total 640. Cada llamada de replay durante la búsqueda consume presupuesto.
Se detiene en la primera violación objetivo; errores de otro tipo terminan el episodio.

No hay ajuste del generador tras observar la matriz. Si falla infraestructura o
el contrato, se corrige, se registra el cambio y se vuelve a ejecutar toda la
matriz con el mismo archivo de configuración. Esto es congelamiento operativo,
no preregistro externo ni evaluación ciega.

## Evidencia

Manifest: hashes SHA-256 de backend, adaptador, oráculo, generador, campaña,
pruebas, protocolo y configuración; versiones de Python, SQLite y dependencias.
raw.jsonl.gz: todas las campañas y los testigos completos y minimizados.
checks.json: controles legítimos y testigos explícitos fuera de la búsqueda.

Los testigos originales y minimizados se reejecutan desde fixtures limpias,
comparando exactamente respuesta y estado. Se cuentan por separado autenticación,
controles, llamadas de campaña, minimización y revalidación.
Se publican detecciones por propiedad, esfuerzo medio limitado y censura.
Ningún fallo en fixed demuestra sólo ausencia de discrepancias observadas en
el presupuesto y fixture; no prueba seguridad.

Pruebas HTTP/SQL adicionales: creación y rechazo de campos de identidad/precio,
sesión manipulada o vencida, roles, pago/reintegro/cancelación repetidos,
rollback después de escrituras y dos solicitudes concurrentes con conexiones
independientes tanto para último cupo como para reintegro.

## Límites

SQLite BEGIN IMMEDIATE serializa escritores; no representa los bloqueos de
PostgreSQL. El transporte de campañas es ASGI en proceso, no TCP.
El dinero es crédito simulado. No se mide un agente LLM, MCP, despliegue productivo,
gestión de credenciales real, ni descubrimiento de vulnerabilidades desconocidas.
La transferencia muestra ejecución en otro dominio diseñado dentro del proyecto;
para generalización independiente se necesita un sistema y políticas externos.
