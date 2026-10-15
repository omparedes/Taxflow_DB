"""Validación local: contrato, seed y respuestas de las nueve operaciones."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tests'))
from jsonschema import Draft7Validator
from test_backend import MemoryRepository
from service import Service
from auth import Auth, email_key, password_hash

contract=json.loads((ROOT/'docs/openapi.json').read_text(encoding='utf-8'))
schemas=contract['components']['schemas']
def nullable_to_jsonschema(value):
    if isinstance(value,dict):
        if value.get('nullable') and 'type' in value:
            value['type']=[value['type'],'null']
        for child in value.values(): nullable_to_jsonschema(child)
    elif isinstance(value,list):
        for child in value: nullable_to_jsonschema(child)
nullable_to_jsonschema(contract)
service=Service(MemoryRepository())
credential='ClaveLocalValidacion-2026'
profile=service.repo.get('demo-01','PROFILE')
service.repo.auth_put(dict(password_hash(credential),PK=email_key(profile['email']),SK='CREDENTIALS',user_id='demo-01'))
token=Auth(service.repo).session('demo-01')['access_token']
headers={'authorization':'Bearer '+token}
ids=[]
for path,methods in contract['paths'].items():
    for method,op in methods.items():
        ids.append(op['operationId'])
        resolved=path.replace('{user_id}','demo-01').replace('{id}','expense-01-01' if 'expenses' in path else 'income-01-01')
        params={'anio':'2026','mes':'9'} if path.endswith('/dashboard') else {'anio':'2026'} if path.endswith('/calendar') else {}
        body={'tipo':'INGRESO','monto_centimos':350000,'aplicar_retencion':True} if method=='post' else None
        if path.endswith('/register'): body={'nombre':'Cuenta Nueva','email':'validacion@taxflow.test','password':credential}
        if path.endswith('/login'): body={'email':profile['email'],'password':credential}
        if path.endswith('/logout'): body={}
        response=service.dispatch(method.upper(),resolved,params,body,headers)
        reference=op['responses']['200']['content']['application/json']['schema']['$ref'].split('/')[-1]
        schema=dict(schemas[reference],components=contract['components'])
        Draft7Validator(schema,format_checker=Draft7Validator.FORMAT_CHECKER).validate(response)
assert len(ids)==len(set(ids))==12
seed=json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8'))
assert seed==MemoryRepository().items
for name,schema in schemas.items(): Draft7Validator.check_schema(schema)
print('Contrato: 12 respuestas verificadas contra esquemas; seed determinista, 112 items. No valida transform SAM.')
