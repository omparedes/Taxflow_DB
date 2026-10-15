"""Carga remota explicita y condicionada; ejecutar solo tras autorizacion del usuario."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', required=True, choices=['LOAD_DEMO_DATA'])
    args = parser.parse_args()
    aws = Path('C:/Program Files/Amazon/AWSCLIV2/aws.exe')
    def call(*command):
        result = subprocess.run([str(aws), *command, '--profile', 'test-flow-academy',
                                 '--region', 'us-east-1', '--no-cli-pager'], capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError('Operacion AWS fallida; revisar sesion/permisos. ' + command[0] + ' ' + command[1])
        return json.loads(result.stdout or '{}')
    identity = call('sts','get-caller-identity')
    if identity['Account'] != '325875101955' or ':assumed-role/voclabs/' not in identity['Arn']:
        raise RuntimeError('Identidad/cuenta inesperada; carga cancelada')
    table = call('dynamodb','describe-table','--table-name','test-flow-dev-demo')['Table']
    if table['TableStatus'] != 'ACTIVE':
        raise RuntimeError('Tabla no activa')
    def encode(v):
        if isinstance(v,bool): return {'BOOL':v}
        if isinstance(v,int): return {'N':str(v)}
        if isinstance(v,str): return {'S':v}
        if isinstance(v,dict): return {'M':{k:encode(x) for k,x in v.items()}}
        raise ValueError('Tipo de seed no permitido')
    # PutItem condicionado: repetir no sobrescribe ni elimina registros existentes.
    items=json.loads((ROOT/'data/seed.json').read_text(encoding='utf-8'))
    for item in items:
        existing=call('dynamodb','get-item','--table-name','test-flow-dev-demo','--consistent-read',
                      '--key',json.dumps({k:encode(item[k]) for k in ('PK','SK')}))
        if existing.get('Item'):
            if existing['Item'] != {k:encode(v) for k,v in item.items()}:
                raise RuntimeError('Item existente diferente; cancelar sin sobrescribir')
            continue
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'item.json'
            path.write_text(json.dumps({k:encode(v) for k,v in item.items()}),encoding='utf-8')
            call('dynamodb','put-item','--table-name','test-flow-dev-demo',
                 '--item','file://'+path.as_posix(),'--condition-expression','attribute_not_exists(PK)')
    print('Carga demo completada o ya existente: '+str(len(items))+' items.')


if __name__=='__main__':
    main()
