# Próxima comparación externa — diseño preparado, ejecución pendiente

## Objetivo

Comparar un generador de secuencias de este laboratorio con la implementación
oficial de RESTler. No se atribuyen nuestros motores de sufijos o mutación a
RESTler, ni se afirma haber ejecutado esa herramienta.

El próximo paso técnico es fijar un commit de microsoft/restler-fuzzer, construir
su herramienta y validar compilación de OpenAPI, login y alcance de operaciones
antes de congelar el protocolo medido. Este entorno local no dispone de dotnet
ni docker; eso no impide preparar el caso en un runner dedicado, pero esa
instalación y sus resultados siguen pendientes.

## Condiciones de una comparación interpretable

1. Ambos tratamientos deben usar TCP, la misma API, versión, fixture SQL y
   biblioteca de identidades/recursos. No comparar latencia TCP de un sistema
   con latencia ASGI del otro.
2. Publicar OpenAPI, diccionario, anotaciones de dependencias, gramática generada,
   configuración y fuente exacta. No añadir testigos defectuosos como ejemplos.
3. Dar a ambos los identificadores y credenciales sintéticos que necesita el
   contrato. Identificar por separado esfuerzo manual y conocimiento añadido
   por diccionarios, anotaciones o tareas válidas.
4. Registrar cada solicitud con estado SQL antes/después y evaluar el mismo
   contrato del negocio. No comparar conteos de HTTP 500 con discrepancias del
   oráculo como si fueran el mismo resultado.
5. Aplicar el presupuesto a todas las solicitudes de búsqueda, replays y
   checkers adicionales. Contabilizar login, reset, limpieza y setup aparte.
6. Definir y comprobar el aislamiento entre secuencias antes de medir. No dejar
   que un tratamiento acumule recursos y el otro se reinicie sin documentarlo.
7. Preservar testigos y errores de infraestructura. Excluir una corrida sólo por
   un criterio fijado antes de observar sus resultados.
8. Informar cobertura de rutas, respuestas y reglas de negocio por separado.
   Los resultados fuera del dominio normalizable del oráculo requieren su
   propia clasificación y no se descartan para favorecer un tratamiento.

## Cuidado con los checkers de usuario

En TurnoSalon un empleado puede operar sobre reservas de otros clientes de su
sucursal. Una regla que interprete cualquier acceso entre dos usuarios como
prohibido puede señalar tareas autorizadas por nuestro contrato. Por eso se
deben conservar los reportes nativos de RESTler y separar su interpretación de
la del oráculo de sucursal/rol. La comparación debe informar ambos conjuntos.

## Puertas de validación antes de la matriz

- Smoke de tareas legítimas y autenticación de cliente/empleado por TCP.
- Reproducción de los cuatro testigos conocidos con observación SQL, fuera de
  búsqueda. Esa reproducción valida la instrumentación, no la eficacia de RESTler.
- Prueba de reset, conteo de solicitudes y parada en el límite.
- Revisión de que los parámetros de generación no contienen etiquetas de
  mutantes ni secuencias preparadas para explotar una falla concreta.
- Congelamiento de presupuesto, semillas/método de aleatoriedad, profundidad,
  número de repeticiones, contrasts y exclusiones antes de la ejecución completa.

La evaluación independiente exige además un servicio público de otro autor y
revisión externa de sus políticas. Hasta que se ejecute, no se agrega a tablas
de resultados ni se contabiliza como generalización demostrada.
