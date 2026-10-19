# Módulo 2. Propietarios y apartaestudios

Estado: **diseño; pendiente de tu aprobación antes de escribir código.** Solo backend, como
en el módulo 1.
Fecha: 2026-10-19.

Cubre: RF-03, RF-04, RF-05, RN-01, RN-02, RN-03 y la parte de CA-04 que no depende de los
contratos. Se apoya en [decisiones-fases-3-a-6.md](../decisiones-fases-3-a-6.md) y en el
módulo 1 (sesión, permisos y auditoría).

---

## 1. Objetivo y alcance

Tener el inventario de apartaestudios y sus dueños, que es la base de residentes, contratos,
cobros e informes. Todo lo que venga después se filtra por propietario (RN-01).

**Incluye**
- Crear, consultar y editar propietarios.
- Crear, consultar y editar apartaestudios, cada uno asociado a un propietario.
- Marca "En mantenimiento" con motivo, que activa y retira el administrador (RN-03).
- Estado Libre u Ocupado **calculado**, nunca editable (RN-02). Ver la sección 3.
- Desactivar y reactivar propietarios y apartaestudios en lugar de borrarlos (ver D-3).
- Auditoría de cada cambio.

**No incluye**
- `GET /apartaestudios/{id}/contratos` (historial de contratos): llega con el módulo de contratos.
- Medidores de agua y energía: van con el módulo de servicios.
- Datos bancarios de los propietarios (no los pide la propuesta y son datos sensibles).
- Pantallas: etapa de frontend.

---

## 2. Requisitos y criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| P-01 | El administrador crea un propietario con nombre y documento; un empleado recibe 403 | RF-03 |
| P-02 | No se pueden registrar dos propietarios con el mismo tipo y número de documento, aunque cambien puntos, espacios o mayúsculas; responde 409 | RF-03 |
| P-03 | `GET /propietarios/{id}` muestra los datos del propietario y la lista de sus apartaestudios | RF-03 |
| P-04 | El administrador crea un apartaestudio con código, dirección y propietario activo; con un propietario inexistente o inactivo responde 409 | RF-03, RF-04, RN-01 |
| P-05 | No se pueden crear dos apartaestudios con el mismo código, aunque cambien mayúsculas o espacios; responde 409 | RF-04 |
| P-06 | Ningún endpoint acepta el estado Ocupado como dato de entrada; enviarlo se rechaza con 422 | RF-05, RN-02 |
| P-07 | La marca de mantenimiento exige motivo, guarda desde cuándo y quién la puso, y se puede retirar; activarla dos veces seguidas responde 409 | RF-05, RN-03 |
| P-08 | La marca de mantenimiento no cambia el estado de ocupación | RN-03 |
| P-09 | `GET /apartaestudios` filtra por propietario, ocupación, mantenimiento, activo y texto (código o dirección) | RF-04, RN-01 |
| P-10 | No se puede desactivar un propietario que tenga apartaestudios activos (409) | D-3 |
| P-11 | Cambiar el propietario de un apartaestudio queda en la auditoría con el anterior y el nuevo | D-4 |
| P-12 | Cada operación de la sección 5 marcada con "Audita" deja su registro | RF-23 |
| P-13 | Todos los endpoints nuevos entran en la prueba automática de permisos por rol | RNF-03, CA-16 |

