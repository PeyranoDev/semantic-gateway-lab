# Afirmaciones y evidencia que necesita el paper

Niveles de evidencia: **validación** (el pipeline reproduce lo registrado),
**exploratoria** (defectos y diseños que informaron el método) y **prospectiva**
(predicciones congeladas antes de ejecutar).

| Afirmación delimitada | Nivel | Evidencia | Límite |
|---|---|---|---|
| Las tablas de transición reproducen el backend medido | Validación | 2.740 campañas v0.5/v0.6/v0.8 idénticas en 19 campos; control negativo 19/20; 8.750 transiciones por caminos reales | Supone dependencia sólo del estado observable; muestra de 50 estados |
| La enumeración de mutaciones es exacta | Validación | Test que recorre todos los caminos de elección del `Mutator` real | Sólo el mutador de TurnoSalon |
| El servicio corregido no viola el oráculo en programas de hasta 8 acciones | Validación | Tabla completa de 723 estados y 126.525 transiciones sin violación | Dominio de 175 acciones, sin creación de recursos, propiedades del oráculo |
| Tareas válidas frente a banco aleatorio, con igual mutador: +43 a +76 puntos en historia, −45 en lectura | Exploratoria | Sustituto con 1.000 semillas; contrastes planificados con McNemar exacto y Holm | Un servicio; defectos revisados |
| La guía por corpus rinde menos que la mutación uniforme en defectos con historia | Exploratoria | −12 a −33 puntos a 120 llamadas; persiste a 480 | El contraste cambia selección, desalojo y planificador a la vez |
| La clave enriquecida sólo ayuda en sobreventa | Exploratoria | +20,7 ± 3,6 puntos; las otras tres incluyen cero | Un servicio |
| La profundidad es un proxy; el alcance por episodio explica `wrong_recipient` | Exploratoria | Monte Carlo de 10.000 episodios por defecto en el benchmark de documentos | n = 10 no confirma la dirección presupuestaria |
| Predicciones desde la especificación ordenan generadores en defectos nuevos | Prospectiva | 26/26 pares (brecha ≥ 0,1); 3 mutantes equivalentes con 0/270 detecciones | La regla de profundidad también acierta 15/15; el alcance agrega 11 pares con extensión |
| Calibración por celda compatible con muestreo | Prospectiva + diagnóstico | 3/20 celdas informativas con p < 0,05; grafos especificación/implementación idénticos; 3.000–9.000 semillas reproducen lo congelado | Diagnóstico post hoc |
| Errores HTTP pueden acompañar escrituras de negocio | Exploratoria | Testigos de invitaciones en Aoristo y parche con rollback | Hecho del caso |
| Se ejecutó un generador externo oficial | Exploratoria | v0.7: RESTler, 60 campañas, 31 trazas revalidadas | Checkers nativos desactivados; sin alcance del reembolso |

## Unidad experimental

Las semillas varían la búsqueda dentro de un sistema. Los mutantes sistemáticos son
defectos nuevos del mismo servicio, no sistemas independientes. Las celdas del
sustituto usan semillas frescas y el código de campaña sin cambios; describen
variación de búsqueda, no variación entre sistemas.

## Afirmaciones que la evidencia actual no autoriza

- Superioridad general frente a RESTler, EvoMaster u otros fuzzers no comparados.
- Novedad de generar secuencias, mutarlas o comprobar autorización con un oráculo.
- Que el alcance supere a la profundidad prospectivamente en la comparación
  aleatorio/mutación: ambos acertaron los mismos pares.
- Que la guía por corpus sea inferior en general: sólo en esta configuración y servicio.
- Generalización a implementaciones de otros autores o a dominios no finitos.
- Seguridad formal fuera del dominio y la profundidad acotados.

## Cierre antes de enviar

Leer los textos completos de [19]–[26]; medir un servicio independiente (crAPI);
comparar con los oráculos de política de acceso de EvoMaster [19]; seleccionar sede
y formato.
