"""Actualiza SOLO las cuentas/112 items de prueba conocidos; conserva otras cuentas."""
import json
import subprocess
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AWS='C:/Program Files/Amazon/AWSCLIV2/aws.exe'

def call(*args):
    r=subprocess.run([AWS,*args,'--profile','test-flow-academy','--region','us-east-1','--no-cli-pager'],capture_output=True,text=True)
    if r.returncode: raise RuntimeError('Operacion AWS fallida: '+args[0]+' '+args[1])
    return json.loads(r.stdout or '{}')

def encode(v):
    if isinstance(v,bool): return {'BOOL':v}
    if isinstance(v,int): return {'N':str(v)}
    if isinstance(v,str): return {'S':v}
    if isinstance(v,dict): return {'M':{k:encode(x) for k,x in v.items()}}
    raise ValueError('Tipo invalido')

if __name__=='__main__':
    identity=call('sts','get-caller-identity')
    assert identity['Account']=='325875101955' and ':assumed-role/voclabs/' in identity['Arn']
    seed=json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8'))
    creds=json.loads((ROOT/'private/account-items.json').read_text(encoding='utf-8'))
    assert len(seed)==112 and len(creds)==3
    backup=[]
    for user in ('demo-01','demo-02','demo-03'):
        result=call('dynamodb','query','--table-name','test-flow-dev-demo',
                    '--key-condition-expression','PK = :pk','--expression-attribute-values',
                    json.dumps({':pk':{'S':'USER#'+user}}),'--consistent-read')
        backup.extend(result['Items'])
    (ROOT/'private/data-before-migration.json').write_text(json.dumps(backup,indent=2)+'\n',encoding='utf-8')
    for offset in range(0,len(seed+creds),25):
        requests={'test-flow-dev-demo':[{'PutRequest':{'Item':{k:encode(v) for k,v in item.items()}}}
                                      for item in (seed+creds)[offset:offset+25]]}
        for attempt in range(6):
            with tempfile.TemporaryDirectory() as directory:
                p=Path(directory)/'batch.json'; p.write_text(json.dumps(requests),encoding='utf-8')
                result=call('dynamodb','batch-write-item','--request-items','file://'+p.as_posix())
            requests=result.get('UnprocessedItems',{})
            if not any(requests.values()): break
            time.sleep(0.25*2**attempt)
        else: raise RuntimeError('Items sin procesar; reanudar migracion')
    print('Migracion completa: 112 datos actualizados y 3 cuentas con hashes. Otras cuentas conservadas.')
