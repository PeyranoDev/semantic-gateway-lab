# Semantic Gateway Lab

Laboratorio reproducible para un nuevo paper de Ignacio Peyrano sobre pruebas
de autorización con estado en runtimes de herramientas para agentes.

**Pregunta:** ¿qué información pierde una abstracción que conserva únicamente
herramientas habilitadas, y qué costo tiene enriquecerla para guiar fuzzing?

Este proyecto toma como referencia el preprint
[From CRUD to Autonomous Agents](https://arxiv.org/abs/2604.25555)
y el [PoC original](https://github.com/PeyranoDev/semantic-gateway-poc).
La implementación experimental es nueva. El fuzzer ejecuta un servicio de
documentos y verifica sus efectos con un oráculo independiente; no recorre
un grafo que ya contiene una arista marcada como vulnerable.

## Empezar

Python **3.11 o superior**, sin dependencias externas, GPU ni claves de API.
En Windows podés sustituir `python` por `py -3` si corresponde.

```bash
python -m unittest discover -s tests -v
python -m fuzzlab demo
python -m fuzzlab analyze
python -m fuzzlab run --config configs/smoke.json --out results/local-smoke
```

La suite base contiene **102 pruebas sin dependencias externas**. Al instalar
las dependencias de los casos HTTP se habilitan otras 20 pruebas:
**122 pruebas en total**. La demo valida ocho defectos
deliberados y un flujo legítimo. `analyze` encuentra un contraejemplo a la
distinguibilidad de llamadas en la abstracción básica dentro de un submodelo
acotado. Los resultados de campañas anteriores no se sobrescriben.

```bash
python -m fuzzlab run --config configs/pilot.json --out results/local-pilot
python -m fuzzlab run --config configs/confirmatory.json --out results/local-confirmatory
```

El piloto tiene 270 ejecuciones: 10 semillas × 3 estrategias × 9 variantes.
La campaña adicional tiene 810: 30 semillas distintas × 3 × 9. Cada variante
contiene un solo defecto, o ninguno en el control `fixed`.

Las campañas terminan al encontrar la primera violación o agotar el presupuesto.
Las trazas son reproducibles; los tiempos dependen del equipo y su carga.

## Qué incluye

| Archivo o carpeta | Función |
|---|---|
| `fuzzlab/backend.py` | Servicio ejecutable con diez herramientas y controles por objeto |
| `fuzzlab/oracle.py` | Especificación independiente de decisiones, efectos, respuestas y auditoría |
| `fuzzlab/abstraction.py` | Abstracciones observacionales básica y enriquecida |
| `fuzzlab/fuzzer.py` | Campañas, replay y minimización de contraejemplos |
| `fuzzlab/analyze.py` | Búsqueda acotada de estados indistinguibles con decisiones diferentes |
| `tests/` | Regresiones, controles corregidos, flujos legítimos y reproducibilidad |
| `configs/` | Presupuestos, profundidad, variantes y semillas exactas |
| `results/pilot-final/` | Datos del piloto con manifiesto del código entregado |
| `results/confirmatory/` | Datos de la campaña adicional con semillas reservadas |
| `docs/protocol.md` | Protocolo, métricas, supuestos y límites |
| `docs/next_steps.md` | Próximo ciclo de investigación |
| `docs/provenance.md` | Referencias al preprint y al commit del PoC revisado |
| `paper/manuscript.md` | Borrador en inglés del nuevo enfoque |
| `paper/results.md` | Interpretación de resultados medidos |
| `.github/workflows/tests.yml` | CI para Python 3.11, 3.12 y 3.13 |

## Estrategias comparadas

| Estrategia | Selección y memoria |
|---|---|
| `random` | Herramientas uniformes; episodios desde el estado inicial |
| `enabled` | 80% de selección sobre herramientas habilitadas por ciclo de vida; corpus indexado por su conjunto |
| `enriched` | Mismo generador y selección de herramientas; corpus que conserva relaciones de propietario, departamento, destinatario, ACL y aprobación |

Las dos estrategias guiadas usan el mismo planificador de corpus y distribución
de argumentos. Cambia la clave de abstracción. La referencia aleatoria también
cambia la selección y no reutiliza prefijos, por lo que su comparación evalúa
el mecanismo guiado completo. Todas contabilizan llamadas de replay.

## Defectos deliberados

Lectura fuera de alcance, aceptación por destinatario incorrecto, aceptación
repetida que sobrescribe permisos, revocación por no propietario, aprobación
para otro recurso, reutilización de aprobación, eliminación sin aprobación y
omisión de auditoría de denegaciones. Son mutantes sintéticos, no vulnerabilidades
descubiertas en servicios de terceros.

Para reproducir una traza, elegí un archivo existente de `results/.../traces/`:

```bash
python scripts/unpack_results.py
python -m fuzzlab replay results/pilot-final/traces/cross_department_read-random-0.json
```

`minimal_trace` conserva la violación y es mínima bajo eliminación de una acción,
no necesariamente la secuencia más corta posible. Los tokens de las trazas usan
una clave pública de prueba: no son credenciales.

## Interpretar resultados

Los datos históricos están guardados como `raw.jsonl.gz`. El comando
`python scripts/unpack_results.py` verifica sus hashes, recupera los JSONL
originales y reconstruye las 722 trazas individuales. No requiere dependencias.
Cada carpeta de campaña contiene:

- `raw.jsonl`: una observación por ejecución, con presupuesto, cobertura,
  violación, trazas y testigo sobre snapshots del backend.
- `manifest.json`: configuración exacta, Python, plataforma y hashes del código.
- `summary.csv` y `summary.md`: resultados por variante y estrategia; intervalos
  Wilson sobre semillas y esfuerzo limitado por presupuesto.
- `traces/`: contraejemplos originales y minimizados.

Los casos no detectados permanecen en el análisis como observaciones censuradas.
Los números de estados son conteos observados, no porcentajes de cobertura total.
No encontrar violaciones en `fixed` no constituye una prueba universal.

## Alcance

El benchmark original usa memoria, reloj fijo y un dominio finito. Las
integraciones posteriores agregan persistencia SQL y HTTP. No se
implementa transporte MCP, OPA/Rego, un firewall semántico, modelos de lenguaje,
una interfaz de aprobación humana. La aprobación HMAC
es una simulación de autoridad externa; no acredita una integración humana real.
El proyecto estudia la frontera de ejecución de herramientas. La evaluación
con agentes reales es una fase posterior y deberá conservar su propia evidencia.

## Clonar desde GitHub

```bash
git clone https://github.com/PeyranoDev/semantic-gateway-lab.git
cd semantic-gateway-lab
python -m unittest discover -s tests -v
```

El ZIP anterior conserva un snapshot descargable y un bundle con su historial
local. El repositorio alojado es la versión de trabajo actual. Los manifiestos
de las campañas identifican exactamente el código que produjo sus resultados.
Las ejecuciones de CI se pueden consultar en la pestaña Actions del repositorio.

Licencia MIT para la implementación nueva. Ver `docs/provenance.md`.

## Segunda ronda: mutación de secuencias

La versión v0.2 agrega seis operadores de mutación, corpus acotado, ablaciones y
tres variantes sintéticas nuevas. La comparación incluye 1.080 ejecuciones,
1.147.407 llamadas y 829 testigos verificados. Ver [resultados v0.2](paper/sequence-results.md)
y [protocolo](docs/sequence-protocol.md). Los módulos de v0.1 se conservan intactos.

```bash
python scripts/unpack_sequence_results.py
python -m fuzzlab.sequence run --config configs/sequence-pilot.json --out results/local-sequence
python -m scripts.analyze_sequence
```

El motor de secuencias detecta reutilización de aprobación en 10/10 semillas por
tratamiento, frente a 0/10 para los motores anteriores en el mismo presupuesto.
También conserva resultados negativos: baja la detección de destinatario incorrecto.
La mejora combina semillas legítimas y mutación; no establece una ventaja universal
ni una garantía de seguridad. No se ejecutaron LLMs ni transporte MCP real.

## AoristoTech case study (v0.3)

The optional integration preserves the original FastAPI HTTP authorization pipeline and SQL repositories against disposable PostgreSQL. It contains a source lock, dependency lock, synthetic fixtures, an independent domain oracle, known regressions, and a four-engine exploratory comparison. The private application source is not bundled. See [the protocol](docs/aoristo-protocol.md) and [integration](integrations/aoristo/README.md). Portable artifact checks now include 88 tests; HTTP/PostgreSQL evidence is produced separately.

The completed PostgreSQL study contains 120 campaigns, 11 passing controls and 7 reproduced known regressions. All 75 discovered target witnesses and their minimized versions were reexecuted. See [AoristoTech results](paper/aoristo-results.md). Validate the published dataset with `python -m scripts.analyze_aoristo`.

## Public real-backend original/fixed case (v0.4)

The [AoristoTech source case](case_studies/aoristo/README.md) includes 62 verbatim real backend modules plus explicitly documented bootstrap/registry adaptations. Its 11-module patch also applies to the full application. Both fixed assemblies pass 21 checks and 120 campaigns (14,400 calls each); the original subset reproduces all 150 historical witnesses. See [mitigation evidence](paper/mitigation-results.md). Portable artifact tests now total 94. Validate with `python -m scripts.analyze_aoristo_case`.

## Segundo dominio: reservas de salones (v0.5)

[TurnoSalon](case_studies/salon/README.md) es un backend nuevo del experimento
con FastAPI, sesiones firmadas y transacciones SQLite. Incluye clientes,
empleados, reservas por sucursal, cupos, cobros con crédito simulado,
cancelaciones y reintegros. No es una aplicación en producción ni una
evaluación independiente.

Se reutilizan el generador y los cuatro motores de v0.3 con un nuevo contrato
y oráculo. El [protocolo](docs/salon-protocol.md) fija 640 campañas:
320 sobre cuatro mutantes aislados y 320 controles corregidos.

    python -m pip install -r backends/salon/requirements.lock
    python -m unittest discover -s tests -p 'test_salon.py' -v
    python -m scripts.salon_http_smoke
    python -m integrations.salon.run --out results/local-salon
    python -m scripts.analyze_salon

La prueba por TCP levanta y termina un servidor local automáticamente.
Las pruebas SQL comprueban rollback y solicitudes simultáneas para último
cupo y reintegro. Las campañas usan HTTP ASGI en proceso; la creación de
reservas se prueba aparte del dominio finito de búsqueda.

[Resultados e interpretación](paper/salon-results.md) ·
[Datos archivados](results/salon-v05/summary.md).

## Separación de componentes y revisión del paper (v0.6)

La evaluación prospectiva fija ocho tratamientos y 30 semillas nuevas. Las
1.200 campañas separan biblioteca válida/aleatoria, repetición, extensión,
mutación y feedback. Se publican todos los contrastes por semilla, incertidumbre
descriptiva y testigos, junto con una réplica completa tras corregir el verificador.
Ver [resultados de componentes](paper/component-results.md),
[protocolo](docs/salon-ablation-protocol.md) y
[auditoría bibliográfica](paper/literature-review.md).

    python -m scripts.analyze_salon_ablation
    python -m scripts.replay_salon_ablation
    python -m scripts.check_salon_repair
    python -m integrations.salon_ablation.run --out results/local-ablation

Las figuras científicas se reproducen con paper/requirements-figures.txt y
python -m scripts.plot_salon_ablation. El manuscrito ahora organiza una pregunta
común y diferencia observación, búsqueda y seguridad. El [mapa de afirmaciones](paper/claims-and-evidence.md)
identifica lo demostrado y lo pendiente.

## Piloto ejecutado con RESTler oficial (v0.7)

Se construyó RESTler desde un commit fijado y se ejecutaron 60 campañas por TCP,
con 44.808 llamadas de búsqueda y 31 testigos revalidados. Los 132 tests pasaron.
Los resultados separan las estrategias BFS/BFS-cheap y el oráculo común de los
checkers nativos, que están desactivados. Las repeticiones de RESTler son
deterministas y no representan muestras aleatorias independientes.

Ver [resultados y límites](paper/restler-pilot-results.md),
[protocolo fijado](docs/restler-pilot-protocol.md) y
[ejecución completa](https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38632820433).
El siguiente paso es validar dependencias de workflows y más estrategias de
RESTler antes de congelar una comparación principal. Este piloto no demuestra
superioridad general.

## Combinación evaluada y resultados completos (v0.8)

Se ejecutaron 900 campañas nuevas con azar, mutación de tareas y una combinación
que comparte el presupuesto por llamadas efectivas. Pasaron 139 tests y se
reprodujeron 892 testigos originales/minimizados de 446 campañas detectadas.
Hubo 160.806 llamadas de búsqueda; las 180 campañas corregidas no observaron fallas.

La combinación mejora la lectura fuera de alcance respecto de mutación sola,
pero pierde detecciones con historia bajo 120 llamadas. Con 480 llamadas alcanza
30/30 en alcance, cupos y confirmación; en reembolsos queda en 21/30 frente a
27/30 de mutación. No hay superioridad general. Ambos presupuestos y las pérdidas
se conservan en el [informe completo](paper/portfolio-results.md).

- [Protocolo previo a ejecución](docs/salon-portfolio-protocol.md).
- [Matriz y verificación en Actions](https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38751685998).
- [Figura reproducible](paper/figures/salon-portfolio.svg).
- [Candidato externo OWASP crAPI, todavía no evaluado](docs/independent-backend-candidate.md).

El intento local interrumpido también está publicado: sus 810 filas coinciden con
el rerun completo, excluyendo solamente el tiempo. El ZIP completo de RESTler v0.7
ya está preservado en Git, con hash verificado.

```bash
python -m scripts.verify_salon_portfolio results/salon-v08 --replay
python -m scripts.check_portfolio_recovery
```
