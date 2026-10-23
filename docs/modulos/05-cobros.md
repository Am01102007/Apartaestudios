# Módulo 5. Cobros

Estado: **diseño; pendiente de tu aprobación antes de escribir código.** Solo backend.
Fecha: 2026-10-23.

Cubre: RF-13, la parte de RF-16 y RF-17 que no depende de los pagos, RN-13 a RN-19, RN-23 y
RN-24 para cobros, RNF-07 para la generación, y los criterios CA-05, CA-06, CA-07 y CA-15. Se
apoya en el módulo 4 (contratos).

---

## 1. Objetivo y alcance

Generar cada mes, sin intervención y sin duplicados, el cobro del canon de cada contrato el día
de su corte, y saber en todo momento qué cobros están pendientes, pagados o en mora y con
cuántos días de atraso.

**Incluye**
- Generación diaria de los cobros del día, automática y también manual para el administrador.
- Consulta de cobros con filtros, y su detalle con ajustes.
- Ajustes y anulación de cobros, con motivo, solo por el administrador.
- Al terminar un contrato, anular los cobros de períodos que empiezan después de la entrega
  (CA-15).
- Un contrato con cobros ya no se edita (C-15 del módulo 4, ahora con cobros reales).
- Auditoría de todo lo anterior.

**No incluye (queda para el módulo que lo necesita)**

| Qué | Módulo |
|---|---|
| Pagos y abonos, saldo a favor y su aplicación al siguiente cobro (RN-20 a RN-22) | 6 Pagos y cartera |
| Pasar a saldo a favor lo pagado de un cobro que se anula (RN-19, RN-24) | 6 Pagos y cartera |
| Canon con incremento: aquí el valor del cobro es el canon vigente, que hoy es el inicial | 7 Incrementos |
| Alerta en pantalla de los cobros del día (RN-16) | 9 Tablero y alertas |
| Programar el proceso diario en el servidor | Fase 10, despliegue |

---

## 2. Criterios de aceptación

| ID | Criterio | Cubre |
|---|---|---|
| K-01 | El día de corte de un contrato vigente, vencido o en terminación se genera su cobro, con el período (inicio y fin), la fecha de corte y el valor del canon vigente | RF-13, RN-13, RN-16 |
| K-02 | **CA-05**: para un contrato iniciado el 31 de enero, los cortes de febrero, marzo y abril caen el 28 (o 29) de febrero, el 31 de marzo y el 30 de abril | RN-15 |
| K-03 | **CA-06**: ejecutar la generación dos veces, o en paralelo, deja un solo cobro por contrato y período | RF-13, RNF-07 |
| K-04 | El primer cobro se genera el día de inicio del contrato (cobro anticipado), y no hay prorrateo: cada cobro es por el canon completo | RN-13, RN-14 |
| K-05 | Un contrato vencido sigue generando cobros; uno por iniciar, terminado, renovado o anulado no genera | RN-10 |
| K-06 | No se generan cobros de períodos que empiezan después de la entrega ni después del cierre por renovación; la renovación cobra desde su propio inicio | RN-11, RN-19 |
| K-07 | **CA-07**: un cobro con saldo aparece en mora desde el día siguiente al corte, en hora de Bogotá, y no antes, con sus días de atraso | RN-17, RN-18 |
| K-08 | **CA-15** (parte de cobros): terminar un contrato anula los cobros de períodos que empiezan después de la entrega y conserva los anteriores con su saldo | RF-10, RN-12, RN-19 |
| K-09 | Saldo = valor + ajustes − pagos aplicados (los pagos llegan con el módulo 6). Un ajuste que deje el saldo negativo se rechaza (409) | RN-23 |
| K-10 | Solo el administrador ajusta y anula, siempre con motivo. Un cobro no se edita ni se borra: el anulado sigue visible como anulado | RN-24, RNF-09 |
| K-11 | Un contrato con cobros no se edita (409) | RN-09 |
| K-12 | Si un día no corrió la generación, la siguiente ejecución crea los cobros que faltaron, cada uno con su fecha de corte (D-2) | RNF-07 |
| K-13 | Cada operación queda en la auditoría, y todos los endpoints nuevos entran en la prueba de permisos | RF-23, RNF-03 |

---

## 3. Reglas de negocio

