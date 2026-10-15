# Estado de Test Flow

Fecha: 2026-10-13 (America/Lima).

## Alcance

Exclusivamente FASE 0. Diagnóstico local y consultas de solo lectura autorizados.
No instalar automáticamente, cambiar IAM, configurar SSO ni desplegar recursos.
No avanzar a otra fase sin indicación. No crear usuarios ni ampliar permisos en Learner Lab.

## Entorno comprobado

Carpeta inicialmente vacía, sin repositorio Git ni AGENTS.md encontrado.
Windows NT 10.0.26200.0, PowerShell 7.6.5.
AWS CLI y SAM no disponibles en PATH ni rutas habituales comprobadas.
Git 2.51.2.windows.1; Node.js 24.15.0; npm 11.12.1; Python Anaconda 3.13.9.
Launcher py sin instalación registrada; Docker no encontrado en PATH.
En el primer diagnóstico no había config/credentials AWS ni variables AWS en el proceso.
En la segunda comprobación AWS CLI seguía sin estar disponible.

## Decisión actual del usuario

AWS Academy Learner Lab universitario, acceso desde Canvas y Start Lab.
Identidad federada voclabs, permisos restringidos. Credenciales temporales desde AWS Details.
Perfil acordado: test-flow-academy (sustituye test-flow-dev).
No aws login, usuarios IAM nuevos, SSO ni cambios administrativos.

## Pendiente

Usuario instala manualmente AWS CLI v2 y configura las tres credenciales temporales fuera del
repositorio mediante editor local. Debe confirmar la región permitida por su laboratorio.
Luego Codex ejecutará list-profiles, configure get region y STS con el perfil explícito.
Cuenta, identidad, región y permisos aún no verificados; no se ejecutó STS.
Las restricciones exactas de servicios/regiones del curso siguen pendientes.
No se instalaron herramientas, cambiaron configuraciones globales ni crearon recursos AWS.

Guía actual: [fase-0-acceso-aws.md](fase-0-acceso-aws.md).

## Validación completada — 2026-10-14 (America/Lima)

AWS CLI 2.38.0 instalado y disponible mediante su ruta absoluta.
Perfil: test-flow-academy. Región configurada: us-east-1.
STS GetCallerIdentity correcto desde Codex: cuenta 325875101955, rol asumido voclabs, identidad no root.
No se guardaron claves, tokens ni el identificador personal de sesión en esta documentación.

El proceso sandbox usa CodexSandboxOffline y no puede acceder a los archivos config/credentials
bajo C:\Users\Oscar\.aws. La validación funcionó mediante ejecución aprobada fuera del sandbox.
No copiar credenciales al repositorio ni cambiar ACL para resolver esta limitación. Futuras consultas
requieren el mismo mecanismo autorizado mientras persista esa restricción.

FASE 0: acceso autenticado y verificado. STS no acredita permisos para otros servicios o despliegue.
Regiones y servicios permitidos por el curso siguen pendientes de comprobar con las instrucciones
específicas del Learner Lab. No se crearon recursos ni se cambiaron permisos IAM.
Esperar instrucción del usuario antes de FASE 1. Las entradas anteriores describen el historial;
esta validación sustituye el estado previo de conexión pendiente.

## Nuevo alcance — modelo de TaxFlow Mobile (2026-10-14)

Usuario pidió modelar/crear DynamoDB con el diseño remitido por el agente del prototipo.
Se revisaron el adjunto textual y las entidades/relaciones del SVG. Se preparó una propuesta
local en modelo-dynamodb-propuesto.md; no se creó infraestructura ni una plantilla desplegable.
STS sigue correcto; DynamoDB ListTables en us-east-1 devolvió lista vacía.

Propuesta: dos tablas PAY_PER_REQUEST, data y reference, un GSI by-user-date. Pendiente de
aprobar y cerrar filtros, autenticación y sincronización antes de fijar claves e índices.
Se enviaron preguntas al usuario sobre backend/lenguaje/autenticación y usuarios/offline.
No contactar al otro agente sin autorización explícita para mensajearlo.

El adjunto contiene valores fiscales desactualizados: UIT 2026 verificada en fuente oficial
5500, no 5150; límites generales de suspensión también difieren. No se cargaron semillas.
La creación de recursos requiere la presentación y aprobación explícita exigidas en el prompt
inicial; el siguiente paso es resolver requisitos pendientes, aprobar modelo, preparar/validar IaC
local y presentar el despliegue concreto. No saltar directamente a CreateTable.

## Requisitos confirmados por el usuario — 2026-10-14

Primera versión: varios usuarios, sin sincronización offline. Android aún es prototipo, sin
backend ni URL base; autenticación y lenguaje/librerías por confirmar con su repositorio.
El usuario pide responsabilidad integral del backend AWS, OpenAPI y guía para Android, pero
ordena revisar requisitos reales y aprobar contrato antes de desarrollar Lambda o crear tablas.
La autenticación también requiere aprobación antes de implementarse.

