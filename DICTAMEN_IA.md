# Dictamen sobre `ia_tests_propuesta.py` — Parte D

**Grupo:** DA8A · **Integrantes:** Nicole López, Luna Pico

> Las tres mutaciones se aplicaron una a la vez sobre el servicio corregido (commit `2daadf3`),
> se ejecutaron ambas baterías y se deshicieron con `git restore` antes de seguir. Las salidas
> son las de nuestra terminal (Windows, PowerShell). La batería corregida está en
> `tests/test_ia_corregido.py` y sobre el servicio sano da `20 passed`.

## Defecto 1

- **Qué está mal**: hay tests que no pueden fallar. `test_crear_poliza_responde` y `test_primas_variadas_son_aceptadas` aceptan `status_code in (200, 201, 422)`, `test_consultar_poliza_inexistente` acepta `in (200, 404)` y `test_listar_polizas_no_falla` solo pide `< 500`. Aceptan a la vez la respuesta correcta y las incorrectas, así que el test queda en verde aunque la API vuelva a responder 200 al crear (H3) o 200 ante una póliza inexistente (H2).
- **Por qué es un defecto** (módulo · sección): M10 · 4. Framework pytest — una aserción solo verifica algo si existe un resultado que la haga fallar; una aserción que admite el código correcto y los incorrectos no distingue un servicio sano de uno roto.
- **Cómo lo comprobamos**: mutación en `main.py`: la creación vuelve a responder 200 en lugar de 201. La batería original sigue en verde; la corregida falla en los 12 tests que crean pólizas y esperan 201.

```diff
-@app.post("/polizas", response_model=PolizaSalida, status_code=201)
+@app.post("/polizas", response_model=PolizaSalida)
 def crear_poliza(datos: PolizaEntrada, db: Session = Depends(get_db),
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest ia_tests_propuesta.py -q --no-header -p no:warnings
......                                                                                                  [100%]
6 passed in 9.26s
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest tests/test_ia_corregido.py -q --no-header -p no:warnings --tb=no -rf
F..F...FFFFFFFFF.F..                                                                                    [100%]
========================================== short test summary info ===========================================
FAILED tests/test_ia_corregido.py::test_crear_poliza_responde_201_y_se_puede_leer - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_numero_duplicado_da_409 - AssertionError: assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[1-auto] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[1-hogar] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[1-vida] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[2500000-auto] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[2500000-hogar] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[2500000-vida] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-auto] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-hogar] - assert 200 ==201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-vida] - assert 200 == 201
FAILED tests/test_ia_corregido.py::test_score_de_poliza_recien_creada_queda_registrado - AssertionError: assert 200 == 201
12 failed, 8 passed in 7.27s
```

- **Corrección**: cada test exige un único resultado (`== 201` al crear, `== 404` si no existe, `== 409` si el número se repite, `== 422` con fechas invertidas o prima no positiva) y además revisa el contenido: lo creado se vuelve a leer con `GET /polizas/{id}` y `GET /polizas` devuelve exactamente las pólizas creadas, en orden.

## Defecto 2

- **Qué está mal**: hay tests que no prueban lo que dicen probar. (a) El bloque «Aislamiento de la base de datos» sustituye con `dependency_overrides` una función `get_db` definida en el propio archivo de tests, que la aplicación nunca usa; la dependencia real, `database.get_db`, queda intacta, de modo que las pruebas escriben en `app.db` aunque el comentario afirme lo contrario. (b) `test_score_de_poliza_recien_creada` dice probar la puntuación, pero acepta una respuesta con `"error"` y nunca comprueba que la predicción quede registrada.
- **Por qué es un defecto** (módulo · sección): M8 · 4. Inyección de dependencias con Depends — `app.dependency_overrides` se indexa por la función de dependencia original; sustituir otra función con el mismo nombre no cambia nada. Y M10 · 5. TestClient de FastAPI — un test de un endpoint debe comprobar su efecto, no solo que responde.
- **Cómo lo comprobamos**: primero, contando las pólizas de `app.db` antes y después de cada batería: la original añadió 7 pólizas a la base real (de 19 a 26) y la corregida ninguna (sigue en 26). Después, la mutación: `/score` calcula y responde el puntaje pero deja de guardar la predicción. El test original sigue en verde; el corregido falla porque `/predicciones` queda vacía.

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> python -c "import sqlite3; print(sqlite3.connect('app.db').execute('select count(*) from polizas').fetchone()[0])"
19
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest ia_tests_propuesta.py -q --no-header -p no:warnings
......                                                                                                  [100%]
6 passed in 5.74s
(.venv) PS C:\Users\vanel\proyectos\polizas-api> python -c "import sqlite3; print(sqlite3.connect('app.db').execute('select count(*) from polizas').fetchone()[0])"
26
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest tests/test_ia_corregido.py -q --no-header -p no:warnings
....................                                                                                    [100%]
20 passed in 9.15s
(.venv) PS C:\Users\vanel\proyectos\polizas-api> python -c "import sqlite3; print(sqlite3.connect('app.db').execute('select count(*) from polizas').fetchone()[0])"
26
```

```diff
     prediccion = Prediccion(poliza_id=poliza.id, puntaje=puntaje,
                             alto_riesgo=puntaje > settings.umbral_alto_riesgo)
