Actualización vigente: el usuario solicitó registro/login/logout, nombres naturales y contraseñas
individuales para tres cuentas. Implementado y desplegado contrato v2; cuentas registradas nuevas
comienzan vacías. El selector público queda retirado. Las decisiones anteriores siguen abajo como
historial. Guía actual: integracion-android.md.

# Test Flow: requisitos y contrato backend pendientes de revisión

Actualización vigente: prototipo académico de tres usuarios ficticios y unos 90 comprobantes,
simulaciones sin persistir, selector sin autenticación real; sin Cognito ni SUNAT. Revisado el
repositorio móvil; contrato propuesto en [integracion-android.md](integracion-android.md) y
[openapi.propuesto.json](openapi.propuesto.json). Las entradas anteriores de autenticación,
volumen y repo pendientes describen la fase previa y quedan sustituidas por esta decisión.

Fecha: 2026-10-14. Estado: levantamiento de requisitos, sin contrato API aprobado.

## Decisiones confirmadas por el usuario

- Aplicación Android en fase de prototipo, desarrollada en Android Studio por otro agente.
- Primera versión para varios usuarios; sin sincronización offline inicial.
- No existe backend AWS ni URL base definitiva.
- Autenticación pendiente de definición y aprobación; no implementarla todavía.
- Lenguaje y librerías Android pendientes de revisar en su repositorio.
- El agente AWS se encarga del diseño e implementación backend y de infraestructura.
- El agente Android consumirá el contrato HTTP acordado.
- Antes de desarrollar Lambda o crear tablas, revisar requisitos reales, definir contrato API
  y esperar aprobación. No inventar operaciones, tablas o reglas.
- El entorno es AWS Academy Learner Lab, con rol restringido y credenciales temporales.
  Cualquier diseño IAM debe respetar las restricciones; no ampliar permisos por defecto.

## Evidencia disponible y límites

El texto y el diagrama adjuntos son una propuesta relacional del agente de prototipo,
no un contrato aprobado ni evidencia de funcionalidades implementadas.
El modelo-dynamodb-propuesto.md es una propuesta exploratoria: sus nombres, claves e índices
no están aprobados. Se revisará con los patrones de acceso reales y con el contrato API.
Las reglas fiscales incluidas en el adjunto contienen parámetros desactualizados; no se
incorporarán como semillas ni lógica ejecutable sin validar vigencia y condiciones aplicables.

## Insumos solicitados

Ruta local o URL del repositorio Android y ubicación de su documentación funcional.
No se ha autorizado contactar al otro agente; la revisión se hará mediante los insumos del usuario.
No copiar credenciales AWS ni Clave SOL al repositorio o al contrato.

## Revisión a realizar con los insumos

1. Identificar pantallas, acciones disponibles, estados, formularios y validaciones reales.
2. Revisar entidades, DTO, repositorios y datos simulados; distinguir código implementado de propuestas.
3. Elaborar una matriz pantalla -> operación -> entradas -> respuesta -> patrón de acceso -> autorización.
4. Confirmar filtros, orden, paginación, volumen esperado y significado de fechas/importes.
5. Acordar identidad autenticada y aislamiento por usuario. El backend obtendrá el usuario de
   una identidad verificada; no confiará solo en usuario_id recibido desde Android.
6. Separar registro de comprobantes y estados manuales de emisión/validación real ante SUNAT.
7. Confirmar alcance de cálculos, pagos parciales, anulaciones y balances; registrar reglas pendientes.
8. Proponer contrato y autenticación para revisión, sin implementarlos hasta aprobación.

## Entregables después de revisar requisitos

- Contrato OpenAPI versionado YAML o JSON, con URL base pendiente hasta despliegue.
- Métodos, rutas, parámetros, cuerpos, paginación y errores acordados.
- Ejemplos sintéticos de respuestas y requisitos de autenticación por operación.
- Modelo DynamoDB vinculado a consultas concretas del contrato.
- Propuesta de runtime Lambda y organización de validaciones/lógica de negocio.
- Documento de integración Markdown para el agente Android.
- Propuesta IAM compatible con los roles y servicios existentes del laboratorio.

## Puntos de aprobación

Primero aprobar requisitos, contrato, autenticación propuesta, modelo y lenguaje backend.
Después preparar implementación local e infraestructura versionada, validar y presentar el
despliegue concreto con cuenta, región, recursos, permisos, costos, verificación y retirada.
La autorización de desarrollo no constituye aprobación para crear recursos AWS.

## Estado actual

No se han desarrollado funciones Lambda, creado tablas ni definido endpoints como contrato final.
La sesión AWS fue verificada y ListTables devolvió lista vacía en us-east-1 en la consulta anterior.
La disponibilidad de permisos de escritura y de roles de ejecución sigue sin verificarse.
