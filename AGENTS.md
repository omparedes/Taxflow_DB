# Test Flow backend

Aplicación académica: tres cuentas iniciales y 90 comprobantes de prueba. Registro/login/logout
solicitados por el usuario; cuentas nuevas vacías. Sin SUNAT, Cognito ni offline.
Solicitud actual autoriza actualizar backend/datos/cuentas; retirada requiere aprobación separada.
Contrato vigente docs/openapi.json v2. private/ contiene accesos locales excluidos de Git;
nunca imprimir contraseñas/tokens/hashes ni copiarlos al contrato.
Consultas locales y AWS de solo lectura autorizadas. Instalaciones, despliegues, seed remoto,
eliminación y modificaciones IAM requieren autorización explícita. No copiar credenciales.
Reutilizar LabRole; no crear roles ni ampliar permisos. El sandbox no lee ~/.aws; consultas
autorizadas requieren ejecución fuera del sandbox. No cambiar ACL ni configuración global.
Ejecutar `python -m unittest discover -s tests -v` y `python scripts/validate.py` tras cambios.
Mantener docs/estado-proyecto.md e integracion-android.md. No modificar el proyecto Android.
