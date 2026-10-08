# Pólizas API

Servicio web para la gestión de pólizas de seguro y siniestros de la Aseguradora Santo Tomás,
con cálculo del riesgo de cada póliza mediante un modelo estadístico.

**Grupo DA8A:** Nicole López y Luna Pico
**Asignatura:** Python para Desarrollo de APIs e Inteligencia Artificial · Universidad Santo Tomás · 2026-II
**Entrega:** Taller del Corte II

---

## Tabla de contenido

1. [Descripción general](#1-descripción-general)
2. [Glosario](#2-glosario)
3. [Aviso de seguridad](#3-aviso-de-seguridad)
4. [Requisitos previos](#4-requisitos-previos)
5. [Instalación y ejecución local](#5-instalación-y-ejecución-local)
6. [Ejecución con Docker](#6-ejecución-con-docker)
7. [Uso del servicio](#7-uso-del-servicio)
8. [Referencia de la API](#8-referencia-de-la-api)
9. [Códigos de estado HTTP](#9-códigos-de-estado-http)
10. [Configuración](#10-configuración)
11. [Pruebas automatizadas](#11-pruebas-automatizadas)
12. [Estructura del proyecto](#12-estructura-del-proyecto)
13. [Solución de problemas](#13-solución-de-problemas)
14. [Antecedentes del proyecto](#14-antecedentes-del-proyecto)

---

## 1. Descripción general

Una **póliza** es un contrato de seguro. Registra quién está asegurado, el tipo de seguro (de
auto, de hogar o de vida), cuánto paga al año (la **prima**) y entre qué fechas está vigente.
Un **siniestro** es un evento que el asegurado reclama, por ejemplo un choque o un robo, con su
fecha y su monto.

Este proyecto es un **servicio web**: un programa que permanece encendido y responde a las
peticiones que otros programas le envían, como "registrar esta póliza" o "consultar todas las
pólizas". Es la pieza que utilizaría, por ejemplo, la aplicación interna de la aseguradora para
guardar y consultar su información. El servicio incluye una **página de pruebas** que se abre
en el navegador y permite usarlo sin conocimientos de programación (ver
[sección 7](#7-uso-del-servicio)).

Funciones del servicio:

- Registrar, consultar y actualizar pólizas.
- Declarar siniestros sobre una póliza.
- Generar un resumen con el número de siniestros de cada póliza y la suma de sus montos.
- Calcular un **puntaje de riesgo** entre 0 y 1 para una póliza. Lo calcula un modelo de
  aprendizaje automático (`modelo.pkl`) a partir de la prima, el número de siniestros, la suma
  de sus montos y los días que lleva vigente la póliza. Cuando el puntaje supera 0,6, la póliza
  se clasifica como de **alto riesgo**. Cada cálculo queda registrado en un historial.

## 2. Glosario

| Término | Significado en este documento |
|---|---|
| **API** | Conjunto de peticiones que acepta el servicio y de respuestas que entrega. |
| **Ruta** (*endpoint*) | Cada dirección a la que se puede enviar una petición, por ejemplo `/polizas`. |
| **GET, POST, PUT** | Tipo de petición: `GET` consulta, `POST` crea un registro nuevo y `PUT` modifica uno existente. |
| **JSON** | Formato de texto en el que se envían y reciben los datos, por ejemplo `{"numero": "POL-2026-09001", "prima": 1250000}`. |
| **Código de estado** | Número de tres cifras con el que el servicio informa el resultado de una petición: `200` éxito, `404` no encontrado, etc. (ver [sección 9](#9-códigos-de-estado-http)). |
| **Terminal** | Programa en el que se escriben instrucciones en lugar de usar el ratón. En Windows: PowerShell o Git Bash; en macOS: Terminal. |
| **Comando** | Instrucción que se escribe en la terminal y se ejecuta al presionar **Enter**. |
| **Repositorio** | Carpeta del proyecto junto con el historial de todos sus cambios, alojada en GitHub. |
| **Entorno virtual** | Carpeta (`.venv`) en la que se instalan las librerías de este proyecto, separada del resto del computador. |
| **Base de datos** | Archivo `app.db` en el que se guardan las pólizas. Es una base SQLite: un único archivo que no requiere instalar programas adicionales. |
| **Migración** | Conjunto de instrucciones, guardadas en la carpeta `alembic/`, que crean o actualizan las tablas de la base de datos. |
| **Docker / contenedor** | Herramienta que empaqueta Python, las librerías y el código en un "contenedor", para que el servicio funcione igual en cualquier computador. |
| **localhost** | Nombre con el que un computador se refiere a sí mismo. `localhost:8000` es el servicio ejecutándose en el propio equipo, en el puerto 8000. |

## 3. Aviso de seguridad

En la versión original de este proyecto (commit `5a5cc5b`, etiqueta `v0-semilla`), las claves
`SECRETO_FIRMA` y `CLAVE_API_REASEGURO` estaban escritas dentro del código (`config.py`) y
quedaron guardadas en el historial público del repositorio. Aunque ya se retiraron del código,
**siguen siendo visibles en ese historial**. En consecuencia:

- **Esas claves se consideran comprometidas y no deben usarse en ningún entorno.**
- Cada instalación debe usar **claves nuevas**, guardadas únicamente en el archivo `.env`, que
  nunca se publica en GitHub (ver [sección 10](#10-configuración)).
- La clave del reasegurador debe renovarse también ante el proveedor.

Para generar una clave nueva y aleatoria, una vez completada la instalación (sección 5, con el
entorno virtual activado), ejecute:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

El comando imprime 64 caracteres aleatorios. Ejecútelo una vez por cada clave.

## 4. Requisitos previos

Esta sección se realiza una sola vez por computador.

### 4.1 Cómo abrir una terminal y escribir comandos

Toda la instalación se hace escribiendo comandos en una terminal.

- **Windows:** presione la tecla **Windows**, escriba `PowerShell` y abra **Windows PowerShell**.
- **macOS:** presione **Cmd + Espacio**, escriba `Terminal` y presione **Enter**.
- **Linux:** abra la aplicación **Terminal** del menú de aplicaciones.

Reglas para todos los comandos de este documento:

- Cada recuadro gris contiene uno o varios comandos. Escriba (o copie y pegue) **una línea a la
  vez** y presione **Enter**.
- Las líneas que empiezan con `#` son comentarios explicativos: **no se escriben**.
- Cuando un paso indica una versión para Windows y otra para macOS o Linux, use solo la de su
  sistema.

### 4.2 Programas necesarios

| Programa | Uso | Instalación |
|---|---|---|
| **Git** | Descargar el proyecto. En Windows incluye **Git Bash**, una terminal útil para algunos ejemplos. | Descargar desde [git-scm.com](https://git-scm.com/downloads) e instalar con las opciones predeterminadas. |
| **Python 3.11 o 3.12** | Ejecutar el servicio en el computador (sección 5). | Descargar desde [python.org/downloads](https://www.python.org/downloads/). **En Windows, marque la casilla "Add python.exe to PATH"** en la primera pantalla del instalador, antes de pulsar *Install Now*. |
| **Docker Desktop** *(opcional)* | Ejecutar el servicio en un contenedor (sección 6). | Se explica en la [sección 4.4, «Instalación de Docker Desktop»](#44-instalación-de-docker-desktop-opcional). |
| **Navegador web** | Usar la página de pruebas del servicio. | Cualquiera: Chrome, Edge, Firefox o Safari. |

### 4.3 Verificación de la instalación

Cierre y vuelva a abrir la terminal (para que reconozca los programas recién instalados) y
ejecute:

```bash
git --version
python --version
```

Cada comando debe responder con un número de versión, por ejemplo `git version 2.51.0` y
`Python 3.12.3`. Si `python` no se reconoce, consulte la [sección 13](#13-solución-de-problemas).

### 4.4 Instalación de Docker Desktop (opcional)

Solo es necesario para la sección 6.

1. Descargue Docker Desktop desde [docker.com](https://www.docker.com/products/docker-desktop/)
   e instálelo con las opciones predeterminadas.
2. **En Windows**, Docker requiere el Subsistema de Windows para Linux (WSL 2). Abra PowerShell
   **como administrador** (tecla Windows → escriba `PowerShell` → clic en *Ejecutar como
   administrador*) y ejecute:

   ```bash
   wsl --install --no-distribution
   ```

   Luego **reinicie el computador**.
3. Abra Docker Desktop y espere a que en la esquina inferior izquierda aparezca
   **"Engine running"**. Para confirmar que funciona, ejecute en una terminal:

   ```bash
   docker run hello-world
   ```

   Debe aparecer el mensaje `Hello from Docker!`.

## 5. Instalación y ejecución local

Siga los pasos en orden. Al terminar, el servicio quedará funcionando en su computador.

### Paso 1. Elegir una carpeta de trabajo

Se recomienda crear una carpeta propia para proyectos. **En Windows, evite el Escritorio y las
carpetas sincronizadas con OneDrive**, porque la sincronización bloquea archivos del proyecto.

```bash
mkdir proyectos
cd proyectos
```

`mkdir` crea la carpeta `proyectos` y `cd` entra en ella.

### Paso 2. Descargar el proyecto

```bash
git clone https://github.com/nicollopez1308/polizas-api.git
cd polizas-api
```

El primer comando descarga el proyecto en una carpeta llamada `polizas-api`; el segundo entra en
ella. **Todos los comandos siguientes deben ejecutarse dentro de esta carpeta.**

### Paso 3. Crear y activar el entorno virtual

```bash
python -m venv .venv
```

```bash
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# macOS o Linux:
source .venv/bin/activate
```

Si la activación funcionó, la línea de la terminal empieza con `(.venv)`. **Cada vez que abra
una terminal nueva** para trabajar con este proyecto, entre a la carpeta (`cd`) y vuelva a
activar el entorno con este mismo comando.

### Paso 4. Instalar las librerías

```bash
pip install -r requirements.txt
```

La instalación tarda algunos minutos. El archivo `requirements.txt` fija la versión exacta de
cada librería, de modo que todas las instalaciones resultan idénticas.

### Paso 5. Crear el archivo de configuración

```bash
# Windows (PowerShell):
Copy-Item .env.example .env

# macOS o Linux:
cp .env.example .env
```

Con los valores de ejemplo el servicio ya funciona. Para un uso real, abra el archivo `.env` con
cualquier editor de texto y reemplace los valores de `SECRETO_FIRMA` y `CLAVE_API_REASEGURO`
por claves nuevas (ver [sección 3](#3-aviso-de-seguridad)).

### Paso 6. Crear la base de datos

```bash
alembic upgrade head
```

Este comando crea el archivo `app.db` con sus tablas, vacías. La última línea debe indicar
`Running upgrade -> ..., esquema inicial`. Si la base de datos ya existía, no se borra: solo se
aplican los cambios que le falten.

### Paso 7. Iniciar el servicio

```bash
uvicorn main:app --port 8000
```

El servicio está en funcionamiento cuando aparece la línea
`Uvicorn running on http://127.0.0.1:8000`. **No cierre esa terminal**: el servicio funciona
mientras ella permanezca abierta. Para detenerlo, haga clic en la terminal y presione
**Ctrl + C**.

Para comprobar que responde, abra en el navegador `http://localhost:8000/health`. Debe mostrar
`{"estado":"ok","base_de_datos":"ok"}`.

### Paso 8 (opcional). Cargar datos de ejemplo

Con el servicio en funcionamiento, abra **una segunda terminal**, entre a la carpeta del
proyecto, active el entorno virtual (paso 3) y ejecute:

```bash
python sembrar_datos.py --polizas 12
```

Se crean 12 pólizas de ejemplo con 3 siniestros cada una, registradas a través del propio
servicio. La respuesta esperada es `12 pólizas creadas (ids 1…12), 3 siniestros cada una.`
Este comando se ejecuta una sola vez por base de datos; si se repite, falla con el código `409`
porque esas pólizas ya existen (ver [sección 13](#13-solución-de-problemas)).

Continúe en la [sección 7](#7-uso-del-servicio) para usar el servicio.

## 6. Ejecución con Docker

Requiere Docker Desktop abierto y en estado **"Engine running"** (ver la
[sección 4.4, «Instalación de Docker Desktop»](#44-instalación-de-docker-desktop-opcional)), y el proyecto descargado (pasos 1 y 2 de la
sección 5). Los comandos se ejecutan dentro de la carpeta `polizas-api`. No es necesario crear
el entorno virtual ni instalar las librerías: el contenedor las trae.

### Paso 1. Construir la imagen

```bash
docker build -t polizas-api .
```

La imagen es la plantilla del contenedor: incluye Python 3.11.9, las librerías y el código. La
primera construcción tarda varios minutos; las siguientes son más rápidas.

### Paso 2. Iniciar el contenedor

```bash
docker run -d --name polizas -p 8000:8000 polizas-api
```

- `-d` ejecuta el contenedor en segundo plano y deja libre la terminal.
- `--name polizas` le asigna el nombre `polizas`.
- `-p 8000:8000` conecta el puerto 8000 del computador con el puerto 8000 del contenedor.

Al iniciar, el contenedor crea las tablas de la base de datos (`alembic upgrade head`) y luego
pone en marcha el servicio. Espere unos 30 segundos y abra en el navegador
`http://localhost:8000/health`. Debe mostrar `{"estado":"ok","base_de_datos":"ok"}`.

### Paso 3. Administrar el contenedor

| Comando | Función |
|---|---|
| `docker ps` | Lista los contenedores en ejecución. En la columna `STATUS` debe aparecer `healthy`: Docker consulta `/health` cada 30 segundos. |
| `docker logs polizas` | Muestra los mensajes del servicio; es útil para diagnosticar errores. |
| `docker restart polizas` | Reinicia el contenedor. |
| `docker rm -f polizas` | Detiene y elimina el contenedor. La imagen se conserva. |

### Uso con claves propias

La imagen incluye los mismos valores de ejemplo de `.env.example`, para que el contenedor
funcione sin configuración adicional. Para usar claves reales, cree el archivo `.env` (paso 5 de
la sección 5) y entrégueselo al contenedor al iniciarlo; sus valores tienen prioridad sobre los
de ejemplo:

```bash
docker run -d --name polizas -p 8000:8000 --env-file .env polizas-api
```

El archivo `.env` y las bases de datos **nunca se incluyen en la imagen**: el archivo
`.dockerignore` los excluye.

### Persistencia de los datos

La base de datos se guarda **dentro** del contenedor:

- Tras `docker restart polizas`, los datos **se conservan**, porque se reinicia el mismo
  contenedor con sus mismos archivos.
- Si el contenedor se elimina (`docker rm -f polizas`) y se crea uno nuevo con `docker run`, el
  nuevo parte de la imagen, que no contiene base de datos: se crea una vacía y **los datos
  anteriores se pierden**.

Para conservar los datos al eliminar el contenedor sería necesario guardar la base de datos en
un **volumen** de Docker (`docker run -v ...`) y apuntar `DATABASE_URL` a un archivo dentro de
él. Esta versión no lo implementa.

## 7. Uso del servicio

### 7.1 Desde el navegador (recomendado)

Con el servicio en funcionamiento, abra en el navegador:

```
http://localhost:8000/docs
```

Se muestra la lista completa de rutas. Para usar una de ellas:

1. Haga clic sobre la ruta, por ejemplo **POST /polizas**.
2. Haga clic en **Try it out**.
3. Complete los datos en el recuadro. La página propone un ejemplo que puede editar.
4. Haga clic en **Execute**.
5. Debajo aparecen el **código de estado** (columna *Code*) y la respuesta (*Response body*).

Ejemplo de datos para registrar una póliza:

```json
{
  "numero": "POL-2026-09001",
  "asegurado": "Ana Rueda",
  "tipo": "auto",
  "prima": 1250000,
  "fecha_inicio": "2026-01-15",
  "fecha_fin": "2027-01-14"
}
```

### 7.2 Desde la terminal, con `curl`

Alternativa para usuarios de terminal. Los ejemplos funcionan en **Git Bash** (Windows), macOS y
Linux. No se recomienda PowerShell: en ella `curl` corresponde a otro programa y las comillas se
interpretan de otra forma.

```bash
curl -X POST localhost:8000/polizas \
  -H "Content-Type: application/json" \
  -d '{"numero": "POL-2026-09001", "asegurado": "Ana Rueda", "tipo": "auto", "prima": 1250000, "fecha_inicio": "2026-01-15", "fecha_fin": "2027-01-14"}'
```

`-X POST` indica una petición de creación, `-H` informa que los datos van en formato JSON y `-d`
contiene los datos.

## 8. Referencia de la API

### 8.1 Resumen de rutas

| Método | Ruta | Descripción | Códigos posibles |
|---|---|---|---|
| GET | `/health` | Estado del servicio y de la base de datos | 200 |
| POST | `/polizas` | Registra una póliza, con sus siniestros si los tiene | 201 · 409 · 422 |
| GET | `/polizas` | Lista todas las pólizas con sus siniestros | 200 |
| GET | `/polizas/{id}` | Consulta una póliza por su identificador | 200 · 404 |
| PUT | `/polizas/{id}` | Modifica **únicamente** los campos enviados de una póliza | 200 · 404 · 422 |
| POST | `/polizas/{id}/siniestros` | Declara un siniestro en una póliza | 201 · 404 · 422 |
| GET | `/siniestros` | Lista todos los siniestros con el número de su póliza | 200 |
| GET | `/resumen` | Número de siniestros y monto total por póliza | 200 |
| POST | `/score` | Calcula y registra el puntaje de riesgo de una póliza | 200 · 404 · 422 |
| GET | `/predicciones` | Historial de puntajes calculados | 200 |

En las rutas, `{id}` se reemplaza por el identificador interno de la póliza, por ejemplo
`/polizas/1`. El servicio asigna ese identificador al registrar la póliza (campo `id` de la
respuesta).

Las respuestas de ejemplo de esta sección se obtuvieron ejecutando el servicio.

### 8.2 `GET /health` — Estado del servicio

```json
{"estado": "ok", "base_de_datos": "ok"}
```

Si la base de datos no responde, el campo `base_de_datos` toma el valor `"sin conexión"`.

### 8.3 `POST /polizas` — Registro de una póliza

| Campo | Obligatorio | Reglas |
|---|---|---|
| `numero` | Sí | Entre 8 y 20 caracteres, por ejemplo `POL-2026-09001`. No puede repetirse. |
| `asegurado` | Sí | Entre 3 y 80 caracteres. Se eliminan los espacios sobrantes y se escribe con mayúscula inicial: `"  ana   rueda "` se guarda como `"Ana Rueda"`. |
| `tipo` | Sí | Tipo de seguro: `auto`, `hogar` o `vida`. El servicio no rechaza otros textos, por lo que debe escribirse exactamente así. |
| `prima` | Sí | Valor anual en pesos, mayor que 0. |
| `fecha_inicio` | Sí | Formato `AAAA-MM-DD`. |
| `fecha_fin` | Sí | Formato `AAAA-MM-DD`; debe ser **posterior** a `fecha_inicio`. |
| `siniestros` | No | Lista de siniestros, con las reglas de la [sección 8.6](#86-post-polizasidsiniestros--declaración-de-un-siniestro). Si se omite, la póliza se registra sin siniestros. |

Respuesta exitosa (código **201**):

```json
{"id": 1, "numero": "POL-2026-09001", "asegurado": "Ana Rueda", "tipo": "auto",
 "prima": 1250000.0, "fecha_inicio": "2026-01-15", "fecha_fin": "2027-01-14", "siniestros": []}
```

Si el número ya está registrado (código **409**):

```json
{"detail": "ya existe la póliza POL-2026-09001"}
```

Si algún dato no cumple las reglas, la respuesta tiene código **422** e indica el campo y el
motivo. Por ejemplo, con las fechas invertidas, el mensaje incluye
`fecha_fin debe ser posterior a fecha_inicio`.

### 8.4 `GET /polizas` y `GET /polizas/{id}` — Consulta de pólizas

`GET /polizas` devuelve la lista de todas las pólizas, cada una con sus siniestros, ordenadas
por `id`. `GET /polizas/1` devuelve únicamente la póliza 1. Si no existe (código **404**):

```json
{"detail": "no existe la póliza 99"}
```

### 8.5 `PUT /polizas/{id}` — Actualización de una póliza

Se envían **solo** los campos que se desea modificar; los demás conservan su valor. Pueden
modificarse `asegurado`, `tipo`, `prima` y `fecha_fin`. Ejemplo para cambiar la prima:

```json
{"prima": 1400000}
```

La respuesta (código **200**) contiene la póliza completa ya actualizada. Si la nueva
`fecha_fin` resultara anterior a `fecha_inicio`, la respuesta tiene código **422** y la póliza
no se modifica.

### 8.6 `POST /polizas/{id}/siniestros` — Declaración de un siniestro

| Campo | Obligatorio | Reglas |
|---|---|---|
| `fecha` | Sí | Formato `AAAA-MM-DD`. |
| `monto` | Sí | Valor en pesos, mayor que 0. |
| `descripcion` | Sí | Entre 3 y 200 caracteres. |
| `estado` | No | Si se omite, toma el valor `abierto`. |

Ejemplo de datos:

```json
{"fecha": "2026-03-10", "monto": 850000, "descripcion": "Choque leve en vía urbana"}
```

Respuesta exitosa (código **201**):

```json
{"id": 1, "fecha": "2026-03-10", "monto": 850000.0,
 "descripcion": "Choque leve en vía urbana", "estado": "abierto"}
```

Si la póliza no existe, la respuesta tiene código **404** y el siniestro **no** se registra.

### 8.7 `GET /siniestros` — Listado de siniestros

```json
[{"id": 1, "fecha": "2026-03-10", "monto": 850000.0, "descripcion": "Choque leve en vía urbana",
  "estado": "abierto", "poliza_id": 1, "numero_poliza": "POL-2026-09001"}]
```

### 8.8 `GET /resumen` — Resumen por póliza

Una fila por póliza, con su número de siniestros y la suma de sus montos. Las pólizas sin
siniestros aparecen con valor 0.

```json
[{"numero": "POL-2026-09001", "n_siniestros": 1, "monto_total": 850000.0}]
```

### 8.9 `POST /score` — Cálculo del puntaje de riesgo

Se envía el **número** de la póliza (no su `id`):

```json
{"numero": "POL-2026-09001"}
```

Respuesta exitosa (código **200**):

```json
{"numero": "POL-2026-09001", "puntaje": 0.5123, "alto_riesgo": false}
```

- `puntaje` varía entre 0 (riesgo bajo) y 1 (riesgo alto). Su valor cambia con el tiempo,
  porque uno de los datos que usa el modelo es el número de días que lleva vigente la póliza.
- `alto_riesgo` es `true` cuando el puntaje supera el umbral configurado (0,6 por defecto).
- Cada cálculo se registra en `/predicciones`.
- Si la póliza no existe, la respuesta tiene código **404**.

### 8.10 `GET /predicciones` — Historial de puntajes

```json
[{"id": 1, "poliza_id": 1, "numero": "POL-2026-09001", "puntaje": 0.5123245652797518,
  "alto_riesgo": false, "creado_en": "2026-10-08T17:13:22.856927"}]
```

`creado_en` corresponde a la fecha y hora del cálculo.

### 8.11 Información que el servicio no expone

Cada póliza almacena internamente una firma (`token_firma`) calculada con la clave secreta. Es
un dato de uso interno y **no se incluye en ninguna respuesta**: cada ruta declara de forma
explícita los campos que puede devolver.

## 9. Códigos de estado HTTP

| Código | Significado | Situación en la que aparece |
|---|---|---|
| **200** | Petición exitosa | Consultas y actualizaciones correctas |
| **201** | Registro creado | Al registrar una póliza o declarar un siniestro |
| **404** | Registro no encontrado | La póliza solicitada no existe |
| **409** | Conflicto | Ya existe una póliza con ese número |
| **422** | Datos no válidos | Falta un campo, una fecha es incorrecta, un monto es negativo, etc. La respuesta indica el campo y el motivo |
| **500** | Error interno | No debería ocurrir. Si ocurre, revise los mensajes de la terminal donde se ejecuta el servicio o `docker logs polizas` |

## 10. Configuración

El servicio lee su configuración de **variables de entorno** o, en su defecto, del archivo
`.env` ubicado en la carpeta del proyecto. De este modo, los datos sensibles no quedan escritos
en el código.

| Variable | Descripción | Valor de ejemplo |
|---|---|---|
| `DATABASE_URL` | Ubicación de la base de datos | `sqlite:///app.db` |
| `SECRETO_FIRMA` | Clave secreta con la que se firma cada póliza | Generar una propia ([sección 3](#3-aviso-de-seguridad)) |
| `CLAVE_API_REASEGURO` | Clave del servicio del reasegurador | Generar una propia |
| `RUTA_MODELO` | Archivo del modelo de riesgo | `modelo.pkl` |
| `UMBRAL_ALTO_RIESGO` | Puntaje a partir del cual una póliza es de alto riesgo | `0.6` |

Consideraciones:

- `.env.example` es la plantilla con valores de ejemplo y **sí** se publica en GitHub.
- `.env` contiene los valores reales y **nunca** se publica: el archivo `.gitignore` lo impide.
  No lo comparta por mensajería ni en capturas de pantalla.
- Si faltan `SECRETO_FIRMA` o `CLAVE_API_REASEGURO`, el servicio no inicia y muestra el error.
  Este comportamiento es intencional: es preferible que no inicie a que funcione con una clave
  inventada.

## 11. Pruebas automatizadas

El proyecto incluye pruebas que verifican automáticamente el comportamiento del servicio. Para
ejecutarlas, con el entorno virtual activado (sección 5, paso 3):

```bash
pytest
```

El resultado esperado es **`39 passed`**. Las pruebas se organizan en tres archivos:

| Archivo | Contenido |
|---|---|
| `tests/test_contrato.py` | Contrato definido por el docente (12 pruebas). No se modifica. |
| `tests/test_api.py` | Pruebas propias del grupo (7 pruebas). |
| `tests/test_ia_corregido.py` | Batería de pruebas generada por una IA, corregida por el grupo (20 pruebas). |

Cada prueba utiliza una base de datos **temporal** propia: las pruebas nunca modifican `app.db`
y pueden ejecutarse cuantas veces se desee.

## 12. Estructura del proyecto

| Archivo o carpeta | Contenido |
|---|---|
| `main.py` | Rutas del servicio y lógica de cada petición. |
| `esquemas.py` | Reglas de validación de los datos de entrada y campos de las respuestas. |
| `modelos.py` | Tablas de la base de datos: pólizas, siniestros y predicciones. |
| `database.py` | Conexión a la base de datos; abre una sesión independiente por cada petición. |
| `config.py` | Lectura de la configuración desde `.env`. |
| `alembic/`, `alembic.ini` | Migraciones que crean las tablas. |
| `modelo.pkl` | Modelo de riesgo previamente entrenado. |
| `requirements.txt` | Librerías necesarias, con su versión exacta. |
| `.env.example` | Plantilla de configuración con valores de ejemplo. |
| `Dockerfile`, `.dockerignore` | Instrucciones para construir la imagen de Docker y archivos excluidos de ella. |
| `tests/` | Pruebas automatizadas. |
| `sembrar_datos.py` | Registra pólizas de ejemplo a través del servicio. |
| `contar_consultas.py` | Mide el número de consultas a la base de datos de cada ruta y genera `CONSULTAS.csv`. El grupo lo modificó para registrar también la estrategia de carga usada en `main.py`. |
| `verificar_entrega.py` | Verificación de la entrega, provista por el docente. |
| `ia_tests_propuesta.py` | Pruebas originales generadas por una IA, sin modificar (objeto de la auditoría). |
| `HALLAZGOS.md` | Los 14 defectos encontrados en la versión original, con su evidencia, y el análisis de consultas. |
| `CONSULTAS.csv` | Mediciones de consultas con 10 y 2000 pólizas. |
| `DICTAMEN_IA.md` | Auditoría de las pruebas generadas por la IA. |
| `BITACORA_IA.md` | Registro del uso de IA durante el taller: propuestas aceptadas y rechazadas. |
| `EQUIPO.md` | Integrantes del grupo. |
| `ENUNCIADO.md`, `plantillas/` | Enunciado del taller y plantillas, provistos por el docente. |

## 13. Solución de problemas

**`python` no se reconoce, o se abre la Microsoft Store (Windows).**
Python no quedó registrado en el sistema. Pruebe con `py` en lugar de `python`, o reinstale
Python marcando **"Add python.exe to PATH"**.

**"La ejecución de scripts está deshabilitada en este sistema" al activar el entorno (Windows).**
Es una protección de PowerShell. Ejecute una sola vez el siguiente comando, responda **S** y
vuelva a activar el entorno:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**`ModuleNotFoundError` al iniciar el servicio o ejecutar las pruebas.**
El entorno virtual no está activado (la línea no empieza con `(.venv)`) o no se ejecutó
`pip install -r requirements.txt`.

**`no such table: polizas`.**
Las tablas no se han creado. Ejecute `alembic upgrade head` (sección 5, paso 6).

**"Address already in use": el puerto 8000 está ocupado.**
Otro programa usa el puerto 8000, por ejemplo otra terminal con `uvicorn` o un contenedor.
Deténgalo (**Ctrl + C** o `docker rm -f polizas`), o use otro puerto, por ejemplo
`uvicorn main:app --port 8001`, y abra `http://localhost:8001/docs`.

**`sembrar_datos.py` falla con el código `409`.**
Las pólizas de ejemplo ya existen en la base de datos. Para empezar de nuevo: detenga el
servicio, elimine el archivo `app.db`, ejecute `alembic upgrade head`, inicie el servicio y
vuelva a cargar los datos.

**Windows no permite eliminar o reemplazar `app.db`.**
El servicio mantiene el archivo abierto. Deténgalo primero con **Ctrl + C**.

**`curl` produce resultados inesperados en PowerShell.**
En PowerShell, `curl` corresponde a otro programa. Use Git Bash o la página `/docs`.

**Docker Desktop muestra "Virtualization support not detected" (Windows).**
Abra el Administrador de tareas (**Ctrl + Shift + Esc**) → **Rendimiento** → **CPU** y revise
el campo **Virtualización**. Si indica *Habilitado*, ejecute `wsl --install --no-distribution`
en PowerShell como administrador y reinicie el computador. Si indica *Deshabilitado*, debe
activarse en la configuración del equipo (BIOS o UEFI).

**El contenedor no responde en `localhost:8000`.**
Espere unos 30 segundos después de `docker run` y revise el estado con `docker ps` y los mensajes
con `docker logs polizas`.

## 14. Antecedentes del proyecto

El proyecto parte del repositorio entregado por el docente, `polizas-api-v0` (etiqueta
`v0-semilla`). Esa versión funcionaba, pero contenía defectos intencionales: claves escritas en
el código, una única conexión a la base de datos compartida por todas las peticiones (un error
de un cliente dejaba el servicio fuera de servicio para todos), códigos de respuesta incorrectos,
un campo interno visible en las respuestas, validaciones que no se aplicaban y un `Dockerfile`
que no respondía fuera del contenedor, entre otros. Los 14 defectos, su evidencia y su
corrección se documentan en `HALLAZGOS.md`; cada corrección corresponde a un commit del
historial del repositorio.
