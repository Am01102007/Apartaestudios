# Módulo 3. Residentes y bloqueos

Estado: **diseño; pendiente de tu aprobación antes de escribir código.** Solo backend.
Fecha: 2026-10-19.

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

Migración `0005_residentes_bloqueos` (nueva). Otorga permisos con `sql_permisos`, y la tabla
`bloqueos` se añade a las de solo inserción y actualización controlada: el rol de la aplicación
no puede borrar bloqueos.

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
| nombre | VARCHAR(150) | nombre de la persona al bloquearla (si es residente, se toma de su registro) |
| motivo | VARCHAR(500) | obligatorio |
| bloqueado_en, bloqueado_por_id | TIMESTAMPTZ, BIGINT FK `usuarios` | |
| levantado_en, levantado_por_id, motivo_levantamiento | TIMESTAMPTZ, BIGINT FK, VARCHAR(500) | nulos mientras está activo; `CHECK`: los tres juntos o ninguno |

Índice único parcial `(tipo_documento, numero_documento) WHERE levantado_en IS NULL` (RR-04).

**Cambio interno:** el tipo de documento y su normalización pasan de `inmuebles` a
`app/core/documentos.py`, para que propietarios, residentes y bloqueos usen exactamente las
mismas reglas. No cambia ningún comportamiento ni dato.

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

**Concurrencia.** Dos bloqueos simultáneos del mismo documento los detiene el índice único
(409). Levantar bloquea la fila del bloqueo. Para CA-03, el módulo de contratos verificará el
bloqueo dentro de su propia transacción con un bloqueo de PostgreSQL sobre el documento, de modo
que un contrato y un bloqueo simultáneos de la misma persona no puedan cruzarse; ese caso se
prueba allá.

---

## 6. Archivos que se crearán o modificarán

**Nuevos**
- `app/core/documentos.py` (tipo de documento y normalización compartidos)
- `app/modulos/residentes/{modelos,esquemas,repositorio,servicio,router}.py`
- `app/modulos/bloqueos/{modelos,esquemas,repositorio,servicio,router}.py`
  (`servicio.bloqueo_activo(...)` es lo que usará el módulo de contratos)
- `alembic/versions/0005_residentes_bloqueos.py`
- `tests/integration/test_residentes.py`, `test_bloqueos.py`, `test_concurrencia_bloqueos.py`

**Modificados**: `app/modulos/inmuebles/*` (usa `core/documentos.py`), `app/db/permisos.py`
(sin borrado en `bloqueos`), `app/api/router.py`, `app/db/modelos.py`,
`tests/integration/test_permisos.py` y `test_permisos_bd.py`, `docs/trazabilidad.md`.

Aquí sí son dos dominios: los residentes consultan los bloqueos, pero los bloqueos no
necesitan a los residentes salvo para tomar el nombre, que se recibe como dato.

---

## 7. Implementación por etapas

| Etapa | Contenido |
|---|---|
| 1 | Mover documentos a `core`, migración 0005 y modelos |
| 2 | Residentes: servicio, endpoints y auditoría |
| 3 | Bloqueos: bloquear, levantar, listar y verificar |
| 4 | Detalle del residente con bloqueo activo; ocultar el motivo al empleado (D-3) |
| 5 | Pruebas de permisos, concurrencia y documentación |

---

## 8. Pruebas previstas

| Archivo | Qué prueba |
|---|---|
| `integration/test_residentes.py` | R-01 a R-04, R-12 |
| `integration/test_bloqueos.py` | R-05 a R-12 |
| `integration/test_concurrencia_bloqueos.py` | Dos bloqueos simultáneos del mismo documento: uno se guarda y el otro responde 409 |
| `integration/test_permisos.py`, `test_permisos_bd.py` | R-13 y R-10 (el rol de la aplicación no puede borrar bloqueos) |

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Lista de personas bloqueadas (Ley 1581: finalidad, autorización, rectificación) | Motivo obligatorio, historial sin borrado, solo el administrador bloquea, motivo oculto al empleado (D-3). La política formal sigue pendiente antes de producción |
| Un documento mal escrito al bloquear no protege nada | La verificación usa la misma normalización; si se escribió mal, se levanta con ese motivo y se bloquea el documento correcto, y ambos quedan en el historial |

Sin dependencias nuevas.

---

## 10. Lista de verificación de finalización

- [ ] Migración 0005 aplicada y reversible
- [ ] Criterios R-01 a R-13 cubiertos por pruebas ejecutadas y aprobadas
- [ ] Prueba de permisos ampliada con los endpoints nuevos
- [ ] Ruff sin hallazgos
- [ ] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam
- [ ] Aprobación de Maryam

---

## Decisiones pendientes

| ID | Pregunta | Recomendación |
|---|---|---|
| D-1 | ¿Datos del residente: nombre, documento y teléfono obligatorios; correo, contacto de emergencia (nombre y teléfono) y notas opcionales? | Sí |
| D-2 | ¿Se puede bloquear un documento aunque esa persona nunca haya sido residente (por ejemplo, alguien que dejó deudas en otro lugar)? | Sí: el bloqueo es por documento |
| D-3 | ¿El empleado ve el motivo de los bloqueos? La propuesta le permite consultar los bloqueos; el motivo es un dato personal sensible | El empleado ve que existe el bloqueo y desde cuándo, pero no el motivo |
