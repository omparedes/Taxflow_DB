# Despliegue autorizado — Test Flow demo

Fecha: 2026-10-14. Implementación, despliegue y seed remoto autorizados explícitamente por el usuario.
Stack CREATE_COMPLETE; seed cargado y 39 comprobaciones HTTPS correctas. La sección de procedimiento conserva
el plan aprobado; las comprobaciones de recursos constan en recursos-aws.json.

## Destino y recursos

- Cuenta: 325875101955; región us-east-1; perfil test-flow-academy; rol operador voclabs.
- Stack nuevo: test-flow-dev-demo.
- Tabla test-flow-dev-demo: PK/SK String, PAY_PER_REQUEST, sin GSI/Streams/TTL/PITR.
- Lambda test-flow-dev-demo: Python 3.13, 128 MB, timeout 10s, rol existente LabRole.
- HTTP API test-flow-dev-demo, etapa $default, integración Lambda y permiso resource-based
  para invocación desde esta API generados por SAM. Una ruta ANY /v1/demo/{proxy+}; el controlador
  atiende únicamente las nueve operaciones del contrato y devuelve 404 para otras.
- Log group /aws/lambda/test-flow-dev-demo, retención de 7 días. Logs solo request_id,
  status y tipo de excepción; no cuerpos, secretos ni datos personales.
- Bucket nuevo propuesto para artefactos: test-flow-artifacts-325875101955-us-east-1.
  Sin acceso público, cifrado SSE-S3, sin versionado. No reutilizar un bucket con ese nombre
  sin verificar que es propio y pertenece a este proyecto; si el nombre no está disponible,
  acordar otro antes de crear. Bucket queda fuera del stack y se retirará separadamente.
- Seed: 112 ítems (3 perfiles + 90 comprobantes + 9 calendarios + 9 avisos + reglas demo).

No crear usuarios, políticas IAM, roles, Cognito, VPC, NAT, claves KMS propias ni servicios extra.
La API demo no autentica: todos los perfiles son seleccionables por cualquier consumidor.
Throttling propuesto 2 solicitudes/segundo con ráfaga 5; es best effort y no un límite de gasto.
No CORS para Android nativo. URL solo para prueba supervisada, con datos ficticios.

## Permisos y restricciones

Confirmado con consultas: LabRole existe, confía en lambda.amazonaws.com y tiene políticas
administradas por el laboratorio. No se modificó ninguna. Ese rol no es exclusivo de la app
y puede tener permisos más amplios: la plantilla no añade permisos y el código solo lee DynamoDB.
Los nombres de políticas no acreditan permisos efectivos; no afirmar mínimo privilegio de LabRole.

Necesario para el runtime: dynamodb:GetItem/Query en esta tabla y logs:CreateLogStream/PutLogEvents
en este log group. No requiere PutItem/Scan para atender la API.
Operador despliegue: CloudFormation gestión de stack/change set, DynamoDB CreateTable/DescribeTable
y DeleteTable para retirar, Lambda CreateFunction/UpdateFunctionCode/AddPermission y operaciones
de gestión, API Gateway gestión, CloudWatch Logs gestión y S3 artefactos. iam:PassRole debe estar
permitido para LabRole con destino Lambda; no se ha demostrado con una escritura.
Seed requiere GetItem/PutItem exclusivamente en la tabla demo. Ante AccessDenied, informar acción
y detener la parte afectada: no ampliar permisos ni cambiar roles automáticamente.

## Costos

Facturables: DynamoDB lecturas/escrituras/almacenamiento, Lambda invocaciones/duración,
API Gateway solicitudes, CloudWatch Logs ingestión/almacenamiento y S3 artefactos.
No se supone cobertura de capa gratuita ni créditos del laboratorio ilimitados.
El costo dependerá de consultas, tamaño y tiempo de conservación; por ejemplo, 1000 aperturas
del dashboard leen dos colecciones pequeñas cada una, no solo dos ítems. Por eso no equivalen
a 2000 unidades de lectura. Con este dataset el uso previsto es pequeño, pero no se promete cero.
Antes de desplegar confirmar saldo Academy y periodo de prueba; no usar pruebas de carga.
Se recomienda alerta de presupuesto si el curso lo permite, sin habilitarla automáticamente.

Precios oficiales para estimación:
- https://aws.amazon.com/dynamodb/pricing/
- https://aws.amazon.com/lambda/pricing/
- https://aws.amazon.com/api-gateway/pricing/
- https://aws.amazon.com/cloudwatch/pricing/
- https://aws.amazon.com/s3/pricing/

## Validaciones ya realizadas

10 pruebas unitarias correctas; nueve respuestas contra esquemas OpenAPI; seed determinista.
YAML parseado localmente y cloudformation validate-template aceptado por AWS.
AWS reportó CAPABILITY_AUTO_EXPAND para SAM. No se creó change set ni stack.
Validar estructura no prueba permisos de creación, transform completo, IAM runtime ni e2e real.
No está instalado SAM CLI ni boto3 local; no se instalaron herramientas.

