# TaxFlow Mobile: propuesta DynamoDB para pruebas

**Sustituida para el MVP académico de tres usuarios por el modelo mínimo de una tabla sin GSI
en [integracion-android.md](integracion-android.md).** Se conserva como historial exploratorio;
no desplegar sus dos tablas ni sus índices.

Fecha: 2026-10-14. Estado: propuesta exploratoria pendiente de revisión del repositorio Android y aprobación; no desplegada.
Decisiones posteriores confirmadas: varios usuarios, sin sincronización offline inicial;
no desarrollar Lambda ni crear tablas antes de acordar requisitos y contrato API.
La revisión se rige por [requerimientos-backend.md](requerimientos-backend.md).
El nombre TaxFlow Mobile procede del adjunto; confirmar si sustituye el nombre inicial Test Flow.

## Evidencia y alcance

Se revisaron el texto adjunto y los textos/relaciones del SVG mermaid-diagram.svg.
Ambos describen diez entidades relacionales. El modelo Room incluido es parcial y no demuestra
que la aplicación ya implemente autenticación, endpoints o sincronización.
Consulta AWS de solo lectura: perfil test-flow-academy, cuenta 325875101955, rol voclabs,
región us-east-1. STS correcto; ListTables devuelve lista vacía.
Esto confirma acceso de lectura, no autorización CreateTable ni disponibilidad del backend.

## Tablas físicas propuestas

1. `test-flow-dev-data`: perfil y datos privados del usuario; PK y SK String.
2. `test-flow-dev-reference`: catálogos y reglas por ejercicio; PK y SK String.

Propuesta para ambas: DynamoDB Standard, PAY_PER_REQUEST, cifrado administrado por AWS,
sin clave KMS propia, sin Streams, sin tablas globales, sin TTL para documentos fiscales.
Un GSI en data: `by-user-date`, GSI1PK String, GSI1SK String, Projection KEYS_ONLY.
Después de Query al índice, BatchGetItem recupera los documentos; conservar el orden del índice
al ensamblar la respuesta y reintentar UnprocessedKeys. No proyectar perfiles ni RUC en este GSI.
reference no necesita GSI para las consultas conocidas.
PITR/respaldos de pago no activados en la propuesta de laboratorio con datos sintéticos;
se deberá aprobar otra política antes de almacenar datos reales. No habilitar backups silenciosamente.

## Mapeo de las diez entidades

U representa un id interno estable vinculado a una identidad autenticada. No usar RUC/DNI/email
como id del usuario o derivar U de un parámetro móvil sin verificar su autorización.

| Entidad del adjunto | Tabla | PK | SK |
|---|---|---|---|
| usuarios | data | USER#U | PROFILE |
| comprobantes_ingresos | data | USER#U | INCOME#UUID |
| comprobantes_gastos | data | USER#U | EXPENSE#UUID |
| balances_anuales | data | USER#U | BALANCE#AAAA |
| obligaciones_usuario | data | USER#U | OBLIGATION#periodo#tipo |
| suspensiones_retencion | data | USER#U | SUSPENSION#AAAA#UUID |
| notificaciones | data | USER#U | NOTIFICATION#UUID |
| configuracion_tributaria | reference | TAX#AAAA | CONFIG |
| categorias_gastos_deducibles | reference | TAX#AAAA | CATEGORY#codigo |
| cronograma_sunat_maestro | reference | CALENDAR#AAAA#digito#tipo | periodo |

Se conservan los atributos de negocio del adjunto como atributos de documentos, con estas
modificaciones explícitas:
- No incluir password_hash hasta seleccionar autenticación. Preferir proveedor JWT externo o
  Cognito si el laboratorio y la app lo permiten. La tabla no implementa login por sí misma.
- categoria_id pasa a categoria_codigo estable. Conservar legacy_categoria_id si Room lo necesita.
  El porcentaje del catálogo se versiona por ejercicio; cada gasto conserva el aplicado.
- Obligaciones incluyen clave de referencia del cronograma, fecha_vencimiento y UUID lógico
  si el cliente lo requiere. Una obligación por usuario/periodo/tipo; confirmar excepciones.
- Balances conservan UUID lógico si hace falta, pero su clave impone uno por usuario/año.
- Dinero en céntimos enteros Number; porcentajes en puntos básicos enteros Number (8% = 800).
  Evitar Double de Room para dinero. Definir transformación del DTO antes de integrar la app.
