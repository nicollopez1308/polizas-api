# Pólizas API

Servicio de gestión de pólizas de la Aseguradora Santo Tomás. Registra pólizas y los
siniestros que se les declaran, resume la cartera y puntúa el riesgo de cada póliza con un
modelo, guardando cada predicción.

Grupo DA8A · Nicole López, Luna Pico · Python para Desarrollo de APIs e IA, USTA 2026-II.
Parte del semilla `polizas-api-v0` (etiqueta `v0-semilla`); los defectos encontrados y su
corrección están en `HALLAZGOS.md`.

## ⚠️ Secretos comprometidos

Las claves `SECRETO_FIRMA` y `CLAVE_API_REASEGURO` estuvieron escritas en `config.py` y
quedaron versionadas en la historia de git (commit `5a5cc5b`, etiqueta `v0-semilla`). Borrarlas
del código no las borra de la historia: **se consideran comprometidas y no deben usarse en
ningún entorno**. Hay que generar claves nuevas (por ejemplo con
`python -c "import secrets; print(secrets.token_hex(32))"`), ponerlas solo en el `.env` local,
que no se versiona, y rotar la clave del reasegurador con el proveedor.

## Requisitos

- Python 3.11 o 3.12 (la imagen de Docker usa 3.11.9).
- Docker, para correrlo en contenedor.

## Configuración

Toda la configuración se lee de variables de entorno o del archivo `.env` (ver `config.py`).
`.env.example` trae valores de ejemplo con los que el servicio arranca:

| Variable | Qué es | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Base de datos | `sqlite:///app.db` |
| `SECRETO_FIRMA` | Secreto con el que se firma cada póliza | — |
| `CLAVE_API_REASEGURO` | Clave del servicio del reasegurador | — |
| `RUTA_MODELO` | Modelo serializado | `modelo.pkl` |
| `UMBRAL_ALTO_RIESGO` | Puntaje desde el que una póliza es de alto riesgo | `0.6` |

## Arranque local (uvicorn)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows (PowerShell): Copy-Item .env.example .env
alembic upgrade head               # crea las tablas en la base de DATABASE_URL
uvicorn main:app --port 8000
```

La documentación interactiva queda en `http://localhost:8000/docs` y la sonda de salud en
`http://localhost:8000/health`. La base empieza vacía; para cargar datos de ejemplo, con el
servicio encendido:

```bash
python sembrar_datos.py --polizas 12
```

El esquema de la base lo crean las migraciones de Alembic (`alembic/`), no la aplicación al
arrancar: si se cambia un modelo, se genera una revisión nueva con
`alembic revision --autogenerate -m "descripción"` y se aplica con `alembic upgrade head`.

## Arranque en contenedor (Docker)

```bash
docker build -t polizas-api .
docker run -d --name polizas -p 8000:8000 polizas-api
curl localhost:8000/health
```

Al arrancar, el contenedor aplica las migraciones (`alembic upgrade head`) y luego levanta
uvicorn en `0.0.0.0:8000`, sin `--reload`, con un usuario sin privilegios. El `HEALTHCHECK`
consulta `/health` cada 30 segundos (`docker ps` muestra `healthy`).

La imagen trae los mismos valores de ejemplo de `.env.example` para que arranque sin
configurar nada. **Con secretos reales**, se pasan al arrancar y tienen prioridad:

```bash
docker run -d --name polizas -p 8000:8000 --env-file .env polizas-api
```

`.env` y las bases `*.db` nunca entran en la imagen: los excluye `.dockerignore`.

### Qué pasa con los datos

La base SQLite vive dentro del contenedor (`/app/app.db`), sin volumen:

- `docker restart polizas` reinicia el **mismo** contenedor: su sistema de archivos se
  conserva, así que las pólizas creadas siguen ahí.
- `docker rm -f polizas` y un `docker run` nuevo desde la misma imagen crean un contenedor
  **nuevo**, que parte de la imagen, donde no hay base: las migraciones crean una vacía y
  `GET /polizas` responde `[]`.

Para que los datos sobrevivan a borrar el contenedor habría que guardar la base en un volumen
de Docker (`docker run -v ...`) y apuntar `DATABASE_URL` a un archivo dentro de él; esta
entrega no lo hace.

## Endpoints

| Método | Ruta | Qué hace | Códigos |
|---|---|---|---|
| GET | `/health` | Sonda de salud; informa si la base responde | 200 |
| POST | `/polizas` | Crea una póliza, con sus siniestros si ya tiene | 201, 409 número repetido, 422 |
| GET | `/polizas` | Lista las pólizas con sus siniestros | 200 |
| GET | `/polizas/{id}` | Consulta una póliza | 200, 404 |
| PUT | `/polizas/{id}` | Actualiza **solo** los campos enviados | 200, 404, 422 |
| POST | `/polizas/{id}/siniestros` | Declara un siniestro | 201, 404, 422 |
| GET | `/siniestros` | Lista los siniestros con el número de su póliza | 200 |
| GET | `/resumen` | Siniestros y monto total por póliza | 200 |
| POST | `/score` | Puntúa el riesgo de una póliza y guarda la predicción | 200, 404 |
| GET | `/predicciones` | Histórico de predicciones, con el número de póliza | 200 |

Ninguna respuesta incluye `token_firma`: cada ruta declara un `response_model` con los campos
que puede devolver.

### Ejemplo

```bash
curl -X POST localhost:8000/polizas \
  -H "Content-Type: application/json" \
  -d '{"numero": "POL-2026-09001", "asegurado": "Ana Rueda", "tipo": "auto", "prima": 1250000,
       "fecha_inicio": "2026-01-15", "fecha_fin": "2027-01-14"}'
```

```bash
curl -X POST localhost:8000/score -H "Content-Type: application/json" -d '{"numero": "POL-2026-09001"}'
```

## Pruebas

```bash
pytest
```

Corre las tres baterías: `tests/test_contrato.py` (contrato del docente, intacto),
`tests/test_api.py` (pruebas propias) y `tests/test_ia_corregido.py` (la batería de la IA
corregida en la Parte D). Las pruebas sustituyen `get_db` con `app.dependency_overrides` por
una base SQLite temporal: nunca tocan `app.db` y pueden correrse varias veces seguidas.

## Utilidades y entregables

- `sembrar_datos.py`: crea pólizas de ejemplo a través de la API.
- `contar_consultas.py`: cuenta las sentencias SQL de cada endpoint y escribe `CONSULTAS.csv`
  (Parte C; lo modificamos para que escriba también la estrategia de carga).
- `verificar_entrega.py`: comprobación de entregables del docente.
- `HALLAZGOS.md` (Partes A y C), `CONSULTAS.csv` (Parte C), `DICTAMEN_IA.md` (Parte D),
  `BITACORA_IA.md` (Parte E), `EQUIPO.md`.
