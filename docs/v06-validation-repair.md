# v0.6 — reparación del verificador y repetición

La primera matriz completó sus 1200 campañas y los replays HTTP internos.
El análisis offline detectó una incompatibilidad de tipos al comparar el
resumen recalculado con summary.json: Wilson devolvía una tupla, que JSON
deserializa como lista. Los valores de los intervalos eran iguales.

La corrección convierte la tupla en lista al construir el resumen. Se agrega
una prueba de ida/vuelta JSON. No se modifican backend, oráculo, generador,
selección de programas, RNG, semillas, presupuesto, corpus, protocolo ni
contrastes. De acuerdo con el protocolo, se congela la corrección y se vuelve
a ejecutar la matriz completa.

Primera corrida: 1200 campañas, 292 detecciones y 129799 llamadas HTTP.
SHA-256 del JSONL descomprimido:
ec50b0f43039f313cfb497cdc2ddae1bca936349855f375b0ce15537b9639b1c.
Configuración SHA-256:
2294a82ca0d039bed2cf68732b140afeca0d49d6d1943c9a828fa9314aa99e92.
Código inicial congelado:
011359225b375b485afcf53aea518db9efaa760e.

Los datos de la primera corrida se conservan como intermediate/attempt1 dentro
de la evidencia de v0.6, y no se suman como réplicas adicionales a la matriz
principal. Un archivo repair-verification.json compara los 1200 resultados
semánticos omitiendo solamente elapsed_s, que depende del equipo y carga.
Sus hashes de código se deben resolver contra el commit inicial, no contra el
verificador corregido. La matriz principal y sus fuentes pasan el verificador
actual sin modificaciones en tiempo de ejecución.