## Procedimiento después de aprobación

1. Renovar sesión Academy si expiró; verificar STS, cuenta/rol y región. Confirmar que nombres
   de tabla/función/API/log group/stack/bucket no colisionen con recursos existentes.
2. Ejecutar localmente scripts/prepare_deploy.py; empaquetar build/template.local.yaml.
3. Crear bucket de artefactos propio mediante AWS CLI y aplicar bloqueo público y SSE-S3.
4. `aws cloudformation package --template-file build/template.local.yaml --s3-bucket
   test-flow-artifacts-325875101955-us-east-1 --output-template-file build/template.packaged.yaml
   --profile test-flow-academy --region us-east-1`. Este paso sube el zip a S3.
5. Crear change set mediante cloudformation deploy con plantilla empaquetada, stack
   test-flow-dev-demo, CAPABILITY_AUTO_EXPAND y --no-execute-changeset. Revisar recursos
   transformados y confirmar que no modifica recursos ajenos. Crear change set es una operación
   AWS y requiere la aprobación de este procedimiento; no se ejecutó aún.
6. Presentar diff del change set. Ejecutarlo dentro del alcance aprobado; si añade recursos
   o permisos fuera de esta lista, pedir aprobación del cambio de alcance antes de continuar.
7. Esperar stack listo. Obtener ApiBaseUrl desde Outputs y documentar URL real en OpenAPI/guía.
8. Ejecutar seed: `python scripts/seed_aws.py --confirm LOAD_DEMO_DATA`. Usa AWS CLI, no boto3
   local; verifica cuenta y rol voclabs. Reanudar no sobrescribe ítems distintos. Carga no atómica.
9. Validar tabla ACTIVE y estructura, consultar seed mediante API. No instalar datos en Android.

## Prueba e2e posterior

GET /v1/demo/users devuelve 3 perfiles. Cada lista de ingresos y gastos sin filtros devuelve
15 documentos propios. Probar q por serie/número, cliente, estados y fechas; cada resumen debe
coincidir con su lista. Un id de demo-01 consultado como demo-02 debe dar 404.
POST simulación 350000 céntimos con retención activa devuelve 28000 de retención y 322000 neto;
las consultas antes/después del simulador deben devolver el mismo dataset.
El agente Android consume la URL obtenida y muestra los datos del selector. Solo entonces
puede declararse completado Android -> API Gateway -> Lambda -> DynamoDB.

## Retirada con aprobación separada

Si hace falta conservar el seed, ya es reproducible localmente. No hay datos reales que exportar.
Eliminar exclusivamente stack test-flow-dev-demo tras confirmar cuenta/región y nombres;
la plantilla eliminará tabla/función/API/log group sin retener datos de prueba.
Luego listar objetos del bucket propio, eliminar exclusivamente sus artefactos y borrar el
bucket propuesto. Nunca borrar el stack inicial del Learner Lab ni LabRole.
No hay script de eliminación automática ni se ejecutó ninguna eliminación.


## Resultado ejecutado — 2026-10-14

Usuario autorizó explícitamente el despliegue y carga. No se modificaron IAM roles/políticas.
Change set initial-demo-20261014 revisado: seis recursos nuevos (incluye etapa y permiso
generados por SAM), sin modificaciones a recursos ajenos. Stack CREATE_COMPLETE.
Bucket propio con SSE-S3 y bloqueo de acceso público verificados. Tabla ACTIVE,
PAY_PER_REQUEST, PK/SK y sin GSI; Lambda Active python3.13/128 MB/10s con LabRole;
retención logs 7 días; etapa con throttling 2/s, ráfaga 5.
Seed de 112 ítems cargado correctamente. Runtime GetItem/Query y despliegue PassRole funcionaron
en este alcance; no equivale a un análisis de todos los permisos del laboratorio.
API: https://8cspr7pmca.execute-api.us-east-1.amazonaws.com
39 pruebas HTTPS correctas según validacion-aws.json. Integración Android pendiente.
No se verificó saldo de créditos Academy desde la consola; sigue a cargo del usuario/instructor.
Retirada requiere aprobación separada, no se eliminaron recursos.

## Actualización de autenticación ejecutada

2026-10-14: solicitud de registro/login y cuentas atendida. Stack UPDATE_COMPLETE,
change set auth-accounts-20261014: misma tabla/función/API/rol; nueva ruta /v1/{proxy+} y
permiso de invocación reemplazado por CloudFormation. No IAM roles ni políticas modificados.
Migration actualiza únicamente el dataset/cuentas iniciales. Registro y sesiones escriben en
la misma tabla; LabRole permitió TransactWriteItems, PutItem, DeleteItem, GetItem/Query en estas pruebas.
12 pruebas locales y 47 comprobaciones HTTPS correctas. Contrato vigente v2 con Bearer.
El plan de selector/sin autenticación descrito arriba corresponde al primer despliegue, sustituido
por esta actualización. URL base conservada. Cualquier retirada sigue requiriendo aprobación.
