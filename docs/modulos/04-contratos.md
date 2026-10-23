# Módulo 4. Contratos

Estado: **backend implementado y probado; pendiente de tu verificación y aprobación.** Solo
backend.
Fecha: diseño e implementación 2026-10-23, tras las decisiones de Maryam (al final).

Cubre: RF-08, RF-09, RF-10, RN-02, RN-04 a RN-12, y los criterios CA-01 a CA-04. Completa
la ocupación del módulo 2 (RF-05) y el rechazo por bloqueo del módulo 3 (RF-07). Se apoya
en los módulos 1 a 3.

---

## 1. Objetivo y alcance

Registrar los contratos que unen un residente con un apartaestudio y llevar su ciclo de vida
(por iniciar, vigente, vencido, en terminación, terminado, anulado), con las reglas que
impiden contratos incompatibles. Con esto la ocupación de cada apartaestudio pasa a ser real.

**Incluye**
- Crear, consultar, listar con filtros y editar contratos (solo mientras no tengan cobros).
- Prorrogar, renovar, terminar y anular.
- Historial de cada contrato.
- Contratos de un apartaestudio y de un residente.
- Ocupación real en apartaestudios, y contratos actuales en el detalle del residente.
- Rechazar contratos de personas bloqueadas (CA-03) y sobre apartaestudios ocupados o
  reservados (CA-01, CA-02).
- Auditoría de todo lo anterior.

**No incluye (queda para el módulo que lo necesita)**

| Qué | Módulo |
|---|---|
| Anular los cobros posteriores a la entrega al terminar (CA-15) | 5 Cobros |
| Bloquear la edición cuando ya hay cobros: aquí la función existe, pero responde "no tiene cobros" hasta que existan | 5 Cobros |
| `GET /contratos/{id}/estado-de-cuenta` y `POST /contratos/{id}/devolver-saldo` | 6 Pagos y cartera |
| Pasar el saldo a favor al contrato nuevo al renovar | 6 Pagos y cartera |
| Canon vigente con incrementos (aquí el canon vigente es el inicial) | 7 Incrementos |
| Alerta diaria de contratos vencidos | 9 Tablero y alertas |
| Pantallas | Frontend |

---

## 2. Criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| C-01 | Ambos roles crean un contrato con apartaestudio, residente, fechas de inicio y terminación, canon y porcentaje de incremento pactado | RF-08 |
| C-02 | La terminación debe ser posterior al inicio; el inicio no puede ser anterior a hoy (D-1); el canon es un entero en pesos mayor que cero; el porcentaje está entre 0 y 100 con hasta dos decimales (422) | RN-08 |
| C-03 | **CA-01**: un contrato sobre un apartaestudio con otro por iniciar, vigente, vencido o en terminación se rechaza (409) y no guarda nada | RF-09, RN-04 |
| C-04 | **CA-02**: un contrato que inicia el mismo día de la entrega del anterior se rechaza; el que inicia al día siguiente se acepta | RN-05 |
| C-05 | **CA-03**: un contrato o una renovación para una persona con bloqueo activo se rechaza (409), también si el bloqueo llega al mismo tiempo | RF-07, RN-07 |
| C-06 | Dos contratos simultáneos sobre el mismo apartaestudio: uno se guarda y el otro responde 409 | RF-09 |
| C-07 | Una persona puede tener contratos en varios apartaestudios a la vez | RN-06 |
| C-08 | No se aceptan contratos sobre apartaestudios inactivos. Un apartaestudio en mantenimiento sí acepta contrato | RN-03 |
| C-09 | El estado del contrato se calcula con la fecha de hoy en Bogotá; nadie lo elige a mano | Sección 8 de la propuesta |
| C-10 | **CA-04**: el apartaestudio aparece Ocupado si y solo si tiene hoy un contrato vigente, vencido o en terminación, en el detalle, en la lista y en el filtro | RF-05, RN-02 |
| C-11 | Prorrogar extiende la terminación del mismo contrato; un contrato vencido que se prorroga vuelve a vigente | RN-11 |
| C-12 | Renovar cierra el contrato y crea uno nuevo enlazado, sin hueco ni traslape de períodos | RN-11 |
| C-13 | Terminar registra fecha de aviso, fecha de entrega y motivo. El contrato queda en terminación hasta la entrega y terminado desde el día siguiente | RN-12 |
| C-14 | Solo el administrador anula, y solo contratos por iniciar, con motivo. Un empleado recibe 403 | Anexo A.3 |
| C-15 | Un contrato con cobros no se edita (409). Se prueba con el módulo 5 | RN-09 |
| C-16 | No se puede desactivar un apartaestudio con un contrato por iniciar, vigente, vencido o en terminación (409) | RP-07 |
| C-17 | El historial muestra cada cambio del contrato con autor y fecha | RF-10 |
| C-18 | Cada operación marcada con "Audita" deja su registro, y todos los endpoints nuevos entran en la prueba de permisos | RF-23, RNF-03 |