| ID | Regla |
|---|---|
| RK-01 | Cada contrato tiene períodos numerados desde 0. El período *n* empieza en su corte (día de inicio del contrato *n* meses después, o el último día del mes si ese día no existe) y termina el día anterior al corte siguiente. Es el cálculo de `estados.inicio_periodo` del módulo 4 |
| RK-02 | Se genera el cobro del período *n* si su corte es hoy o anterior, no es anterior al inicio del contrato, no es posterior al fin de reserva (entrega o cierre por renovación) y el contrato no está anulado |
| RK-03 | Un solo cobro por contrato y período, para siempre: lo garantiza una restricción única en la base de datos, y la generación usa `INSERT … ON CONFLICT DO NOTHING`. Un período con un cobro anulado no se vuelve a generar |
| RK-04 | El valor del cobro se fija al generarlo con el canon vigente y no cambia después. Las correcciones se hacen con ajustes |
| RK-05 | El estado del cobro se calcula, no se guarda: **Anulado**; **Pagado** si el saldo es cero; **En mora** si tiene saldo y hoy es posterior al corte; **Abonado** si tiene pagos y saldo y hoy es el corte; **Pendiente** en otro caso. Días de atraso = hoy − corte, solo en mora |
| RK-06 | Un ajuste tiene valor entero distinto de cero (positivo aumenta la deuda, negativo la reduce) y motivo. No sirve para cargos adicionales (daños o servicios están fuera del alcance) |
| RK-07 | Anular un cobro exige motivo y que no esté ya anulado. Con el módulo 6, lo pagado de ese cobro pasará a saldo a favor |
| RK-08 | Terminar (o corregir la entrega de) un contrato anula, con el motivo "Terminación del contrato", los cobros no anulados cuyo período empieza después de la entrega |

---

## 4. Cambios en el modelo de datos

Migración `0007_cobros` (nueva). El rol de la aplicación no puede borrar en las dos tablas, y
los ajustes son de solo inserción.

**`cobros`**

| Columna | Tipo | Notas |
|---|---|---|
| id | BIGINT identidad | PK |
| contrato_id | BIGINT FK | índice |
| numero_periodo | INTEGER | `CHECK` ≥ 0; `UNIQUE (contrato_id, numero_periodo)` (RK-03) |
| periodo_inicio, periodo_fin | DATE | el corte es `periodo_inicio`; `CHECK` fin ≥ inicio |
| valor | NUMERIC(14,0) | tipo `Dinero`; `CHECK` > 0 |
| generado_en | TIMESTAMPTZ | |
| generado_por_id | BIGINT FK `usuarios`, nulo | nulo = proceso automático |
| anulado_en, anulado_por_id, motivo_anulacion | | `CHECK` los tres juntos o ninguno. Al terminar un contrato, el autor es quien registró la terminación |

**`ajustes_cobro`**: id, cobro_id, valor (NUMERIC(14,0), `CHECK` ≠ 0), motivo, registrado_por_id,
registrado_en.

Índices: `cobros (periodo_inicio)` para la generación y los filtros por vencimiento.

**Cambios en el módulo 4**: `contratos.servicio.tiene_cobros` consulta la tabla real, y
`terminar` llama a la anulación de RK-08.

---

## 5. Endpoints y permisos

Todos bajo `/api/v1`; los que modifican exigen `X-CSRF-Token`.

| Método | Ruta | Rol | Audita | Descripción |
|---|---|---|---|---|
| GET | /cobros | Ambos | No | Lista con filtros por estado, contrato, apartaestudio, propietario y rango de vencimiento |
| GET | /cobros/{id} | Ambos | No | Detalle con estado, saldo, días de atraso y ajustes (los pagos aplicados llegan con el módulo 6) |
| POST | /cobros/{id}/ajustes | Admin | Sí | Registra un ajuste con motivo; el saldo no puede quedar negativo |
| POST | /cobros/{id}/anular | Admin | Sí | Anula un cobro con motivo |
| POST | /cobros/generar | Admin | Sí | Ejecuta la generación del día; nunca duplica. Responde cuántos cobros creó |

Son las 5 rutas de cobros del anexo A.4. Además, el detalle del contrato agrega su lista de
cobros.

**Proceso automático (D-1).** El comando `uv run python -m app.comandos.generar_cobros` hace lo
mismo que `POST /cobros/generar` y es lo que el servidor ejecutará cada día, como ya se hace con
`purgar_sesiones`.

**Concurrencia.** Dos generaciones simultáneas no duplican gracias a la restricción única con
`ON CONFLICT DO NOTHING`. Ajustar y anular bloquean la fila del cobro. Terminar un contrato
bloquea el contrato y después sus cobros, el mismo orden que usa la generación.

---

## 6. Archivos que se crearán o modificarán

**Nuevos**
- `app/modulos/cobros/{modelos,esquemas,estados,repositorio,servicio,router}.py`
  (`estados.py`: estado, saldo y días de atraso sin base de datos)
