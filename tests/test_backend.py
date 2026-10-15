import base64
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'scripts'))
import app
from generate_seed import build_seed
from repository import clean, DynamoRepository
from service import Service


class MemoryRepository:
    def __init__(self):
        self.items=build_seed()
    def get(self,user,key):
        return next((clean(copy.deepcopy(i)) for i in self.items if i['PK']=='USER#'+user and i['SK']==key),None)
    def rules(self):
        return clean(self.items[0])
    def query(self,user,kind):
        return [clean(copy.deepcopy(i)) for i in self.items if i['PK']=='USER#'+user and i['SK'].startswith(kind+'#')]
    def auth_get(self,pk,sk):
        return next((clean(copy.deepcopy(i)) for i in self.items if i['PK']==pk and i['SK']==sk),None)
    def auth_put(self,item):
        self.items=[i for i in self.items if (i['PK'],i['SK'])!=(item['PK'],item['SK'])]+[copy.deepcopy(item)]
    def auth_delete(self,pk,sk):
        self.items=[i for i in self.items if (i['PK'],i['SK'])!=(pk,sk)]
    def create_account(self,key,credentials,profile):
        if self.auth_get(key,'CREDENTIALS'):
            error=RuntimeError('duplicate')
            error.response={'Error':{'Code':'TransactionCanceledException'}}
            raise error
        self.auth_put(dict(credentials,PK=key,SK='CREDENTIALS'))
        self.auth_put(dict(profile,PK='USER#'+profile['id'],SK='PROFILE'))


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.repo=MemoryRepository()
        app._service=Service(self.repo)
        from auth import Auth
        self.tokens={u:Auth(self.repo).session(u)['access_token'] for u in ('demo-01','demo-02','demo-03')}
    def request(self,path,method='GET',query='',body=None,raw=None,encoded=False,token=None,anonymous=False):
        user=next((u for u in self.tokens if u in path),'demo-01')
        headers={'content-type':'application/json'}
        if not anonymous: headers['authorization']='Bearer '+(token or self.tokens[user])
        event={'rawPath':path,'rawQueryString':query,'requestContext':{'http':{'method':method}},
               'headers':headers,'body':raw if raw is not None else json.dumps(body),
               'isBase64Encoded':encoded}
        result=app.handler(event,SimpleNamespace(aws_request_id='test-request'))
        return result['statusCode'],json.loads(result['body'])
    def test_seed_has_three_distinct_users_and_ninety_receipts(self):
        self.assertEqual(115,len(self.repo.items))
        self.assertEqual(115,len({(x['PK'],x['SK']) for x in self.repo.items}))
        for user in ('demo-01','demo-02','demo-03'):
            self.assertEqual(15,len(self.repo.query(user,'INCOME')))
            self.assertEqual(15,len(self.repo.query(user,'EXPENSE')))
        self.assertEqual('Carlos Jara',self.request('/v1/me')[1]['nombre'])
    def test_user_isolation_and_foreign_id_not_found(self):
        for user in ('demo-01','demo-02','demo-03'):
            status, data=self.request(f'/v1/demo/users/{user}/incomes')
            self.assertEqual(200,status)
            self.assertTrue(all(i['id'].startswith('income-'+user[-2:]) for i in data['items']))
        self.assertEqual(404,self.request('/v1/demo/users/demo-02/incomes/income-01-01')[0])
        self.assertEqual(403,self.request('/v1/demo/users/demo-99/incomes')[0])
    def test_combined_search_date_state_and_totals(self):
        status,data=self.request('/v1/demo/users/demo-01/incomes',query='q=e001-012&cliente=HORIZONTE&desde=2026-09-14&hasta=2026-09-14&estado=PAGADO')
        self.assertEqual(200,status)
        self.assertEqual(['income-01-12'],[x['id'] for x in data['items']])
        self.assertEqual(data['items'][0]['monto_bruto_centimos'],data['resumen']['bruto_centimos'])
        self.assertEqual(0,self.request('/v1/demo/users/demo-01/incomes',query='q=sin-coincidencia')[1]['total'])
    def test_expense_category_and_observed(self):
        status,data=self.request('/v1/demo/users/demo-02/expenses',query='categoria=restaurantes&estado=OBSERVADO')
        self.assertEqual(200,status)
        self.assertEqual(1,data['total'])
        self.assertEqual('expense-02-05',data['items'][0]['id'])
    def test_dashboard_excludes_unpaid_and_caps_deductions(self):
        status,data=self.request('/v1/demo/users/demo-03/dashboard',query='anio=2026&mes=9')
        self.assertEqual(200,status)
        paid=[i for i in self.repo.query('demo-03','INCOME') if i['estado']=='PAGADO']
        self.assertEqual(sum(i['monto_bruto_centimos'] for i in paid),data['ingresos_anio_centimos'])
        for i in self.repo.items:
            if i['PK']=='USER#demo-03' and i['SK'].startswith('EXPENSE#'):
                i['deducible_centimos']=1000000
        data=self.request('/v1/demo/users/demo-03/dashboard',query='anio=2026&mes=9')[1]
        self.assertEqual(1650000,data['deducible_anio_centimos'])
    def test_simulations_threshold_rounding_and_no_writes(self):
        before=copy.deepcopy(self.repo.items)
        path='/v1/demo/users/demo-01/simulations'
        for amount,retention in [(150000,0),(150001,12000),(350000,28000)]:
            status,data=self.request(path,'POST',body={'tipo':'INGRESO','monto_centimos':amount,'aplicar_retencion':True})
            self.assertEqual(200,status); self.assertEqual(retention,data['retencion_centimos'])
            self.assertFalse(data['persistido'])
        status,data=self.request(path,'POST',body={'tipo':'GASTO','monto_centimos':10,'categoria':'restaurantes'})
        self.assertEqual(2,data['deducible_centimos'])
        self.assertEqual(10,data['neto_centimos'])
        self.assertEqual(before,self.repo.items)
    def test_invalid_requests(self):
        for query in ('desde=2026-02-30','desde=2026-09-01&hasta=2026-08-01','estado=ERROR','q=','q=a&q=b','usuario_id=demo-02'):
            self.assertEqual(400,self.request('/v1/demo/users/demo-01/incomes',query=query)[0])
        self.assertEqual(400,self.request('/v1/demo/users/demo-01/dashboard',query='anio=2025&mes=9')[0])
        path='/v1/demo/users/demo-01/simulations'
        for raw in ('{','{"tipo":"INGRESO","tipo":"GASTO"}','{"tipo":"INGRESO","monto_centimos":NaN}', '[]'):
            self.assertEqual(400,self.request(path,'POST',raw=raw)[0])
        for amount in (True,1.5,0,-1):
            self.assertEqual(400,self.request(path,'POST',body={'tipo':'INGRESO','monto_centimos':amount,'aplicar_retencion':True})[0])
    def test_base64_json(self):
        raw=base64.b64encode(json.dumps({'tipo':'GASTO','monto_centimos':32000,'categoria':'restaurantes'}).encode()).decode()
        status,data=self.request('/v1/demo/users/demo-01/simulations','POST',raw=raw,encoded=True)
        self.assertEqual(200,status); self.assertEqual(4800,data['deducible_centimos'])
    def test_repository_paginates_query(self):
        repository=object.__new__(DynamoRepository)
        repository.table=Mock()
        repository.table.query.side_effect=[{'Items':[{'id':'a'}],'LastEvaluatedKey':{'PK':'p','SK':'a'}},{'Items':[{'id':'b'}]}]
        self.assertEqual(['a','b'],[x['id'] for x in repository.query('demo-01','INCOME')])
        self.assertEqual({'PK':'p','SK':'a'},repository.table.query.call_args.kwargs['ExclusiveStartKey'])
    def test_errors_do_not_leak_exception(self):
        self.repo.get=Mock(side_effect=RuntimeError('sensitive-marker'))
        status,data=self.request('/v1/me')
        self.assertEqual(500,status); self.assertNotIn('sensitive-marker',json.dumps(data))

    def test_registration_login_logout_and_empty_account(self):
        fields={'nombre':'Nueva Cuenta','email':'nueva@taxflow.test','password':'ClaveSeguraNueva-2026'}
        status,data=self.request('/v1/auth/register','POST',body=fields,anonymous=True)
        self.assertEqual(200,status)
        token=data['access_token']
        for route in ('incomes','expenses','notifications'):
            self.assertEqual(0,self.request('/v1/me/'+route,token=token)[1]['total'])
        dash=self.request('/v1/me/dashboard',query='anio=2026&mes=9',token=token)[1]
        self.assertEqual(0,dash['ingresos_anio_centimos'])
        self.assertEqual(0,self.request('/v1/me/calendar',query='anio=2026',token=token)[1]['total'])
        self.assertEqual(409,self.request('/v1/auth/register','POST',body=dict(fields,email='NUEVA@taxflow.test'),anonymous=True)[0])
        login={k:fields[k] for k in ('email','password')}
        self.assertEqual(200,self.request('/v1/auth/login','POST',body=login,anonymous=True)[0])
        self.assertEqual(401,self.request('/v1/auth/login','POST',body=dict(login,password='ContraseñaErronea-2026'),anonymous=True)[0])
        self.assertEqual(200,self.request('/v1/auth/logout','POST',body={},token=token)[0])
        self.assertEqual(401,self.request('/v1/me',token=token)[0])

    def test_anonymous_denied_and_session_expiry(self):
        from auth import Auth
        self.assertEqual(401,self.request('/v1/demo/users/demo-01/incomes',anonymous=True)[0])
        self.assertEqual(401,self.request('/v1/demo/users',anonymous=True)[0])
        self.assertEqual(403,self.request('/v1/demo/users/demo-02/incomes',token=self.tokens['demo-01'])[0])
        expired=Auth(self.repo,clock=lambda:0).session('demo-01')['access_token']
        self.assertEqual(401,self.request('/v1/me',token=expired)[0])


if __name__=='__main__': unittest.main()
