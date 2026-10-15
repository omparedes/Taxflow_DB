import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

USERS = ('demo-01', 'demo-02', 'demo-03')
CATEGORIES = ('restaurantes', 'servicios', 'alojamiento', 'essalud')


class ApiError(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message


def bad(message):
    raise ApiError(400, 'VALIDATION_ERROR', message)


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        bad('Entero fuera de rango')
    return value


def query_number(params, name, low, high):
    value = params.get(name, '')
    if not re.fullmatch(r'[0-9]+', value):
        bad('Parametro numerico requerido: ' + name)
    return integer(int(value), low, high)


def check_params(params, allowed):
    if set(params) - set(allowed):
        bad('Parametros desconocidos')


def filtered(items, params, expense=False):
    allowed = {'desde', 'hasta', 'estado', 'categoria'} if expense else {'desde', 'hasta', 'estado', 'q', 'cliente'}
    check_params(params, allowed)
    for key in ('desde', 'hasta'):
        if key in params:
            try:
                if date.fromisoformat(params[key]).isoformat() != params[key]:
                    bad('Fecha debe usar YYYY-MM-DD')
            except ValueError:
                bad('Fecha invalida')
    if params.get('desde', '') > params.get('hasta', '9999-12-31'):
        bad('desde debe ser anterior o igual a hasta')
    states = ('MANUAL', 'OBSERVADO') if expense else ('PAGADO', 'PENDIENTE', 'REVERTIDO')
    if 'estado' in params and params['estado'] not in states:
        bad('Estado invalido')
    if 'categoria' in params and params['categoria'] not in CATEGORIES:
        bad('Categoria invalida')
    for key, limit in (('q', 100), ('cliente', 150)):
        if key in params and not 1 <= len(params[key]) <= limit:
            bad('Busqueda fuera de rango')
    selected = []
    for item in items:
        if not params.get('desde', '') <= item['fecha'] <= params.get('hasta', '9999-12-31'):
            continue
        if any(item[key] != params[key] for key in ('estado', 'categoria') if key in params):
            continue
        if 'cliente' in params and params['cliente'].casefold() not in item['cliente'].casefold():
            continue
        if 'q' in params:
            q = params['q'].casefold()
            if not (q in item['cliente'].casefold() or q in (item['serie'] + '-' + item['numero']).casefold()):
                continue
        selected.append(item)
    return sorted(selected, key=lambda i: (-date.fromisoformat(i['fecha']).toordinal(), i['id']))


def percentage(amount, bp):
    return int((Decimal(amount) * Decimal(bp) / 10000).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


class Service:
    def __init__(self, repository):
        self.repo = repository

    def dispatch(self, method, path, params, body, headers=None):
        from auth import Auth
        auth = Auth(self.repo)
        headers = headers or {}
        if method == 'POST' and path in ('/v1/auth/register','/v1/auth/login','/v1/auth/logout'):
            check_params(params, ())
            return auth.dispatch(path.rsplit('/',1)[-1],body,headers)
        user_id, _ = auth.authenticate(headers)
        if method == 'GET' and path == '/v1/me':
            check_params(params, ())
            return self.repo.get(user_id,'PROFILE')
        if path.startswith('/v1/me/'):
            path = '/v1/demo/users/' + user_id + path[len('/v1/me'):]
        match = re.fullmatch(r'/v1/demo/users/([^/]+)/(dashboard|incomes|expenses|calendar|notifications|simulations)(?:/([a-z0-9-]{1,40}))?', path)
        if not match:
            raise ApiError(404, 'NOT_FOUND', 'Ruta no encontrada')
        user, route, ident = match.groups()
        if user != user_id:
            raise ApiError(403, 'FORBIDDEN', 'No tienes acceso a esta cuenta')
        if self.repo.get(user, 'PROFILE') is None:
            raise ApiError(404, 'NOT_FOUND', 'Usuario no encontrado')
        if method == 'POST' and route == 'simulations' and ident is None:
            check_params(params, ())
            return self.simulate(body)
        if method != 'GET' or route == 'simulations':
            raise ApiError(404, 'NOT_FOUND', 'Ruta no encontrada')
        if ident:
            if route not in ('incomes', 'expenses'):
                raise ApiError(404, 'NOT_FOUND', 'Ruta no encontrada')
            check_params(params, ())
            item = self.repo.get(user, ('INCOME' if route == 'incomes' else 'EXPENSE') + '#' + ident)
            if not item:
                raise ApiError(404, 'NOT_FOUND', 'Comprobante no encontrado')
            return item
        if route in ('incomes', 'expenses'):
            expense = route == 'expenses'
            items = filtered(self.repo.query(user, 'EXPENSE' if expense else 'INCOME'), params, expense)
            if expense:
                totals = {'total_centimos': sum(i['monto_centimos'] for i in items),
                          'deducible_centimos': sum(i['deducible_centimos'] for i in items)}
            else:
                totals = {out: sum(i[field] for i in items) for out, field in
                          [('bruto_centimos', 'monto_bruto_centimos'), ('retencion_centimos', 'retencion_centimos'), ('neto_centimos', 'monto_neto_centimos')]}
            return {'items': items, 'total': len(items), 'resumen': totals}
        if route == 'notifications':
            check_params(params, ())
            items = sorted(self.repo.query(user, 'NOTIFICATION'), key=lambda i: i['id'])
            items.sort(key=lambda i: i['created_at'], reverse=True)
            return {'items': items, 'total': len(items)}
        check_params(params, ('anio', 'mes') if route == 'dashboard' else ('anio',))
        query_number(params, 'anio', 2026, 2026)
        if route == 'calendar':
            items = sorted((i for i in self.repo.query(user, 'CALENDAR') if i['fecha'].startswith('2026-')),
                           key=lambda i: (i['fecha'], i['id']))
            return {'items': items, 'total': len(items)}
        return self.dashboard(user, query_number(params, 'mes', 1, 12))

    def rules(self):
        rules = self.repo.rules()
        if not rules:
            raise ApiError(503, 'DATASET_NOT_READY', 'Configuracion pendiente')
        return rules

    def simulate(self, body):
        if not isinstance(body, dict):
            bad('Objeto JSON requerido')
        kind = body.get('tipo')
        required = {'tipo', 'monto_centimos', 'aplicar_retencion'} if kind == 'INGRESO' else {'tipo', 'monto_centimos', 'categoria'}
        if kind not in ('INGRESO', 'GASTO') or set(body) != required:
            bad('Campos de simulacion invalidos')
        amount = integer(body['monto_centimos'], 1, 100000000)
        rules = self.rules()
        retention = deductible = 0
        if kind == 'INGRESO':
            if type(body['aplicar_retencion']) is not bool:
                bad('aplicar_retencion debe ser booleano')
            if body['aplicar_retencion'] and amount > rules['umbral_retencion_centimos']:
                retention = percentage(amount, rules['retencion_pb'])
        else:
            if body['categoria'] not in CATEGORIES:
                bad('Categoria invalida')
            deductible = percentage(amount, rules['categorias_pb'][body['categoria']])
        return dict(tipo=kind, monto_centimos=amount, retencion_centimos=retention,
                    neto_centimos=amount-retention, deducible_centimos=deductible,
                    reglas_version=rules['version'], persistido=False)

    def dashboard(self, user, month):
        incomes = [i for i in self.repo.query(user, 'INCOME') if i['fecha'].startswith('2026-')]
        expenses = [i for i in self.repo.query(user, 'EXPENSE') if i['fecha'].startswith('2026-')]
        paid = [i for i in incomes if i['estado'] == 'PAGADO']
        valid = [i for i in expenses if i['estado'] == 'MANUAL']
        rules = self.rules()
        activity = [dict(tipo='INGRESO', id=i['id'], fecha=i['fecha'], titulo=i['cliente'], monto_centimos=i['monto_bruto_centimos']) for i in incomes]
        activity += [dict(tipo='GASTO', id=i['id'], fecha=i['fecha'], titulo=i['proveedor'], monto_centimos=i['monto_centimos']) for i in expenses]
        activity.sort(key=lambda i: (i['id'], i['tipo']))
        activity.sort(key=lambda i: i['fecha'], reverse=True)
        return dict(usuario_id=user, anio=2026, mes=month,
                    ingresos_mes_centimos=sum(i['monto_bruto_centimos'] for i in paid if i['fecha'][5:7] == f'{month:02}'),
                    ingresos_anio_centimos=sum(i['monto_bruto_centimos'] for i in paid),
                    retenciones_anio_centimos=sum(i['retencion_centimos'] for i in paid),
                    gastos_anio_centimos=sum(i['monto_centimos'] for i in expenses),
                    deducible_anio_centimos=min(sum(i['deducible_centimos'] for i in valid), rules['uit_centimos']*3),
                    limite_7_uit_centimos=rules['uit_centimos']*7, limite_3_uit_centimos=rules['uit_centimos']*3,
                    reglas_version=rules['version'], actividad_reciente=activity[:5])