-    db.add(prediccion)
-    db.commit()
     return {"numero": poliza.numero, "puntaje": round(puntaje, 4),
             "alto_riesgo": prediccion.alto_riesgo}
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest ia_tests_propuesta.py -q --no-header -p no:warnings -k score
.                                                                                                       [100%]
1 passed, 5 deselected in 6.33s
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest tests/test_ia_corregido.py -q --no-header -p no:warnings --tb=no -rf
.................F..                                                                                    [100%]
========================================== short test summary info ===========================================
FAILED tests/test_ia_corregido.py::test_score_de_poliza_recien_creada_queda_registrado - AssertionError: assert [] == ['POL-IA-000001']
1 failed, 19 passed in 7.47s
```

- **Corrección**: el fixture `cliente` sustituye `database.get_db`, la dependencia que la aplicación usa de verdad, por una sesión sobre una base SQLite temporal y vacía para cada test (con `PRAGMA foreign_keys=ON`), y la retira al terminar. `test_las_pruebas_no_tocan_app_db` comprueba que `app.db` no cambia. El test de score exige 200, que no haya `"error"`, que el puntaje esté entre 0 y 1 y que `/predicciones` contenga exactamente la predicción con el número de la póliza.

## Defecto 3

- **Qué está mal**: hay tests que unas veces pasan y otras no. `_poliza()` elige el tipo con `random.choice` y la prima con `random.uniform(1, 5_000_000)` sin fijar semilla: cada corrida prueba datos distintos, y cuando el servicio trata mal un rango de valores el test falla solo si le toca uno de ellos. El fallo no se puede reproducir, y como no queda registro del valor usado, tampoco se puede diagnosticar.
- **Por qué es un defecto** (módulo · sección): M10 · 7. Reproducibilidad sin Docker — un resultado de pruebas debe repetirse igual con el mismo código; si depende del azar de la corrida, ni el verde ni el rojo dicen nada sobre el servicio.
- **Cómo lo comprobamos**: mutación en `esquemas.py`: un validador que rechaza primas mayores de 2.500.000, límite que no existe en el negocio. Ejecutamos la batería original ocho veces seguidas con el mismo código: seis en verde y dos en rojo, siempre en `test_score_de_poliza_recien_creada` (la póliza aleatoria quedó por encima del límite, se rechazó con 422 y el score respondió 404); `test_primas_variadas_son_aceptadas` nunca falla porque acepta el 422. La corregida falla de forma determinista en los tres casos con prima 4.999.999,99.

```diff
     tipo: str = Field(description="auto, hogar o vida")
-    prima: float = Field(gt=0, description="Prima anual, en pesos")
+    prima: float = Field(gt=0, le=2_500_000, description="Prima anual, en pesos")
     fecha_inicio: date
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> 1..8 | ForEach-Object { pytest ia_tests_propuesta.py -q --no-header -p no:warnings --tb=no -rf | Select-String "FAILED|passed" }

6 passed in 7.02s
FAILED ia_tests_propuesta.py::test_score_de_poliza_recien_creada - assert 404...
1 failed, 5 passed in 5.61s
6 passed in 6.47s
6 passed in 5.88s
6 passed in 5.51s
6 passed in 5.35s
FAILED ia_tests_propuesta.py::test_score_de_poliza_recien_creada - assert 404...
1 failed, 5 passed in 5.37s
6 passed in 5.51s
```

```
(.venv) PS C:\Users\vanel\proyectos\polizas-api> pytest tests/test_ia_corregido.py -q --no-header -p no:warnings --tb=no -rf
========================================== short test summary info ===========================================
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-auto] - assert 422 == 201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-hogar] - assert 422 ==201
FAILED tests/test_ia_corregido.py::test_primas_y_tipos_validos_son_aceptados[4999999.99-vida] - assert 422 == 201
3 failed, 17 passed in 7.74s
```

- **Corrección**: se eliminan `random` y los datos aleatorios. La variedad que buscaba la IA se conserva con casos fijos y explícitos: `pytest.mark.parametrize` combina los tres tipos (`auto`, `hogar`, `vida`) con primas de 1, 2.500.000 y 4.999.999,99, incluidos los extremos del rango que usaba la IA, y cada caso exige 201 y que la respuesta conserve el tipo y la prima. El número de póliza también es fijo, porque cada test tiene su propia base vacía y ya no hay colisiones que evitar. Si un caso falla, su nombre dice qué valor lo provocó.