- `app/comandos/generar_cobros.py`
- `alembic/versions/0007_cobros.py`
- `tests/unit/test_estados_cobro.py`
- `tests/integration/test_cobros.py`, `test_generacion_cobros.py`,
  `test_concurrencia_cobros.py`, `test_comando_generar_cobros.py`

**Modificados**: `app/modulos/contratos/{servicio,esquemas}.py` (cobros en el detalle,
`tiene_cobros`, anulación al terminar), `app/db/{modelos,permisos}.py`, `app/api/router.py`,
`tests/integration/test_permisos.py` y `test_permisos_bd.py`, `test_contratos.py` (C-15 real),
`docs/trazabilidad.md`.

---

## 7. Implementación por etapas

| Etapa | Contenido |
|---|---|
| 1 | Estado, saldo y atraso (`estados.py`) con pruebas unitarias |
| 2 | Migración 0007 y modelos |
| 3 | Generación (servicio, endpoint y comando), con recuperación de días faltantes |
| 4 | Consulta, ajustes y anulación |
| 5 | Conexión con contratos: edición bloqueada y anulación al terminar |
| 6 | Permisos, concurrencia y documentación |

---

## 8. Pruebas previstas

| Archivo | Qué prueba |
|---|---|
| `unit/test_estados_cobro.py` | Cada estado en sus días límite (corte y día siguiente); saldo; días de atraso |
| `integration/test_generacion_cobros.py` | K-01, K-02 (CA-05) recorriendo tres meses, K-04 a K-06, K-12 |
| `integration/test_cobros.py` | K-07 (CA-07), K-08 (CA-15), K-09 a K-11, K-13 |
| `integration/test_concurrencia_cobros.py` | K-03 (CA-06): dos generaciones en paralelo; ajuste y anulación simultáneos del mismo cobro |
| `integration/test_comando_generar_cobros.py` | El comando genera lo mismo que el endpoint y repetirlo no duplica |
| `integration/test_permisos.py`, `test_permisos_bd.py` | K-13 y que el rol de la aplicación no puede borrar cobros ni ajustes |

Como en los módulos anteriores, cada prueba de concurrencia se comprobará quitando la protección
que la hace pasar y viendo que falla.

---

## 9. Riesgos

| Riesgo | Mitigación |
|---|---|
| Cobros duplicados por reintentos o ejecuciones simultáneas | Restricción única por contrato y período; generación idempotente (CA-06) |
| El servidor no corre el proceso un día | La siguiente ejecución recupera los cobros que faltaron (D-2), y el administrador puede ejecutarlo a mano |
| Errores de fechas en meses cortos | Un solo cálculo de cortes (módulo 4), probado con días 29, 30 y 31 (CA-05) |
| Un cobro anulado por error no se puede reactivar | Según D-3, se compensa con un ajuste en el cobro siguiente, con su motivo |

Sin dependencias nuevas.

---

## 10. Lista de verificación de finalización

- [ ] Migración 0007 aplicada y reversible
- [ ] Criterios K-01 a K-13 cubiertos por pruebas ejecutadas y aprobadas
- [ ] Pruebas de concurrencia comprobadas quitando su protección
- [ ] Prueba de permisos ampliada con los endpoints nuevos
- [ ] Ruff sin hallazgos
- [ ] Matriz de trazabilidad actualizada
- [ ] Pruebas ejecutadas en el computador de Maryam
- [ ] Aprobación de Maryam

---

## Decisiones pendientes

| ID | Pregunta | Recomendación |
|---|---|---|
| D-1 | ¿Cómo corre la generación diaria? | Con un comando que el servidor ejecuta cada día a las 00:05 de Bogotá (Programador de tareas de Windows o cron, se configura en el despliegue), más el botón manual del administrador. No agrega librerías. La alternativa, un programador dentro de la API, agrega una dependencia nueva y cambia el stack |
| D-2 | Si un día no corrió la generación, ¿la siguiente ejecución crea los cobros que faltaron? | Sí, cada uno con su propia fecha de corte, así la mora y los días de atraso salen correctos |
| D-3 | Si un cobro se anula por error, ¿cómo se corrige? | No se reactiva: el administrador registra un ajuste positivo en el cobro siguiente, con el motivo. Así nada se borra ni se edita (RNF-09) |
| D-4 | ¿Los ajustes pueden ser positivos (aumentan la deuda) y negativos (descuentos), siempre con motivo? | Sí, sin dejar el saldo negativo. No sirven para cargos adicionales como daños, que están fuera del alcance |
