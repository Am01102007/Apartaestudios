# Módulo 3. Residentes y bloqueos

Estado: **backend implementado y probado; pendiente de tu verificación y aprobación.** Solo
backend.
Fecha: diseño 2026-10-19; implementación 2026-10-22, tras las decisiones de Maryam (al final).

Cubre: RF-06, RF-07 y la parte de RN-07 que no depende de los contratos ("todo bloqueo y
levantamiento registra motivo, fecha y responsable"). Se apoya en los módulos 1 y 2.

---

## 1. Objetivo y alcance

Tener el directorio de las personas que arriendan y la lista de personas que no pueden firmar
contratos nuevos, con su historial completo. El módulo de contratos usará los dos.

**Incluye**
- Crear, consultar, buscar y editar residentes.
- Bloquear una persona por su documento, con motivo, y levantar el bloqueo con motivo.
- Consultar los bloqueos activos o históricos y verificar si un documento está bloqueado.
- Ver en el detalle de un residente si tiene un bloqueo activo.
- Auditoría de todo lo anterior.

**No incluye**
- `GET /residentes/{id}/contratos` y los contratos en el detalle: llegan con el módulo de contratos.
- Impedir contratos a personas bloqueadas (CA-03): se aplica y prueba en el módulo de contratos,
  que usará la función de verificación de este módulo.
- Política de tratamiento de datos (Ley 1581): sigue pendiente antes de producción.
- Pantallas: etapa de frontend.

---

## 2. Requisitos y criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| R-01 | El administrador registra un residente con nombre, documento y teléfono; un empleado recibe 403 | RF-06 |
| R-02 | No se pueden registrar dos residentes con el mismo tipo y número de documento, aunque cambie el formato (409) | RF-06 |
| R-03 | El directorio busca por nombre o documento; ambos roles pueden consultarlo | RF-06 |
| R-04 | El detalle de un residente indica si tiene un bloqueo activo | RF-06, RF-07 |
| R-05 | Bloquear exige motivo; guarda fecha, hora y responsable | RF-07, RN-07 |
| R-06 | No puede haber dos bloqueos activos para el mismo documento (409), tampoco si llegan a la vez | RF-07 |
| R-07 | Levantar exige motivo; guarda fecha, hora y responsable, y el bloqueo sigue visible como levantado | RF-07, RN-07 |
| R-08 | Un bloqueo levantado no se puede levantar otra vez (409); la persona sí se puede volver a bloquear | RF-07 |
| R-09 | `GET /bloqueos/verificar` responde si un documento tiene bloqueo activo, aunque la persona no sea residente | RF-07 |
| R-10 | Ningún bloqueo se borra ni se edita; ningún endpoint lo permite y el rol de la aplicación no puede borrarlo en la base | RF-07 |
| R-11 | Según D-3, el empleado ve que un documento está bloqueado, pero no el motivo | RNF-16 |
| R-12 | Cada operación marcada con "Audita" deja su registro | RF-23 |
| R-13 | Todos los endpoints nuevos entran en la prueba automática de permisos | RNF-03, CA-16 |

---

## 3. Reglas de negocio

| ID | Regla |
|---|---|
| RR-01 | El documento del residente sigue el mismo formato y normalización de los propietarios (RP-02). Tipo + número es único entre residentes |
| RR-02 | Los residentes no se borran. No tienen estado activo: "residente actual" se calculará a partir de sus contratos, como la ocupación |
| RR-03 | Un bloqueo se aplica a un **documento** (tipo + número), no a un registro de residente. Así se puede bloquear a alguien que nunca ha sido residente (D-2) y el bloqueo sigue vigente aunque se cree su registro después |
| RR-04 | Como máximo un bloqueo activo por documento. Lo garantiza un índice único parcial en la base de datos |
| RR-05 | Bloquear y levantar registran motivo (3 a 500 caracteres), momento y responsable. Un bloqueo nunca se borra ni se edita: el historial es la lista de bloqueos de ese documento |
| RR-06 | Solo el administrador bloquea y levanta. Ambos roles consultan (propuesta, sección 4) |

---

## 4. Cambios en el modelo de datos

Migración `0005_residentes_bloqueos` (nueva). Otorga permisos con `sql_permisos`. El rol de la
aplicación puede leer, insertar y actualizar (levantar) bloqueos, pero no borrarlos: el borrado
solo se otorga en `sesiones`.

**`residentes`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| nombre | VARCHAR(150) | obligatorio |
| tipo_documento, numero_documento | VARCHAR(5), VARCHAR(20) | como en `propietarios`; `UNIQUE` el par |
| telefono | VARCHAR(20) | obligatorio (D-1) |
| correo | VARCHAR(254) | opcional |
| contacto_emergencia_nombre, contacto_emergencia_telefono | VARCHAR(150), VARCHAR(20) | opcionales; si hay uno, el otro es obligatorio |
| notas | TEXT | opcional, máximo 1000 caracteres |
| creado_en, actualizado_en | TIMESTAMPTZ | |

**`bloqueos`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| tipo_documento, numero_documento | VARCHAR(5), VARCHAR(20) | normalizados; índice |
| nombre | VARCHAR(150) | obligatorio: nombre de la persona al bloquearla (la pantalla lo propondrá desde el registro del residente) |
| motivo | VARCHAR(500) | obligatorio |
| bloqueado_en, bloqueado_por_id | TIMESTAMPTZ, BIGINT FK `usuarios` | |
| levantado_en, levantado_por_id, motivo_levantamiento | TIMESTAMPTZ, BIGINT FK, VARCHAR(500) | nulos mientras está activo; `CHECK`: los tres juntos o ninguno |

Índice único parcial `(tipo_documento, numero_documento) WHERE levantado_en IS NULL` (RR-04).

**Cambio interno:** el tipo de documento y su normalización pasan de `inmuebles` a
`app/core/documentos.py`; la base de los esquemas de entrada y los tipos comunes (teléfono,
correo, documento) a `app/core/entradas.py`; y la búsqueda sin comodines a
`app/db/consultas.py`. Así propietarios, residentes y bloqueos usan exactamente las mismas
reglas. No cambia ningún comportamiento ni dato: las 168 pruebas anteriores siguen pasando.

---

## 5. Endpoints y permisos

Todos bajo `/api/v1`; los que modifican exigen `X-CSRF-Token`.

| Método | Ruta | Rol | Audita | Descripción |
|---|---|---|---|---|
| GET | /residentes | Ambos | No | Directorio con búsqueda por nombre o documento |
| POST | /residentes | Admin | Sí | Registra un residente |
| GET | /residentes/{id} | Ambos | No | Detalle con su bloqueo activo, si tiene (los contratos se añaden con su módulo) |
| PATCH | /residentes/{id} | Admin | Sí | Edita datos de un residente |
| GET | /bloqueos | Ambos | No | Bloqueos activos, levantados o todos; búsqueda por nombre o documento |
| GET | /bloqueos/verificar | Ambos | No | `?tipo_documento=CC&numero_documento=...` → si tiene bloqueo activo y desde cuándo |
| POST | /bloqueos | Admin | Sí | Bloquea un documento con motivo |
| POST | /bloqueos/{id}/levantar | Admin | Sí | Levanta un bloqueo con motivo |

Son las rutas del anexo A.2 de la propuesta, salvo `GET /residentes/{id}/contratos`, que se
implementa con los contratos.

**Concurrencia.** Bloquear toma un bloqueo de PostgreSQL sobre el documento
(`pg_advisory_xact_lock`) hasta el fin de la transacción; si aun así dos bloqueos llegaran a la
vez, el índice único parcial detiene al segundo (409). Levantar bloquea la fila del bloqueo.
`exigir_sin_bloqueo`, que usará el módulo de contratos, toma el mismo bloqueo del documento:
si alguien está bloqueando a esa persona, la verificación espera y luego ve el bloqueo (base de
CA-03; el caso completo con contratos se prueba en ese módulo).

---

## 6. Archivos creados o modificados

**Nuevos**

| Archivo | Propósito |
|---|---|
| `app/core/documentos.py` | Tipo de documento, normalización y regla de solo dígitos (CC y NIT) |
| `app/core/entradas.py` | Base de los esquemas de entrada y tipos comunes |
| `app/db/consultas.py` | Búsqueda de texto literal (`%` y `_` no actúan como comodines) |
| `app/modulos/residentes/{modelos,esquemas,repositorio,servicio,router}.py` | Directorio de residentes |
| `app/modulos/bloqueos/{modelos,esquemas,repositorio,servicio,router}.py` | Bloqueos; `servicio.exigir_sin_bloqueo(...)` es lo que usará el módulo de contratos |
| `alembic/versions/0005_residentes_bloqueos.py` | Tablas, índice único parcial y permisos |
| `tests/integration/test_{residentes,bloqueos,concurrencia_bloqueos}.py`, `ayudas_personas.py`, `conftest.py` | Pruebas y fijaciones comunes |

**Modificados**: `app/modulos/inmuebles/*` (usa los módulos comunes), `app/api/router.py`,
`app/db/modelos.py`, `tests/integration/ayudas.py` (`en_paralelo`),
`tests/integration/test_permisos.py` y `test_permisos_bd.py`, README, `docs/trazabilidad.md`.

Aquí sí son dos dominios: los residentes consultan los bloqueos, pero los bloqueos no
necesitan a los residentes salvo para tomar el nombre, que se recibe como dato.

---

## 7. Implementación por etapas

| Etapa | Estado |
|---|---|
| 1. Mover documentos a `core`, migración 0005 y modelos | Hecha |
| 2. Residentes: servicio, endpoints y auditoría | Hecha |
| 3. Bloqueos: bloquear, levantar, listar y verificar | Hecha |
| 4. Detalle del residente con bloqueo activo; ocultar el motivo al empleado (D-3) | Hecha |
| 5. Pruebas de permisos, concurrencia y documentación | Hecha |
| 6. Pantallas | Aplazada a la etapa de frontend |

---

## 8. Pruebas y resultados

Ejecutadas el 2026-10-22 en el entorno de desarrollo de Claude (Linux, Python 3.13,
PostgreSQL 16). **Todavía no se han ejecutado en tu computador.**

| Archivo | Pruebas | Criterios | Resultado |
|---|---|---|---|
| `integration/test_residentes.py` | 15 | R-01 a R-04, R-12; contacto de emergencia completo | 15 aprobadas |
| `integration/test_bloqueos.py` | 15 | R-05 a R-12; `exigir_sin_bloqueo` | 15 aprobadas |
| `integration/test_concurrencia_bloqueos.py` | 3 | R-06 en paralelo; el índice único como respaldo; la verificación espera a un bloqueo en curso | 3 aprobadas |
| `integration/test_permisos.py` | 4 | R-13 (los 8 endpoints nuevos con cada rol y sin sesión) | 4 aprobadas |
| `integration/test_permisos_bd.py` | 16 | R-10: el rol de la aplicación no puede borrar bloqueos, residentes, propietarios ni apartaestudios | 16 aprobadas |
| Módulos 1 y 2 y estructura base | 154 | Sin cambios de comportamiento tras mover los documentos a `core` | 154 aprobadas |
| **Total** | **207** | | **207 aprobadas, 0 fallidas** |

`ruff check` y `ruff format --check`: sin hallazgos. La migración 0005 se aplicó, se revirtió y
se volvió a aplicar en una base aparte, y `alembic check` no encontró diferencias con los modelos.

Para confirmar que la prueba de espera detecta un error real, se quitó a propósito el bloqueo del
documento en `exigir_sin_bloqueo`: la prueba falló. El cambio se revirtió.

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Lista de personas bloqueadas (Ley 1581: finalidad, autorización, rectificación) | Motivo obligatorio, historial sin borrado, solo el administrador bloquea, motivo oculto al empleado (D-3). La política formal sigue pendiente antes de producción |
| Un documento mal escrito al bloquear no protege nada | La verificación usa la misma normalización; si se escribió mal, se levanta con ese motivo y se bloquea el documento correcto, y ambos quedan en el historial |

Sin dependencias nuevas.

---

## 10. Lista de verificación de finalización

- [x] Migración 0005 aplicada y reversible
- [x] Criterios R-01 a R-13 cubiertos por pruebas ejecutadas y aprobadas
- [x] Prueba de permisos ampliada con los endpoints nuevos
- [x] Ruff sin hallazgos
- [x] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam
- [ ] Aprobación de Maryam

---

## Decisiones tomadas (2026-10-22)

Maryam respondió "1 si 2 si 3 no lo ve": las tres recomendaciones.

| ID | Pregunta | Decisión |
|---|---|---|
| D-1 | ¿Datos del residente: nombre, documento y teléfono obligatorios; correo, contacto de emergencia (nombre y teléfono) y notas opcionales? | Sí |
| D-2 | ¿Se puede bloquear un documento aunque esa persona nunca haya sido residente (por ejemplo, alguien que dejó deudas en otro lugar)? | Sí: el bloqueo es por documento |
| D-3 | ¿El empleado ve el motivo de los bloqueos? La propuesta le permite consultar los bloqueos; el motivo es un dato personal sensible | El empleado ve que existe el bloqueo y desde cuándo, pero no el motivo |