- Fechas ISO YYYY-MM-DD; timestamps UTC ISO 8601; documentos RUC/DNI String para preservar ceros.
- Campos opcionales pueden omitirse; no usar string vacío para claves. Añadir moneda PEN
  cuando corresponda; no mezclar importes USD sin conversión definida.
- Versionado: schema_version, version, created_at, updated_at, deleted_at cuando corresponda.
  Registro fuente y version de regla en cálculos; no dar por validado SUNAT un registro manual.

## Patrones de acceso y claves del índice

| Consulta | Operación / clave |
|---|---|
| Perfil propio | GetItem USER#U / PROFILE |
| Documento por UUID | GetItem USER#U / INCOME#UUID o EXPENSE#UUID |
| Ingresos por emisión y rango | Query GSI1PK=USER#U#INCOME, GSI1SK=YYYY-MM-DD#UUID |
| Gastos por emisión y rango | Query GSI1PK=USER#U#EXPENSE, GSI1SK=YYYY-MM-DD#UUID |
| Dashboard de un año | GetItem USER#U / BALANCE#AAAA |
| Obligaciones por vencimiento | Query GSI1PK=USER#U#OBLIGATION, GSI1SK=fecha_vencimiento#periodo#tipo |
| Notificaciones recientes | Query GSI1PK=USER#U#NOTIFICATION, GSI1SK=timestamp#UUID |
| Suspensiones de un año | Query tabla USER#U, begins_with(SK,SUSPENSION#AAAA#) |
| Configuración anual | GetItem TAX#AAAA / CONFIG |
| Categorías de un año | Query TAX#AAAA, begins_with(SK,CATEGORY#) |
| Cronograma por dígito y tipo | Query CALENDAR#AAAA#digito#tipo, rango de periodo |

Todas las listas paginan LastEvaluatedKey mediante cursor opaco y ligado al usuario/filtros.
Usar ScanIndexForward=false para listados recientes. Los límites se aplican a elementos evaluados,
no a coincidencias de filtros. No implementar un Scan global para búsquedas de un usuario.
El índice tiene consistencia eventual: devolver el documento escrito en la respuesta y usar
GetItem consistente para verificación inmediata. No calcular saldos leyendo un GSI recién actualizado.

Gastos por categoría, ingresos por estado de pago, notificaciones no leídas y búsquedas de texto
no están resueltos eficientemente por el GSI propuesto. Antes de desplegar, confirmar si son filtros
indispensables o locales sobre listas pequeñas y acotadas. Añadir un índice o una vista materializada
solo si el patrón lo requiere. No afirmar que esta propuesta cubre aún todos los filtros de la app.

## Integridad y cálculos

DynamoDB no aplica las FK, UNIQUE, CHECK ni GENERATED del SQL. El backend deberá validarlos.
Las claves impiden duplicar usuario/año para balances y periodo/tipo para obligaciones.
Para recibos únicos, usar un ítem de reserva en la misma tabla:
PK=USER#U, SK=UNIQUE#INCOME#serie#correlativo, owner_id=UUID.
Crearlo con condición attribute_not_exists y TransactWriteItems junto con el recibo.
Al cambiar serie/correlativo, liberar la reserva antigua verificando owner_id y crear la nueva
en la misma transacción. No asumir que un GSI impone unicidad.
Unicidad de RUC/email requiere reservas globales y normalización si se confirma ese requisito;
el email de autenticación debe administrarse primero mediante el proveedor elegido.

Las modificaciones usan version esperada y ConditionExpression para evitar sobrescrituras.
La eliminación de un usuario no tiene cascada automática: necesita procedimiento paginado explícito.
El balance es un resultado derivado. Al modificar pagos/gastos se deben actualizar documentos,
resumen de bases de cálculo y balance en una transacción con control optimista, o acordar un
recalculador con estado pendiente visible. No basta sumar montos: deducciones topadas, tramos,
reversiones y cambios de año deben recalcularse con entradas completas y reglas versionadas.
El criterio fiscal por fecha de cobro frente a fecha de emisión, pagos parciales, rentas mixtas
4ta/5ta y excepciones por profesión/actividad quedan pendientes de especificación.
No cargar balances precalculados del prototipo como verdad fiscal.