---

## 3. Reglas de negocio

| ID | Regla |
|---|---|
| RC-01 | El estado no se guarda: se calcula con la fecha de hoy en Bogotá, en la misma consulta que lo lee. Así nunca se desincroniza y no depende de un proceso nocturno |
| RC-02 | Estados, en este orden de prioridad: **Anulado** (tiene anulación) · **Renovado** (ya empezó el contrato que lo renueva) · **Terminado** (hoy es posterior a la entrega) · **En terminación** (tiene aviso registrado y la entrega es hoy o futura) · **Por iniciar** (hoy es anterior al inicio) · **Vencido** (hoy es posterior a la terminación) · **Vigente** (el resto) |
| RC-03 | Ocupado = existe un contrato del apartaestudio vigente, vencido o en terminación hoy. Reemplaza la función que hoy responde siempre "libre" |
| RC-04 | Cada contrato reserva su apartaestudio desde el inicio hasta el fin de su ocupación: la entrega, el día anterior al contrato que lo renueva o, si no tiene ninguno de los dos, sin fin. La base de datos impide que dos reservas del mismo apartaestudio se crucen (restricción de exclusión con `btree_gist`, ya instalada). Esto cumple RN-04 y RN-05 aun con peticiones simultáneas; los contratos anulados no reservan |
| RC-05 | Antes de guardar, el servicio verifica en este orden: apartaestudio existe y está activo, residente existe, persona sin bloqueo activo, sin cruce de reservas. Bloquea la fila del apartaestudio y luego el documento del residente, siempre en ese orden |
| RC-06 | El día de corte es el día del inicio (RN-13). Los aniversarios se cuentan desde el inicio, aunque haya prórrogas (RN-29). Un 29 de febrero cae el 28 en años no bisiestos |
| RC-07 | **Editar** (fechas, canon, porcentaje y notas) solo si el contrato no tiene cobros y no está anulado, terminado ni renovado. El apartaestudio y el residente no se cambian: se anula y se crea otro |
| RC-08 | **Prorrogar**: contratos vigentes o vencidos que no tengan una renovación registrada. La nueva terminación debe ser posterior a la actual y no anterior a hoy. Se permite aunque la persona tenga bloqueo (RN-07 solo impide contratos nuevos y renovaciones) |
| RC-09 | **Renovar**: contratos vigentes o vencidos, sin bloqueo activo de la persona y una sola vez por contrato (salvo que la renovación se anule). El nuevo contrato toma el mismo apartaestudio y residente, con nueva terminación, canon (por defecto, el vigente) y porcentaje. Su inicio lo calcula el sistema según D-2 |
| RC-10 | **Terminar**: contratos vigentes o vencidos sin renovación registrada, o en terminación, con fecha de aviso (no futura), fecha de entrega (no anterior al inicio) y motivo. Según D-3, mientras la entrega no haya pasado se puede registrar de nuevo para corregir la fecha |
| RC-11 | **Anular**: solo el administrador, solo contratos por iniciar, con motivo. El contrato sigue visible como anulado. Si era una renovación, el contrato anterior vuelve a quedar sin fin de reserva y se puede renovar de nuevo |
| RC-12 | Nada se borra. Las prórrogas se guardan además como filas propias (fecha anterior, fecha nueva, autor, momento) y salen en el detalle. El historial es la auditoría del contrato, que registra cada operación, prórrogas incluidas |