Se registró la base de revisión en requerimientos-backend.md y se marcó el modelo DynamoDB
como exploratorio. No hay arquitectura ni contrato aprobados. Se solicitó ruta/URL del
repositorio Android y documentación. Próximo paso: revisar esos insumos, mapear pantallas y
operaciones, proponer contrato y confirmar decisiones pendientes. No generar endpoints ficticios.

## Revisión Android y alcance demo confirmado — 2026-10-14

Repo revisado sin modificar: C:\Github\Taxflow_Movil, HEAD 28b7eab0e1f25fd8428187cb73d3eba09c39ba9d.
Kotlin/Compose; sin Room ni cliente HTTP declarados; manifiesto sin INTERNET. Login simulado,
listas e indicadores fijos, simulador no guarda. Documentación PostgreSQL/offline no es alcance vigente.

Usuario confirmó tres perfiles ficticios, aproximadamente 30 comprobantes cada uno; simulación
sin persistir, selector sin autenticación real, sin Cognito/SUNAT/offline. Objetivo e2e Android-AWS.
Se prepararon docs/integracion-android.md y docs/openapi.propuesto.json (9 operaciones propuestas).
Modelo mínimo: una tabla test-flow-dev-demo, PK/SK, sin GSI; Query por usuario y tipo, filtros
sobre dataset acotado en Lambda. La propuesta anterior de dos tablas/GSI queda sustituida.

Contrato/reglas didácticas/runtime Python propuestos pendientes de aprobación. No hay Lambda,
plantilla de infraestructura ni recursos remotos creados. Seed propuesto: 15 ingresos +15 gastos
por usuario, además de perfiles/avisos/calendario/reglas ficticios. Escrituras opcionales excluidas.
Impuesto/ahorro/consumo de 7 UIT no incluidos: requieren fórmulas o aceptar simplificación visual.
JSON y referencias internas de OpenAPI comprobados; validación formal según herramientas locales.
Próximo paso: usuario aprueba contrato, modelo y alcance de métricas; después desarrollar/validar
localmente. Presentar recursos/permisos/costos para aprobación separada antes de desplegar.

## Implementación local aprobada y completada — 2026-10-14

Usuario aprobó contrato/modelo/Python/dashboard simplificado. Backend en src/app.py,
service.py y repository.py; GetItem/Query consistente y paginado, sin escrituras runtime.
Contrato vigente docs/openapi.json v1.0.0 (openapi.propuesto.json solo historial).
Seed local determinista data/seed.json: 112 items, tres usuarios y 90 comprobantes.
Plantilla SAM template.yaml: tabla, Lambda, HTTP API, log group 7 días; LabRole existente.
Paquete local build/lambda.zip; scripts para generar/empaquetar/validar y carga condicional AWS.
README/AGENTS/.gitignore/.env.example añadidos sin secretos; no se inicializó Git.

10 pruebas unittest correctas; nueve respuestas validadas contra esquemas OpenAPI/seed.
YAML correcto y AWS cloudformation validate-template aceptado (CAPABILITY_AUTO_EXPAND).
LabRole confirmado con trust Lambda; nombres de políticas consultados, sin modificarlos.
Permisos efectivos de DynamoDB runtime/PassRole y creación de recursos pendientes de prueba.
SAM CLI y boto3 local no instalados; Lambda usa SDK incluido. No se instalaron herramientas.

No se creó stack, change set, bucket, Lambda, API ni tabla. Seed no cargado en AWS.
Propuesta de despliegue concreta en docs/despliegue.md incluye bucket S3 adicional de artefactos,
stack test-flow-dev-demo en 325875101955/us-east-1, costos, permisos, seed y retirada.
Se requiere autorización explícita de despliegue y carga antes de escrituras remotas.
Android no fue modificado ni contactado; la URL y validación e2e quedan pendientes de despliegue.

## Despliegue autorizado y completado — 2026-10-14

Usuario respondió «si autorizo» al despliegue y seed. Sesión/cuenta/nombres verificados sin
colisiones. Bucket test-flow-artifacts-325875101955-us-east-1 creado, SSE-S3 y bloqueo público
verificados. Paquete Lambda subido a key c079627e8a2ef8c2863f37ce2eb47e30.
Change set initial-demo-20261014 revisado y ejecutado: solo seis recursos previstos; sin IAM roles
nuevos ni cambios en políticas. Stack test-flow-dev-demo CREATE_COMPLETE.
API base: https://8cspr7pmca.execute-api.us-east-1.amazonaws.com
DynamoDB test-flow-dev-demo ACTIVE/PAY_PER_REQUEST/sin GSI; Lambda Active con LabRole;
logs 7 días, etapa $default 2 solicitudes/s, ráfaga 5. Seed completo: 112 ítems, 90 comprobantes.