Offline, si se requiere: idempotency_key estable por operación, conflictos por version, tombstones,
retención y feed ordenado de cambios con cursor definido; updated_at por sí solo no basta.
El índice by-user-date no es un feed de sincronización. Esta parte no está aprobada ni implementada.

## Correcciones fiscales necesarias antes de seed

El adjunto usa UIT 2026=5150 y límites derivados 36050/15450. La fuente oficial consultada indica
UIT 2026=5500, por tanto 7 UIT=38500 y 3 UIT=16500. SUNAT indica límite anual general de suspensión
2026=48125, con casos de dietas/directores y similares diferentes; el adjunto usa 45063.
El umbral por recibo y el umbral mensual son conceptos separados y deben tener atributos distintos.
No cargar tasas, reglas de retención, calendario, suspensión ni requisitos de bancarización sin
verificar el ejercicio y sus condiciones. Marcar ejemplos como sintéticos, no oficialmente validados.

Fuentes:
- https://elperuano.pe/noticia/285208-mef-establece-en-s-5-500-la-unidad-impositiva-tributaria-para-2026
- https://personas.sunat.gob.pe/trabajador-independiente/declaracion-pago
- https://personas.sunat.gob.pe/trabajador-independiente/que-pasa-si

## Integración y permisos del laboratorio

La app consume HTTPS API -> backend -> DynamoDB. No entregar credenciales Academy al APK.
Crear tablas vacías no crea endpoints, autenticación, sincronización ni emisión real de RHE.
El backend y su lenguaje se seleccionan con el usuario; no se asume que Kotlin/Room del ejemplo
corresponde a la app implementada. No manejar Clave SOL ni implementar integración SUNAT aquí.
El rol voclabs seguirá siendo el de desarrollo. No crear usuarios ni roles ni ampliar políticas.
Si después hace falta Lambda, verificar primero un rol de ejecución existente permitido y PassRole;
no asumir que LabRole existe o que sirve para cualquier servicio.

## Alcance propuesto para un primer despliegue posterior

Dos tablas y un GSI, cuenta 325875101955, us-east-1, perfil test-flow-academy.
Sin usuarios, políticas, funciones, API, Cognito, buckets, semillas ni servicios adicionales.
Una plantilla versionada se preparará tras aprobar el modelo. SAM admite recursos CloudFormation
de DynamoDB; preferir un stack solo de tablas si CloudFormation está permitido por el laboratorio.
Si no, acordar una ruta versionada con CLI antes de ejecutarla; no sortear restricciones.

Permisos de gestión a verificar: CreateTable/DescribeTable/DescribeTimeToLive/DescribeContinuousBackups,
TagResource si hay etiquetas, y las acciones CloudFormation necesarias para la ruta aprobada.
No se ha probado ninguno de los permisos de escritura. No usar CreateTable como prueba de permiso.
Runtime futuro: GetItem, BatchGetItem, Query y escrituras/transacciones solo en estas tablas e índice
según casos de uso aprobados. No acceso general a DynamoDB.

Facturación: lecturas, escrituras, almacenamiento y GSI; transacciones y lecturas de documentos
tras el índice incrementan consumo. Respaldos/PITR también tienen costo si se activan posteriormente.
No se promete cobertura gratuita. Verificar saldo del laboratorio y estimar con cantidad de usuarios,
tamaño de documentos y operaciones. Referencia: https://aws.amazon.com/dynamodb/pricing/

Validación posterior: estado ACTIVE, claves/índice y modo de capacidad correctos; escribir y consultar
datos sintéticos solo con aprobación de esa prueba, comprobar duplicados/aislamiento/conflictos con
el backend cuando exista. La integración completa requerirá autenticación y endpoints aparte.
Retirada posterior: borrar exclusivamente el stack/tablas creadas en esta prueba tras aprobación,
considerando exportación previa de datos; nunca eliminar recursos ajenos o de producción.

## Decisiones pendientes solicitadas al usuario

Autenticación actual, lenguaje real de la app y URLs/backend; usuarios ficticios y volumen;
sincronización offline inicial; filtros imprescindibles; aprobación del modelo y de los recursos.

Referencias DynamoDB:
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/data-modeling.html
- https://docs.aws.amazon.com/us_en/amazondynamodb/latest/developerguide/data-modeling-blocks.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html