---

## 4. Cambios en el modelo de datos

Migración `0006_contratos` (nueva). El rol de la aplicación no puede borrar en las dos tablas.

**`contratos`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| apartaestudio_id, residente_id | BIGINT FK | índices |
| fecha_inicio, fecha_terminacion | DATE | `CHECK` terminación > inicio |
| canon_inicial | NUMERIC(14,0) | tipo `Dinero`; `CHECK` > 0 |
| porcentaje_incremento | NUMERIC(5,2) | `CHECK` entre 0 y 100 |
| notas | TEXT | opcional |
| contrato_anterior_id | BIGINT FK `contratos` | enlace de renovación; índice único parcial sin los anulados: un contrato tiene a lo sumo una renovación válida |
| fecha_aviso, fecha_entrega, motivo_terminacion, terminacion_registrada_por_id | DATE, DATE, VARCHAR(500), BIGINT FK | `CHECK` los cuatro juntos o ninguno |
| anulado_en, anulado_por_id, motivo_anulacion | TIMESTAMPTZ, BIGINT FK, VARCHAR(500) | `CHECK` los tres juntos o ninguno |
| fin_reserva | DATE | nulo = sin fin. La mantiene el servicio (entrega o día anterior a la renovación) |

`CHECK` adicionales: la entrega y el fin de reserva no son anteriores al inicio.
| creado_por_id, creado_en, actualizado_en | | |

Restricción de exclusión:
`EXCLUDE USING gist (apartaestudio_id WITH =, daterange(fecha_inicio, fin_reserva, '[]') WITH &&) WHERE (anulado_en IS NULL)`.

**`prorrogas`**: id, contrato_id, terminacion_anterior, terminacion_nueva, registrada_por_id,
registrada_en.

**Cambios en módulos anteriores**
- `inmuebles/repositorio.ocupado(hoy)` pasa a ser un `EXISTS` sobre los contratos (RC-03).
- `apartaestudios.desactivar` rechaza si hay un contrato que reserva el apartaestudio hoy o
  más adelante (C-16).
- El detalle del residente agrega sus contratos actuales.

---

## 5. Endpoints y permisos

Todos bajo `/api/v1`; los que modifican exigen `X-CSRF-Token`.

| Método | Ruta | Rol | Audita | Descripción |
|---|---|---|---|---|
| GET | /contratos | Ambos | No | Lista con filtros por estado, propietario, apartaestudio y residente |
| POST | /contratos | Ambos | Sí | Crea un contrato tras validar bloqueo, ocupación y fechas |
| GET | /contratos/{id} | Ambos | No | Detalle con estado, canon vigente, próximo corte, próximo aniversario y contratos enlazados |
| PATCH | /contratos/{id} | Ambos | Sí | Edita mientras no tenga cobros (RC-07) |
| POST | /contratos/{id}/prorrogar | Ambos | Sí | Extiende la terminación |
| POST | /contratos/{id}/renovar | Ambos | Sí | Cierra el contrato y crea el nuevo enlazado |
| POST | /contratos/{id}/terminar | Ambos | Sí | Registra aviso, entrega y motivo |
| POST | /contratos/{id}/anular | Admin | Sí | Anula un contrato por iniciar, con motivo |
| GET | /contratos/{id}/historial | Ambos | No | Cambios del contrato con autor y fecha |
| GET | /apartaestudios/{id}/contratos | Ambos | No | Contratos del apartaestudio, del más reciente al más antiguo |
| GET | /residentes/{id}/contratos | Ambos | No | Contratos del residente |

