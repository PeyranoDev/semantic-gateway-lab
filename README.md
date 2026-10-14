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

El primer comando ejecuta **44 pruebas**. La demo valida ocho defectos
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
python -m fuzzlab replay results/pilot-final/traces/cross_department_read-random-0.json
```

`minimal_trace` conserva la violación y es mínima bajo eliminación de una acción,
no necesariamente la secuencia más corta posible. Los tokens de las trazas usan
una clave pública de prueba: no son credenciales.

## Interpretar resultados

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

Backend determinista en memoria, reloj fijo y dominio finito de prueba. No se
implementa transporte MCP, OPA/Rego, un firewall semántico, modelos de lenguaje,
una interfaz de aprobación humana ni persistencia durable. La aprobación HMAC
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
