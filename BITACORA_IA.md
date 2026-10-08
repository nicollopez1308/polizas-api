# Bitácora de uso de IA

**Grupo:** DA8A · **Integrantes:** Nicole López, Luna Pico
**Herramientas usadas:** Claude (claude.ai), en una conversación de Nicole y otra de Luna. No usamos otras IA.

> Las tres secciones son obligatorias. **`## Rechazado` es la que se califica.**
> Una bitácora que solo lista prompts aceptados vale la mitad.

Forma de trabajo: Claude leía el enunciado y el código, proponía cada paso y lo probaba en una
copia del repositorio; nosotras ejecutábamos cada comando en nuestros equipos (Windows), le
pegábamos la salida real y solo hacíamos commit cuando la salida coincidía con lo esperado.
Todas las salidas de `HALLAZGOS.md`, `CONSULTAS.csv` y `DICTAMEN_IA.md` salieron de nuestras
terminales.

## Prompts

| # | Parte | Quién | Prompt (resumido si es largo) |
|---|-------|-------|-------------------------------|
| 1 | Todas | Nicole | «Tengo que realizar este taller (enlace al enunciado). Quiero que me ayudes a resolverlo paso a paso, explicándome todo detalladamente para evitar errores.» |
| 2 | Preparación | Nicole | «Me das un código pero ¿qué hago con esto?»: pedimos que cada comando viniera con dónde escribirlo (PowerShell o Git Bash) y qué debía responder. |
| 3 | A | Nicole | Le pegamos la respuesta de `GET /polizas/1`, la de `/polizas/99999` y la salida de `pytest tests/test_contrato.py` (11 failed, 1 passed) para identificar los defectos. |
| 4 | A | Nicole | Le pedimos que llevara la lista de hallazgos y armara `HALLAZGOS.md` con comandos de evidencia reproducibles por el calificador. |
| 5 | B | Nicole | Refactor restricción por restricción (B1 a B10), con un commit por restricción y comprobando con pytest antes de cada commit. |
| 6 | B | Nicole | Errores de Windows pegados tal cual: `Unlink of file 'app.db' failed`, `test_contrato.py fue modificado` en el verificador, `Virtualization support not detected` en Docker Desktop. |
| 7 | B7 · B8 | Luna | Ayuda paso a paso para preparar su equipo, corregir `esquemas.py` (B7) y escribir `tests/test_api.py` con base temporal y `dependency_overrides` (B8). |
| 8 | B8 | Luna | El Control de aplicaciones de Windows bloqueaba `pip.exe` y una DLL de scipy en su equipo; pidió alternativas y terminó trabajando en GitHub Codespaces. |
| 9 | C | Nicole | Le pegamos la salida de `contar_consultas.py` sin estrategias (11/2/11/11 y 2001/2/2001/2001) para decidir la estrategia de cada endpoint. |
| 10 | D | Nicole | Auditar `ia_tests_propuesta.py` y diseñar una mutación por defecto; le pegamos las salidas de cada mutación. |
| 11 | E | Nicole | Reescribir el README con el arranque real y ensayar la demo de Docker (`restart` y contenedor nuevo). |

## Aceptado

| # | Qué propuso la IA | Por qué lo aceptamos | Qué cambiamos antes de usarlo |
|---|-------------------|----------------------|-------------------------------|
| 1 | Comandos de evidencia de la Parte A con `curl -w "%{http_code}"` y `git show v0-semilla:archivo`, y las 14 filas de `HALLAZGOS.md` | `git show v0-semilla:` da la misma salida aunque el archivo ya esté corregido, y cada fila apunta a la versión donde vive el defecto | Corrimos cada comando en nuestra terminal y comprobamos que la salida coincidiera con la de la tabla; H12 y H14 se reescribieron para que la salida fuera de una sola línea y H14 fuera un comando autónomo |
| 2 | `config.py` con `BaseSettings`, `get_settings()` con `lru_cache` e inyectada con `Depends` (B2) | Es lo que pide B2 y hace que la app respete `DATABASE_URL` | Comprobamos con `Get-FileHash app.db` antes y después de pytest que la base real ya no cambiaba; generamos secretos nuevos con `secrets.token_hex(32)` en vez de reutilizar los comprometidos |
| 3 | `get_db()` con `yield` y `finally: db.close()`, sin sesión global (B3) | El comando de H14 pasó de 500 a 200: un error de un cliente ya no tumba el servicio | Nada; lo verificamos repitiendo el comando de H14 |
| 4 | Esquemas de salida con `from_attributes=True` y `response_model` en todas las rutas, `_buscar_poliza` con 404, 409 con `IntegrityError` + `rollback`, `PUT` con `exclude_unset` (B4, B6) | Pusieron en verde los 12 tests del contrato y los 7 de `test_api.py` | Corrimos `pytest` dos veces seguidas (19 passed) y sembramos 12 pólizas para revisar a mano que `token_firma` ya no salía |
| 5 | Estrategias de la Parte C: `selectinload`, `lazy`, `joinedload` y consulta `agregada` | Están respaldadas por nuestra medición: 2/2/1/1 y 5/2/1/1 consultas | Medimos primero el código sin estrategias; el 5 de `/polizas` con 2000 pólizas lo entendimos antes de aceptarlo (bloques de 500 en el `IN`) |
| 6 | `Dockerfile` multietapa sobre `python:3.11.9-slim-bookworm`, usuario no root, `HEALTHCHECK`, `.dockerignore` (B9) | Cumple B9 y el contenedor quedó `(healthy)` respondiendo desde el host | Lo construimos y probamos en el equipo de Nicole; pasamos `.env` a saltos de línea LF para Docker |
| 7 | `tests/test_ia_corregido.py` y las tres mutaciones de la Parte D | Cada mutación deja en verde la batería original y en rojo la corregida | Ejecutamos las mutaciones nosotras y deshicimos cada una con `git restore` antes de seguir |

