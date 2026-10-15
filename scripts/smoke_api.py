"""Verificacion HTTPS con sesiones; secretos solo en archivos private/."""
import argparse, json, re, secrets, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests')); sys.path.insert(0,str(ROOT/'src'))
from test_backend import MemoryRepository
from service import Service
from auth import Auth

def main():
 parser=argparse.ArgumentParser(); parser.add_argument('--base-url',required=True)
 base=parser.parse_args().base_url.rstrip('/')
 if not re.fullmatch(r'https://[a-z0-9]+\.execute-api\.us-east-1\.amazonaws\.com',base): raise ValueError('URL invalida')
 checks=[]
 def call(path,body=None,token=None,params=None,status=200):
  url=base+path+('?' + urllib.parse.urlencode(params) if params else '')
  headers={'Content-Type':'application/json'}
  if token: headers['Authorization']='Bearer '+token
  request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers,method='POST' if body is not None else 'GET')
  for attempt in range(5):
   time.sleep(0.6)
   try:
    with urllib.request.urlopen(request,timeout=20) as response: code,actual=response.status,json.load(response)
    break
   except urllib.error.HTTPError as error:
    if error.code==429 and attempt<4: time.sleep(1+attempt); continue
    code=error.code; actual=json.loads(error.read()); break
  if code!=status: raise AssertionError(f'{path}: HTTP {code}; esperado {status}')
  checks.append({'path':path,'status':code}); return actual
 call('/v1/me',status=401); call('/v1/demo/users/demo-01/incomes',status=401)
 accounts=json.loads((ROOT/'private/accesos-prueba.json').read_text(encoding='utf-8'))
 for account in accounts:
  session=call('/v1/auth/login',body={k:account[k] for k in ('email','password')}); token=session['access_token']; user=account['id']
  assert session['user']['nombre']==account['nombre']
  local=Service(MemoryRepository()); local_token=Auth(local.repo).session(user)['access_token']
  for route in ('','/incomes','/expenses','/dashboard','/calendar','/notifications'):
   params={'anio':'2026','mes':'9'} if route=='/dashboard' else {'anio':'2026'} if route=='/calendar' else {}
   actual=call('/v1/me'+route,token=token,params=params)
   expected=local.dispatch('GET','/v1/me'+route,params,None,{'authorization':'Bearer '+local_token})
   assert actual==expected,'Datos/calculos distintos: '+route
  call('/v1/demo/users/'+('demo-02' if user!='demo-02' else 'demo-01')+'/incomes',token=token,status=403)
  for body in ({'tipo':'INGRESO','monto_centimos':350000,'aplicar_retencion':True},{'tipo':'GASTO','monto_centimos':32000,'categoria':'restaurantes'}):
   assert call('/v1/me/simulations',body=body,token=token)==local.simulate(body)
  call('/v1/auth/logout',body={},token=token); call('/v1/me',token=token,status=401)
 call('/v1/auth/login',body={'email':accounts[0]['email'],'password':'ContraseñaIncorrecta-2026'},status=401)
 registration={'nombre':'Cuenta de prueba de registro','email':'registro-'+secrets.token_hex(5)+'@taxflow.test','password':'Tf-'+secrets.token_urlsafe(15)+'!'}
 session=call('/v1/auth/register',body=registration); token=session['access_token']
 (ROOT/'private/registro-verificacion.json').write_text(json.dumps(registration,indent=2)+'\n',encoding='utf-8')
 for route in ('incomes','expenses','notifications'): assert call('/v1/me/'+route,token=token)['total']==0
 assert call('/v1/me/calendar',token=token,params={'anio':'2026'})['total']==0
 dashboard=call('/v1/me/dashboard',token=token,params={'anio':'2026','mes':'9'})
 assert dashboard['ingresos_anio_centimos']==dashboard['gastos_anio_centimos']==0
 call('/v1/auth/register',body=registration,status=409); call('/v1/auth/logout',body={},token=token)
 report={'base_url':base,'version':'2.0.0','passed':len(checks),'checks':checks,'scope':'HTTPS y sesiones; Android pendiente de actualizar'}
 (ROOT/'docs/validacion-aws.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('Validacion HTTPS completada: '+str(len(checks))+' comprobaciones. Sin secretos en reporte.')
if __name__=='__main__': main()