scripts/smoke_api.py completó 39 comprobaciones HTTPS con comparaciones exactas contra seed y
Service local: nueve operaciones, tres usuarios, filtros, errores, aislamiento lógico y
simulaciones sin cambios de datos. Resultado en docs/validacion-aws.json.
Contrato docs/openapi.json y docs/integracion-android.md actualizados con URL real.
Inventario docs/recursos-aws.json; README y docs/despliegue.md reflejan resultado.
Runtime GetItem/Query y PassRole para este despliegue funcionaron; no se ampliaron permisos.

Responsabilidad backend de esta etapa completa. No se modificó ni contactó al agente Android.
La prueba Android -> AWS queda pendiente de que el agente móvil consuma la guía/contrato.
No hay autenticación: solo usuarios ficticios. No almacenar datos reales. No eliminar recursos
sin autorización adicional. El estado de saldo Academy no fue consultado en consola.

## Actualización de cuentas y autenticación — 2026-10-14

Usuario solicitó presentar una aplicación con contraseña/registro y nombres naturales; aprobó
implícitamente mediante petición concreta actualizar las cuentas y datos del prototipo existente.
Credenciales Academy estaban vencidas; usuario confirmó renovación y STS validó cuenta/rol.

Change set auth-accounts-20261014 revisado y ejecutado: modifica Lambda/API y reemplaza permiso
 de invocación por nuevo path /v1/{proxy+}. No crea servicios, tablas ni IAM roles/políticas.
Stack UPDATE_COMPLETE. Ruta antigua del selector ya no devuelve perfiles públicos.

Tres cuentas: Carlos Jara, Carmen González, Óscar Paredes. 112 ítems conocidos actualizados con
nombres naturales y origen MANUAL; credenciales como tres registros de hashes separados.
private/accesos-prueba.txt y .json guardan accesos solicitados (excluidos de Git, no imprimir).
private/account-items.json tiene hashes/salts; copia de datos previos en private/data-before-migration.json.
No se sobrescribieron cuentas fuera de las tres iniciales; no se eliminaron recursos.

src/auth.py: PBKDF2-HMAC-SHA256 600000 iteraciones, salt individual; sesiones aleatorias 256 bits,
solo SHA-256 del token almacenado y expires_at (2 horas). Logout revoca sesión actual.
Registro email único + perfil en TransactWriteItems. Nuevo usuario id user-UUID, sin copiar datos;
profesion vacía y ultimo_digito_ruc null. Todos los endpoints propios requieren Bearer.
Rutas /v1/me y /v1/me/... recomendadas. Aliases antiguos por user_id requieren sesión propia;
cuenta ajena devuelve 403. No Cognito ni integración SUNAT añadidos.

12 pruebas locales correctas y 12 respuestas contra OpenAPI v2 verificadas. 47 comprobaciones
HTTPS correctas (docs/validacion-aws.json): tres logins/datos, login incorrecto, logout/revocación,
aislamiento y registro nuevo vacío/duplicado. Se creó una cuenta extra de verificación sin datos;
su acceso está en private/registro-verificacion.json. No se eliminó esa cuenta.

Actualizados README, contrato docs/openapi.json v2, docs/integracion-android.md, inventario.
Usuario dice integración Android v1 realizada. Agente AWS no modificó Android ni contactó otro
agente: falta adaptar sus formularios/DTO/cabecera Bearer según la nueva guía para acceso v2.
URL sigue https://8cspr7pmca.execute-api.us-east-1.amazonaws.com.
No recuperar contraseña ni validar email/MFA; entorno académico. Sesiones expiradas se rechazan
lógicamente, no hay TTL automático; no se debe introducir información real de SUNAT.

## Reajuste de Contrato OpenAPI y Guía Android — 2026-10-14

Revisión de docs/integracion-android.md y docs/openapi.json completada:
1. openapi.json: añadido requestBody obligatorio a POST /v1/auth/logout (objeto vacio {})
   para alinearse con el validador de payloads de Lambda; añadido esquema EmptyObject;
   eliminados esquemas huérfanos DemoUser y DemoUserList; normalizados operationIds.
2. integracion-android.md: ampliado con modelos Kotlin completos (ProfileDto con ultimoDigitoRuc
   nullable, SessionResponse, LoginRequest, RegisterRequest), interfaz Retrofit v2 sin userId
   en el path, configuración de ApiClient con AuthInterceptor y RateLimitRetryInterceptor,
   gestión de sesión en repositorio y pautas de AuthScreen.
3. Validación local ejecutada: 12 pruebas unitarias correctas y scripts/validate.py verificado.

## Publicación del código — 2026-10-15

Usuario solicitó publicar en https://github.com/omparedes/Taxflow_DB.
Repositorio remoto comprobado vacío. Preparado primer commit en main con código, plantilla,
seed sin contraseñas y documentación. private/, .env, .aws, build/ y paquetes excluidos de Git.
Doce pruebas y validación de doce respuestas OpenAPI correctas antes de publicar.
No se cambió infraestructura AWS ni el proyecto Android para esta publicación.