## Rechazado

| # | Qué propuso la IA | Por qué lo rechazamos | Qué hicimos en su lugar |
|---|-------------------|-----------------------|-------------------------|
| 1 | La batería de tests generada por IA, `ia_tests_propuesta.py`, tal como venía | Está en verde pero no demuestra nada: su «aislamiento» sustituye una función `get_db` local que la app no usa (escribió 7 pólizas en nuestra `app.db`, de 19 a 26), acepta varios códigos de estado a la vez (`in (200, 201, 422)`) y usa datos aleatorios sin semilla (8 corridas con el mismo código: 6 en verde y 2 en rojo) | La corregimos en `tests/test_ia_corregido.py` y lo demostramos con tres mutaciones en `DICTAMEN_IA.md` |
| 2 | Primera opción que evaluamos con Claude para B1: fijar en `requirements.txt` las versiones que `pip` acababa de instalar en Windows (numpy 2.5.3, con scipy 1.18.1 como dependencia) | Al revisarlas en PyPI, esas versiones exigen Python ≥ 3.12, y la imagen de Docker usa 3.11.9: el `docker build` habría fallado aunque todo funcionara en nuestro equipo | Fijamos `numpy==2.4.6`, que funciona en 3.11 y en 3.12 (commit `89ce7a3`) |
| 3 | Alternativa que Claude midió en la Parte C siguiendo la regla «cargar todo de una vez»: `joinedload` en `/polizas` (1 consulta en vez de 5) | Lo medimos: con 2000 pólizas fue más lento (230 ms contra 180 ms), porque en una relación uno-a-muchos el `JOIN` repite cada póliza por cada siniestro | `selectinload` en `/polizas` (commit `2daadf3`; explicado en `HALLAZGOS.md`, Parte C) |
| 4 | Alternativa medida: corregir el N+1 de `/resumen` con `selectinload` | Corrige el N+1 (5 consultas), pero trae los 6000 siniestros a memoria solo para sumarlos: 166 ms contra 15 ms de la consulta agregada | Consulta `agregada` con `COUNT`, `SUM` y `GROUP BY` (commit `2daadf3`) |
| 5 | Alternativa medida: cargar con `joinedload` los siniestros de `/polizas/{id}` | La medición dio 2 consultas con 10 y con 2000 pólizas: no crece con N, así que adelantar la carga no cambia cómo escala | Lo dejamos en `lazy` con un comentario en `main.py` |
| 6 | La lista inicial de Claude tenía 15 candidatos; incluir en `HALLAZGOS.md` el 15.º: `/predicciones` sin el número de póliza | El máximo es 14 y una fila débil resta; no encontramos una sección del curso que lo cubriera directamente | Lo dejamos fuera de la tabla, pero lo corregimos en B6 porque lo exige `test_score_registra_la_prediccion` |
| 7 | En el plan inicial de B4, hacer obligatorio `asegurado` en el modelo al mismo tiempo que `tipo` y `fecha_fin` | Con el validador todavía sin `return`, todas las pólizas nuevas habrían fallado al guardarse | Lo pospusimos hasta que Luna arregló el validador (B7, `f696890`) y lo hicimos en la migración inicial (B5, `151f78f`) |
| 8 | Tomar las evidencias de la Parte A con `curl` en PowerShell | En PowerShell `curl` es otro programa con otro formato de salida: no coincidiría con lo que reproduce el calificador | Corrimos todos los comandos de evidencia en Git Bash |
| 9 | Una imagen de Docker que solo arrancaba con `--env-file .env` (primera versión de B9) | El enunciado arranca el contenedor con `docker run -p 8000:8000`, sin `--env-file`; así la app se caía por falta de secretos, y no arrancar con `docker run` pone tope de 60 | La imagen trae los valores de ejemplo de `.env.example`, que se sobrescriben con `--env-file` (commit `73f8a89`); lo probamos sin `--env-file` |
| 10 | Un comando concreto con volumen (`-v ...`) en el README para conservar los datos al borrar el contenedor | No lo habíamos probado y, con el usuario no root, la carpeta del volumen podía quedar sin permisos de escritura | En el README solo explicamos qué pasa con los datos tras `restart` y tras un contenedor nuevo, y que haría falta un volumen |