Son 11 de las 13 rutas del anexo A.3 para contratos y las dos del anexo A.2 que esperaban
este módulo. Los errores de regla responden 409 con un código propio:
`apartaestudio_reservado`, `apartaestudio_inactivo`, `persona_bloqueada`,
`estado_no_permite`, `ya_renovado` y `tiene_cobros`.

**Concurrencia.** Crear y renovar bloquean la fila del apartaestudio y después el documento del
residente, el mismo bloqueo que usa `POST /bloqueos`. Si dos peticiones cruzan reservas a pesar
de eso, la restricción de exclusión responde por la base de datos. Prorrogar, terminar, editar
y anular bloquean la fila del contrato.

---

## 6. Archivos creados o modificados

**Nuevos**
- `app/modulos/contratos/`:
  - `estados.py`: reglas de fechas sin base de datos (estado, cortes, aniversarios, inicio de la
    renovación);
  - `consultas.py`: las mismas reglas de estado y ocupación como expresiones SQL, que usa también
    el módulo de inmuebles;
  - `modelos.py`, `esquemas.py`, `repositorio.py`, `servicio.py`, `router.py`.
- `alembic/versions/0006_contratos.py`
- `tests/unit/test_estados_contrato.py`
- `tests/integration/test_contratos.py`, `test_ciclo_contrato.py`,
  `test_concurrencia_contratos.py`, `ayudas_contratos.py`

**Modificados**
- `app/modulos/inmuebles/repositorio.py` y `apartaestudios.py`: ocupación real y desactivación
  protegida (C-16).
- `app/modulos/residentes/esquemas.py` y `router.py`: contratos actuales en el detalle.
- `app/modulos/auditoria/`: consulta del historial de una entidad, con su autor.
- `app/db/modelos.py`, `app/db/permisos.py`, `app/api/router.py`.
- `tests/integration/test_permisos.py` y `test_permisos_bd.py`; `tests/conftest.py` (ver nota).
- `docs/trazabilidad.md`.

**Nota: corrección en módulos anteriores.** Al probar el cruce de contratos se encontró que el
"punto de guardado" que usaban los módulos 1 a 3 para detectar duplicados no hacía nada:
SQLAlchemy escribe los cambios pendientes antes de abrirlo. Para el usuario no cambiaba nada,
porque la petición respondía el mismo 409 y terminaba sin confirmar. Se quitó, se corrigieron los
comentarios que lo describían, y la sesión compartida de las pruebas ahora se revierte también
cuando una petición termina en error.

---

## 7. Implementación por etapas

| Etapa | Contenido |
|---|---|
| 1 | Reglas de fechas (`estados.py`) con sus pruebas unitarias |
| 2 | Migración 0006, modelos y restricción de exclusión |
| 3 | Crear, consultar, listar y editar, con las validaciones de RC-05 |
| 4 | Ocupación real, desactivación protegida, contratos en apartaestudio y residente |
| 5 | Prorrogar, renovar, terminar, anular e historial |
| 6 | Permisos, concurrencia y documentación |

---

## 8. Pruebas y resultados

Ejecutadas el 2026-10-23 en el entorno de desarrollo de Claude (Linux, Python 3.13,
PostgreSQL 16), dos corridas completas seguidas. **Todavía no se han ejecutado en tu
computador.**

