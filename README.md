# Test Flow — backend AWS

API con registro, login, sesiones y logout. Tres cuentas iniciales: Carlos Jara, Carmen González
 y Óscar Paredes, con 90 comprobantes en total. Cuentas nuevas comienzan vacías.

URL base: https://8cspr7pmca.execute-api.us-east-1.amazonaws.com

- [Contrato OpenAPI v2](docs/openapi.json)
- [Guía Android](docs/integracion-android.md)
- [Recursos y despliegue](docs/despliegue.md)
- [Estado del proyecto](docs/estado-proyecto.md)
- Accesos de prueba privados: private/accesos-prueba.txt, excluido de Git.

Una tabla DynamoDB sin GSI, Lambda Python 3.13, HTTP API y LabRole existente. Sin Cognito,
SUNAT ni offline. No introducir información fiscal real en este entorno académico.

## Verificación local

```powershell
& 'C:\Users\Oscar\anaconda3\python.exe' -m unittest discover -s tests -v
& 'C:\Users\Oscar\anaconda3\python.exe' scripts/validate.py
& 'C:\Users\Oscar\anaconda3\python.exe' scripts/prepare_deploy.py
```

Boto3 del runtime Lambda, sin instalación local adicional. jsonschema instalado se utiliza para
validar respuestas del servicio. src/auth.py implementa PBKDF2-HMAC-SHA256, 600000 iteraciones,
salt individual y sesiones opacas de dos horas. No usar los accesos privados en otra aplicación.
Registro crea cuenta/perfil en transacción. Sin escritura de comprobantes desde el simulador.

scripts/migrate_accounts.py actualiza exclusivamente las tres cuentas/datos de prueba conocidos
 y conserva otras cuentas. Escrituras/retirada y cambios IAM requieren autorización del usuario.
El contrato v2 reemplaza el selector público: Android debe enviar Bearer en las consultas.