CA-04 completo ("el estado Ocupado coincide siempre con un contrato vigente, vencido o en
terminación") se prueba en el módulo de contratos, porque necesita contratos reales.

---

## 3. Reglas de negocio

| ID | Regla |
|---|---|
| RP-01 | Cada apartaestudio pertenece a exactamente un propietario (RN-01) |
| RP-02 | Documento del propietario: tipo (`CC`, `CE`, `NIT`, `PA` pasaporte, `PPT`) y número de 3 a 20 letras o dígitos. Se guarda en mayúsculas, sin puntos, espacios ni guiones. El par tipo + número es único |
| RP-03 | Código del apartaestudio: de 1 a 20 caracteres (letras, números, guion y espacio), único sin distinguir mayúsculas; se guarda en mayúsculas y sin espacios repetidos. Ejemplos: `201`, `A-302` |
| RP-04 | **Ocupación (RN-02)**: un apartaestudio está Ocupado si **hoy, en hora de Bogotá**, tiene un contrato en estado vigente, vencido o en terminación; si no, está Libre. Se calcula en cada consulta y no existe ninguna columna que se pueda editar. Hasta que exista el módulo de contratos, todos aparecen como Libre |
| RP-05 | **Mantenimiento (RN-03)**: marca independiente con motivo, fecha de inicio y responsable. Puede coexistir con Ocupado y no impide firmar un contrato. Solo la activa y retira el administrador |
| RP-06 | Propietarios y apartaestudios no se borran: se desactivan y se reactivan, para que los contratos, cobros e informes históricos conserven sus datos (D-3) |
| RP-07 | Un apartaestudio inactivo no admite contratos nuevos (se aplicará en el módulo de contratos). No se podrá desactivar con un contrato por iniciar, vigente, vencido o en terminación |
| RP-08 | Un apartaestudio puede cambiar de propietario (por ejemplo, por venta). Los contratos y cobros guardarán el propietario del momento en que se crearon, así que el historial no se mueve al dueño nuevo (D-4) |

---

## 4. Cambios en el modelo de datos

Migración `0004_propietarios_apartaestudios` (nueva; no toca las anteriores). Al final otorga
los permisos al rol de la aplicación con `sql_permisos`, como la 0003.

**`propietarios`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| nombre | VARCHAR(150) | obligatorio (persona o empresa) |
| tipo_documento | VARCHAR(5) | `CHECK` con los tipos de RP-02 |
| numero_documento | VARCHAR(20) | normalizado; `UNIQUE (tipo_documento, numero_documento)` |
| telefono | VARCHAR(20) | opcional |
| correo | VARCHAR(254) | opcional, en minúsculas |
| direccion | VARCHAR(200) | opcional (de correspondencia) |
| notas | TEXT | opcional, máximo 1000 caracteres |
| activo | BOOLEAN | por defecto verdadero |
| creado_en, actualizado_en | TIMESTAMPTZ | |

**`apartaestudios`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| codigo | VARCHAR(20) | normalizado; único |
| propietario_id | BIGINT | FK a `propietarios`, `ON DELETE RESTRICT`; índice |
| direccion | VARCHAR(200) | obligatoria |
| area_m2 | NUMERIC(6,2) | opcional, mayor que 0 |
| descripcion | TEXT | opcional, máximo 1000 caracteres |
| en_mantenimiento | BOOLEAN | por defecto falso |
| mantenimiento_desde | TIMESTAMPTZ | nulo si no está en mantenimiento |
| mantenimiento_motivo | VARCHAR(300) | ídem |
| mantenimiento_por_id | BIGINT | FK a `usuarios`; ídem |
| activo | BOOLEAN | por defecto verdadero |
| creado_en, actualizado_en | TIMESTAMPTZ | |

`CHECK` de coherencia: si `en_mantenimiento` es verdadero, desde, motivo y responsable son
obligatorios; si es falso, los tres son nulos. Así la base de datos no puede quedar con una
marca a medias. El historial de cuándo se puso y se quitó la marca queda en la auditoría.

No hay columna de ocupación: es RP-04. La función que la calcula vive en el servicio de
apartaestudios, recibe la fecha de hoy en Bogotá y, cuando exista la tabla `contratos`, será
una sola consulta `EXISTS` para toda la lista (sin una consulta por apartaestudio).

---

## 5. Endpoints y permisos

Todos bajo `/api/v1`; los que modifican exigen `X-CSRF-Token`. "Ambos" = administrador y empleado.

| Método | Ruta | Rol | Audita | Descripción |
|---|---|---|---|---|
| GET | /propietarios | Ambos | No | Lista con filtros por activo y texto (nombre o documento) |
| POST | /propietarios | Admin | Sí | Crea un propietario |
| GET | /propietarios/{id} | Ambos | No | Detalle con sus apartaestudios y la ocupación de cada uno |
| PATCH | /propietarios/{id} | Admin | Sí | Edita datos (no el estado activo) |
| POST | /propietarios/{id}/desactivar | Admin | Sí | **Nuevo** (D-3): falla si tiene apartaestudios activos |
| POST | /propietarios/{id}/activar | Admin | Sí | **Nuevo** (D-3) |
| GET | /apartaestudios | Ambos | No | Lista con filtros por propietario, ocupación, mantenimiento, activo y texto |
| POST | /apartaestudios | Admin | Sí | Crea un apartaestudio |
| GET | /apartaestudios/{id} | Ambos | No | Detalle con ocupación calculada y contrato activo (nulo hasta el módulo de contratos) |
| PATCH | /apartaestudios/{id} | Admin | Sí | Edita código, dirección, área, descripción o propietario |
| POST | /apartaestudios/{id}/mantenimiento | Admin | Sí | Activa (`{"activo": true, "motivo": "..."}`) o retira (`{"activo": false, "motivo": "..."}`) la marca |
| POST | /apartaestudios/{id}/desactivar | Admin | Sí | **Nuevo** (D-3) |
| POST | /apartaestudios/{id}/activar | Admin | Sí | **Nuevo** (D-3); exige que su propietario esté activo |

Las rutas que no dicen "Nuevo" son las del anexo A.2 de la propuesta.

**Concurrencia.** Cambios sobre el mismo apartaestudio bloquean su fila. Desactivar un
propietario bloquea su fila y luego, en orden de id, las de sus apartaestudios, para que nadie
active ni cree un apartaestudio suyo al mismo tiempo. Un código o documento duplicado que llega
en paralelo lo detiene la restricción única y responde 409, igual que en el módulo 1.

---

## 6. Archivos que se crearán o modificarán

**Nuevos**
- `app/modulos/propietarios/{modelos,esquemas,repositorio,servicio,router}.py`
- `app/modulos/apartaestudios/{modelos,esquemas,repositorio,servicio,router}.py`
  (`servicio.ocupacion(...)` es el punto que completará el módulo de contratos)
- `alembic/versions/0004_propietarios_apartaestudios.py`
- `tests/integration/test_propietarios.py`, `test_apartaestudios.py`, `test_concurrencia_inmuebles.py`
- `tests/unit/test_normalizacion_inmuebles.py` (documentos y códigos)

**Modificados**: `app/api/router.py`, `app/db/modelos.py`, `tests/integration/test_permisos.py`
(los endpoints nuevos con cada rol), `docs/trazabilidad.md`, este documento.

---

## 7. Implementación por etapas

| Etapa | Contenido |
|---|---|
| 1 | Migración 0004 y modelos |
| 2 | Propietarios: servicio, endpoints y auditoría |
| 3 | Apartaestudios: servicio, endpoints, mantenimiento y ocupación |
| 4 | Desactivar y reactivar, con sus bloqueos de filas |
| 5 | Pruebas de permisos, concurrencia y documentación |

---

## 8. Pruebas previstas

| Archivo | Qué prueba |
|---|---|
| `unit/test_normalizacion_inmuebles.py` | RP-02 y RP-03: `1.234.567` = `1234567`, `a-302 ` = `A-302`, caracteres no válidos |
| `integration/test_propietarios.py` | P-01 a P-03, P-10, P-12 |
| `integration/test_apartaestudios.py` | P-04 a P-09, P-11, P-12 |
| `integration/test_concurrencia_inmuebles.py` | Dos creaciones con el mismo código en paralelo; desactivar un propietario mientras se le crea un apartaestudio |
| `integration/test_permisos.py` | P-13: el empleado recibe 403 en todo lo que es solo de administrador |

Se reporta el resultado real de cada archivo, como en el módulo 1.

---

## 9. Riesgos y dependencias

| Riesgo | Mitigación |
|---|---|
| La ocupación se ve Libre en todos hasta el módulo de contratos | Es lo correcto mientras no haya contratos; la función queda lista para completarse y CA-04 se prueba allá |
| Datos personales de propietarios (Ley 1581) | Solo los mínimos; sin datos bancarios; la política de tratamiento sigue pendiente antes de producción |
| Cambio de propietario mueve informes antiguos | RP-08: contratos y cobros guardan el propietario del momento |

Sin dependencias nuevas.

---

## 10. Lista de verificación de finalización

- [ ] Migración 0004 aplicada y reversible
- [ ] Criterios P-01 a P-13 cubiertos por pruebas ejecutadas y aprobadas
- [ ] Prueba de permisos ampliada con los endpoints nuevos
- [ ] Ruff sin hallazgos
- [ ] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam
- [ ] Aprobación de Maryam

---

## Decisiones pendientes

| ID | Pregunta | Recomendación |
|---|---|---|
| D-1 | ¿Datos del propietario: nombre y documento obligatorios; teléfono, correo, dirección y notas opcionales, sin datos bancarios? | Sí |
| D-2 | ¿Los apartaestudios están en un solo edificio o en varios? Con uno solo, el código basta (`201`); con varios, conviene una tabla de edificios | Sin tabla de edificios: código único y dirección en cada apartaestudio, lo que sirve para ambos casos |
| D-3 | ¿Desactivar y reactivar propietarios y apartaestudios en lugar de borrarlos? Añade cuatro endpoints | Sí, igual que con los usuarios |
| D-4 | ¿Se permite cambiar el propietario de un apartaestudio (venta), conservando el historial con el dueño anterior? | Sí |