| Archivo | Pruebas | Criterios | Resultado |
|---|---|---|---|
| `unit/test_estados_contrato.py` | 33 | Cada estado en sus días límite; cortes en días 29, 30, 31 y en 29 de febrero (incluye el ejemplo de CA-05); aniversarios; inicio de la renovación (D-2) | 33 aprobadas |
| `integration/test_contratos.py` | 25 | C-01 a C-04 (CA-01 a CA-04), C-07, C-08, C-14 a C-16, C-18; D-1 | 25 aprobadas |
| `integration/test_ciclo_contrato.py` | 16 | C-09, C-11 a C-13, C-17; CA-03 en la renovación; D-2 a D-4; estado en SQL igual al de Python durante 47 días seguidos | 16 aprobadas |
| `integration/test_concurrencia_contratos.py` | 5 | C-06 en paralelo; la restricción de exclusión como respaldo; contrato y bloqueo simultáneos (C-05); renovación y contrato nuevo simultáneos | 5 aprobadas |
| `integration/test_permisos.py` | 4 | C-18: los 11 endpoints nuevos con cada rol y sin sesión | 4 aprobadas |
| `integration/test_permisos_bd.py` | 21 | El rol de la aplicación no puede borrar contratos ni prórrogas | 21 aprobadas |
| Módulos 1 a 3 y estructura base | 187 | Sin cambios de comportamiento | 187 aprobadas |
| **Total** | **291** | | **291 aprobadas, 0 fallidas** |

`ruff check` y `ruff format --check`: sin hallazgos. La migración 0006 se aplicó, se revirtió y se
volvió a aplicar, y `alembic check` no encontró diferencias con los modelos.

Para confirmar que las pruebas de concurrencia detectan errores reales, se cambió el código a
propósito y se revirtió después:

| Cambio a propósito | Resultado |
|---|---|
| Quitar la restricción de exclusión | Falla la prueba de respaldo; la de C-06 sigue pasando gracias al bloqueo del apartaestudio |
| Quitar además el bloqueo del apartaestudio | Falla la prueba de C-06 |
| Quitar el bloqueo del documento en `exigir_sin_bloqueo` | Falla la prueba de contrato y bloqueo simultáneos |

C-15 (un contrato con cobros no se edita) se probó simulando que el contrato tiene cobros; la
prueba real llega con el módulo 5.

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Contratos superpuestos por peticiones simultáneas | Bloqueo de la fila del apartaestudio y restricción de exclusión en la base de datos |
| Estado desincronizado con las fechas | El estado se calcula al consultar (RC-01); no se guarda |
| Renovación que cobra dos veces o deja un hueco | El sistema calcula el inicio de la renovación (D-2), y la restricción de exclusión impide el traslape |
| Prórroga legal automática (Ley 820, art. 6) | El sistema no prorroga solo: marca Vencido, sigue reservando el apartaestudio y la alerta llega con el módulo 9 (tablero) |

Sin dependencias nuevas.

---

## 10. Lista de verificación de finalización

- [x] Migración 0006 aplicada y reversible
- [x] Criterios C-01 a C-18 cubiertos por pruebas ejecutadas y aprobadas (C-15 con cobros
  simulados; la prueba real llega con el módulo 5)
- [x] Pruebas de concurrencia comprobadas quitando su bloqueo
- [x] Prueba de permisos ampliada con los endpoints nuevos
- [x] Ruff sin hallazgos
- [x] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam
- [ ] Aprobación de Maryam

---

## Decisiones tomadas (2026-10-23)

Maryam eligió la recomendación en 2, 3 y 4, y no en 1.

| ID | Pregunta | Decisión |
|---|---|---|
| D-1 | ¿Se pueden registrar contratos con fecha de inicio pasada, para cargar los arriendos que ya existen? | **No.** El inicio no puede ser anterior a hoy, al crear ni al editar |
| D-2 | ¿Cuándo empieza el contrato renovado? | Lo calcula el sistema: el día en que empezaría el siguiente período del contrato anterior después de su terminación, o después de hoy si ya está vencido |
| D-3 | Si el residente cambia la fecha de entrega, ¿se puede corregir? | Sí, registrando la terminación de nuevo mientras la entrega no haya pasado; ambas quedan en el historial |
| D-4 | En un contrato renovado, ¿los aniversarios se cuentan desde el inicio del contrato nuevo? | Sí. Las prórrogas siguen contando desde el inicio original |
