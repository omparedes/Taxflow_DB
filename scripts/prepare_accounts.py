"""Genera accesos locales privados; no imprime contraseñas ni conecta a AWS."""
import json
import secrets
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from auth import email_key,password_hash

folder=ROOT/'private'
folder.mkdir(exist_ok=True)
file=folder/'accesos-prueba.json'
seed=json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8'))
profiles=[x for x in seed if x['SK']=='PROFILE']
if not file.exists():
    accesses=[{'id':p['id'],'nombre':p['nombre'],'email':p['email'],
               'password':'Tf-'+secrets.token_urlsafe(15)+'!'} for p in profiles]
    file.write_text(json.dumps(accesses,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
else:
    accesses=json.loads(file.read_text(encoding='utf-8'))
records=folder/'account-items.json'
if not records.exists():
    records.write_text(json.dumps([dict(password_hash(a['password']),PK=email_key(a['email']),
                                       SK='CREDENTIALS',user_id=a['id']) for a in accesses],indent=2)+'\n',encoding='utf-8')
lines=['Accesos para pruebas manuales de Test Flow','Archivo privado excluido de Git. No son credenciales AWS.','']
for a in accesses:
    lines.extend([a['nombre'],'Correo: '+a['email'],'Contraseña: '+a['password'],''])
(folder/'accesos-prueba.txt').write_text('\n'.join(lines),encoding='utf-8')
print('Tres accesos preparados en private/accesos-prueba.txt; hashes separados. Valores no impresos.')
