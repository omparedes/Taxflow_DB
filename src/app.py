"""HTTP API payload 2.0. Logs sin cuerpos ni datos de usuarios."""
import base64
import json
import logging
from urllib.parse import parse_qsl

from repository import DynamoRepository
from service import ApiError, Service, bad

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_service = None


def handler(event, context):
    global _service
    request_id = getattr(context, 'aws_request_id', 'local')
    status = 200
    try:
        http = event.get('requestContext', {}).get('http', {})
        method, path = http.get('method', ''), event.get('rawPath', '')
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        pairs = parse_qsl(event.get('rawQueryString', ''), keep_blank_values=True)
        if len({k for k, _ in pairs}) != len(pairs):
            bad('Parametros duplicados')
        params = dict(pairs)
        body = None
        if method == 'POST':
            if headers.get('content-type', '').split(';')[0].strip().lower() != 'application/json':
                bad('Content-Type application/json requerido')
            raw = event.get('body') or ''
            if len(raw) > 8192:
                bad('Cuerpo excede limite demo')
            try:
                if event.get('isBase64Encoded'):
                    raw = base64.b64decode(raw, validate=True).decode('utf-8')
                def unique_object(pairs):
                    result = {}
                    for k, v in pairs:
                        if k in result:
                            bad('Campos JSON duplicados')
                        result[k] = v
                    return result
                body = json.loads(raw, object_pairs_hook=unique_object,
                                  parse_constant=lambda _: bad('JSON no finito'))
            except (ValueError, UnicodeError):
                bad('JSON invalido')
        if _service is None:
            _service = Service(DynamoRepository())
        payload = _service.dispatch(method, path, params, body, headers)
    except ApiError as error:
        status = error.status
        payload = {'error': dict(code=error.code, message=error.message, request_id=request_id)}
    except Exception as error:
        code = getattr(error, 'response', {}).get('Error', {}).get('Code', '')
        status = 503 if code in ('ProvisionedThroughputExceededException', 'ThrottlingException', 'RequestLimitExceeded', 'InternalServerError') else 500
        payload = {'error': dict(code='UNAVAILABLE' if status == 503 else 'INTERNAL_ERROR',
                                 message='Servicio temporalmente no disponible', request_id=request_id)}
        logger.error(json.dumps({'request_id': request_id, 'status': status, 'exception_type': type(error).__name__}))
    logger.info(json.dumps({'request_id': request_id, 'status': status}))
    return dict(statusCode=status, headers={'content-type': 'application/json; charset=utf-8',
                                           'cache-control': 'no-store'},
                body=json.dumps(payload, ensure_ascii=False, allow_nan=False))
