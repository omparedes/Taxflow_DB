"""Persistencia de datos, cuentas y sesiones; SDK del runtime Lambda."""
import os
from decimal import Decimal


def clean(value):
    if isinstance(value, Decimal):
        if value != value.to_integral_value():
            raise ValueError('Dataset contiene un decimal no entero')
        return int(value)
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in ('PK', 'SK')}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


class DynamoRepository:
    def __init__(self):
        import boto3
        self.table = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])
        self.client = boto3.client('dynamodb')

    def auth_get(self, pk, sk):
        item = self.table.get_item(Key={'PK': pk, 'SK': sk}, ConsistentRead=True).get('Item')
        return clean(item) if item else None

    def auth_put(self, item):
        self.table.put_item(Item=item)

    def auth_delete(self, pk, sk):
        self.table.delete_item(Key={'PK': pk, 'SK': sk})

    def create_account(self, email_key, credentials, profile):
        from boto3.dynamodb.types import TypeSerializer
        serializer = TypeSerializer()
        def encode(item):
            return {key:serializer.serialize(value) for key,value in item.items()}
        # Une la reserva de email con el perfil; no pueden quedar cuentas parciales.
        self.client.transact_write_items(TransactItems=[
            {'Put': {'TableName': self.table.name, 'Item': encode(dict(credentials, PK=email_key, SK='CREDENTIALS')),
                     'ConditionExpression': 'attribute_not_exists(PK)'}},
            {'Put': {'TableName': self.table.name, 'Item': encode(dict(profile, PK='USER#'+profile['id'], SK='PROFILE')),
                     'ConditionExpression': 'attribute_not_exists(PK)'}}])

    def get(self, user_id, key):
        item = self.table.get_item(Key={'PK': 'USER#' + user_id, 'SK': key},
                                   ConsistentRead=True).get('Item')
        return clean(item) if item else None

    def rules(self):
        item = self.table.get_item(Key={'PK': 'DEMO', 'SK': 'RULES#demo-v1'},
                                   ConsistentRead=True).get('Item')
        return clean(item) if item else None

    def query(self, user_id, kind):
        args = dict(KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                    ExpressionAttributeValues={':pk': 'USER#' + user_id, ':sk': kind + '#'},
                    ConsistentRead=True)
        items = []
        while True:
            result = self.table.query(**args)
            items.extend(clean(x) for x in result.get('Items', []))
            # Dataset fijo; impedir crecimiento accidental sin cambiar contrato.
            if len(items) > 100:
                raise ValueError('Coleccion demo excede 100 registros')
            last = result.get('LastEvaluatedKey')
            if not last:
                return items
            args['ExclusiveStartKey'] = last
