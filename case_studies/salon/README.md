# TurnoSalon — reservas de servicios por sucursal

Segundo backend del laboratorio: clientes, empleados, reservas, cupos, cobros
con crédito simulado, cancelaciones y reintegros. Código nuevo creado para el
experimento, con API y base SQL reales. No procede de un negocio en producción.

Backend: backends/salon. Experimento: integrations/salon.
Contrato y matriz fijada: docs/salon-protocol.md.

## Ejecutar

Desde la raíz del repositorio, Python 3.11+:

    python -m venv .venv
    .venv/bin/pip install -r backends/salon/requirements.lock
    .venv/bin/python -m unittest discover -s tests -p 'test_salon.py' -v
    .venv/bin/python -m integrations.salon.run --out results/local-salon
    .venv/bin/python -m scripts.analyze_salon

El análisis sin argumentos verifica la matriz archivada results/salon-v05.
La corrida nueva exige una carpeta vacía y usa un SQLite temporal por variante.

## API independiente

    export SALON_SIGNING_KEY='salon-research-public-fixture-signing-key-only'
    .venv/bin/python -m backends.salon --db /tmp/salon-demo.db --fixture

La base debe ser nueva al usar --fixture. API local en http://127.0.0.1:8000;
OpenAPI en /docs. La CLI solamente expone la versión fixed.

POST /sessions con username alice y password research-only-alice obtiene
una sesión Bearer. Otros usuarios sintéticos: bob, staff_a y staff_b;
sus contraseñas siguen el mismo prefijo research-only-.

GET /bookings, POST /bookings con slot a, GET /bookings/a y
POST /bookings/a/{reserve,pay,confirm,cancel,refund} son los endpoints de negocio.
Confirm y refund requieren staff_a en la sucursal a.
Los ejemplos contienen credenciales públicas de fixtures, no credenciales reales.
La clave pública sirve exclusivamente para la demo local.

## Qué significa el experimento

Cuatro errores deliberados se comparan contra un control corregido.
Los motores y operadores se transfieren de v0.3; se implementan otro contrato,
programas legítimos y oráculo. Detectar mutantes conocidos en este servicio nuevo
no demuestra generalización a empresas independientes ni seguridad del control.
