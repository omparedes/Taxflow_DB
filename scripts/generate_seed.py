"""Genera datos locales deterministas. Nunca conecta a AWS."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from service import percentage

ROOT = Path(__file__).resolve().parents[1]


def build_seed():
    rules = dict(PK='DEMO', SK='RULES#demo-v1', version='demo-v1', uit_centimos=550000,
                 retencion_pb=800, umbral_retencion_centimos=150000,
                 categorias_pb=dict(restaurantes=1500, alojamiento=1500, servicios=3000, essalud=10000))
    items = [rules]
    categories = ('restaurantes', 'servicios', 'alojamiento', 'essalud')
    names = ('Carlos Jara','Carmen González','Óscar Paredes')
    emails = ('carlos.jara@taxflow.test','carmen.gonzalez@taxflow.test','oscar.paredes@taxflow.test')
    clients = ('Estudio Horizonte','Consultora Andina','Servicios Norte')
    providers = ('Restaurante Los Olivos','Centro Médico Alameda','Hotel Costa Verde','Aportes del hogar')
    for u, profession in enumerate(('Diseñador','Consultora','Docente'), 1):
        user, pk = f'demo-{u:02}', f'USER#demo-{u:02}'
        items.append(dict(PK=pk, SK='PROFILE', id=user, nombre=names[u-1], email=emails[u-1],
                          profesion=profession, ultimo_digito_ruc=u))
        for i in range(1, 16):
            gross = (u*1000+i*110)*100
            retention = percentage(gross, 800) if gross > 150000 and i % 4 else 0
            ident = f'income-{u:02}-{i:02}'
            items.append(dict(PK=pk, SK='INCOME#'+ident, id=ident,
                              cliente=clients[i%3], serie=f'E{u:03}', numero=f'{i:03}',
                              fecha=f'2026-{7+(i-1)//5:02}-{2+i:02}', monto_bruto_centimos=gross,
                              retencion_centimos=retention, monto_neto_centimos=gross-retention,
                              estado=('PAGADO','PENDIENTE','REVERTIDO')[i%3], origen='MANUAL'))
            ident = f'expense-{u:02}-{i:02}'
            category, amount = categories[(i-1)%4], (u*40+i*13)*100
            bp = rules['categorias_pb'][category]
            items.append(dict(PK=pk, SK='EXPENSE#'+ident, id=ident,
                              proveedor=providers[(i-1)%4], serie=f'B{u:03}', numero=f'{i:03}',
                              fecha=f'2026-{7+(i-1)//5:02}-{1+i:02}', categoria=category,
                              monto_centimos=amount, porcentaje_deducible_pb=bp,
                              deducible_centimos=percentage(amount,bp), estado='OBSERVADO' if i%5==0 else 'MANUAL', origen='MANUAL'))
        for i in range(1,4):
            ident = f'calendar-{u:02}-{i:02}'
            items.append(dict(PK=pk,SK='CALENDAR#'+ident,id=ident,titulo=('Declaración mensual','Declaración anual','Suspensión de retenciones')[i-1],
                              fecha=f'2026-{8+i:02}-{15+u:02}',formulario=('616','709','1609')[i-1],
                              estado=('PENDIENTE','PRESENTADO','ACTIVO')[i-1],
                              detalle=('Revisar ingresos del periodo','Revisar resumen del ejercicio','Consultar estado de la constancia')[i-1],origen='MANUAL'))
            ident = f'notification-{u:02}-{i:02}'
            items.append(dict(PK=pk,SK='NOTIFICATION#'+ident,id=ident,titulo=('Próximo vencimiento','Resumen de ingresos','Gastos del periodo')[i-1],
                              mensaje=('Revisa tu calendario de obligaciones.','Consulta tus ingresos y retenciones.','Revisa los gastos registrados en el periodo.')[i-1],
                              created_at=f'2026-09-{10+i:02}T12:00:00Z',es_urgente=i==1,origen='MANUAL'))
    return items


if __name__ == '__main__':
    path = ROOT / 'data' / 'seed.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(build_seed(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Seed local generado: 112 items, 3 perfiles, 90 comprobantes.')
