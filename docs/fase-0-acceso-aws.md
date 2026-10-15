# FASE 0: AWS Academy Learner Lab

Estado: conexión pendiente. AWS CLI no disponible en PATH ni en su ruta habitual; SAM tampoco.
Git 2.51.2, Node.js 24.15.0 y Python 3.13.9 disponibles. No se instalaron herramientas.

## Método acordado

El usuario accede desde Canvas > AWS Academy > Start Lab > consola, mediante rol federado voclabs.
Usar exclusivamente las credenciales temporales proporcionadas por AWS Details y el perfil
`test-flow-academy`. No configurar SSO, crear usuarios IAM, modificar permisos ni usar aws login.
No desplegar recursos. Las restricciones concretas de servicios y regiones deben consultarse en
las instrucciones del laboratorio; no asumir permisos por el nombre del rol.

## Pasos manuales

1. Instalar AWS CLI v2 mediante https://awscli.amazonaws.com/AWSCLIV2.msi.
   Esta instalación es manual; Codex no la ha ejecutado. Abrir una nueva terminal y comprobar:

```powershell
aws --version
```

2. Iniciar el laboratorio y esperar a que esté listo. Abrir AWS Details y mostrar las credenciales
   para AWS CLI. No pegar secretos en el chat, terminal ni repositorio.
3. En PowerShell, abrir el archivo de credenciales del usuario en un editor local:

```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.aws" -Force | Out-Null
notepad "$env:USERPROFILE\.aws\credentials"
```

Estos comandos modifican únicamente la configuración local del usuario y deben ejecutarse manualmente.
En el editor, pegar el bloque suministrado por AWS Details y cambiar su encabezado `[default]`
a `[test-flow-academy]`. Si hay otros perfiles, conservarlos y añadir o actualizar solo este bloque.
Debe contener las tres propiedades: `aws_access_key_id`, `aws_secret_access_key` y `aws_session_token`.
Guardar como `credentials` sin extensión `.txt`. No se incluyen valores de ejemplo para secretos.
El archivo guarda credenciales temporales en texto plano fuera del repositorio; mantenerlo privado.

4. Elegir la región explícitamente permitida por las instrucciones del Learner Lab. Sustituir
   el marcador antes de ejecutar (no introducir literalmente los signos < >):

```powershell
aws configure set region <REGION_PERMITIDA> --profile test-flow-academy
aws configure set output json --profile test-flow-academy
```

5. Validar sin mostrar credenciales:

```powershell
aws configure list-profiles
aws configure get region --profile test-flow-academy
aws sts get-caller-identity --profile test-flow-academy --no-cli-pager
```

STS debe devolver la cuenta del laboratorio y un ARN de rol asumido coherente con voclabs.
STS verifica identidad, no permisos para desplegar. No requiere una concesión IAM adicional.
Codex deberá ejecutar estas mismas consultas después de que el usuario termine la configuración.
No usar `aws configure list` para documentar credenciales ni imprimir archivos o cachés.

## Renovación y restricciones

Las credenciales copiadas no se renuevan automáticamente. Si expiran, volver a Start Lab según
el estado de la sesión, obtener las credenciales actuales en AWS Details y reemplazar las tres
propiedades del perfil. Un token de otra sesión junto a claves antiguas no funciona.
`ExpiredToken` requiere renovar; errores de token inválido requieren revisar el bloque completo
sin exponer sus valores. Ante `AccessDenied`, registrar la operación y respetar las restricciones;
no crear políticas ni intentar ampliar permisos. Consultar al instructor si es necesario.

No asumir duración fija, regiones concretas, disponibilidad de servicios, LabRole, iam:PassRole
ni permisos para crear roles. Verificar esas condiciones en las instrucciones del curso antes de
la futura arquitectura. El presupuesto del laboratorio también limita las pruebas posteriores.

Si Codex no encuentra aws después de instalarlo, comprobar la ruta habitual
`C:\Program Files\Amazon\AWSCLIV2\aws.exe` o reiniciar Codex para actualizar PATH.
Usar siempre `--profile test-flow-academy`; las variables de otra terminal no se propagan a Codex.
No copiar secretos para resolver fallos de red o sandbox.

## Fuentes

- Instalación: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Perfiles y token: https://docs.aws.amazon.com/cli/latest/topic/config-vars.html
- Credenciales temporales: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_use-resources.html
- STS: https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html

Las condiciones específicas del Learner Lab proceden de la descripción del usuario; faltan las
restricciones de su curso. Esta guía sustituye la recomendación anterior de login/SSO.
