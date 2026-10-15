"""Contraseñas con PBKDF2 y sesiones opacas: sin secretos de firma globales."""
import hashlib
import hmac
import re
import secrets
import time
import uuid

from service import ApiError, bad

ITERATIONS = 600000
SESSION_SECONDS = 7200


def email_normalize(value):
    if not isinstance(value, str) or not 3 <= len(value) <= 100:
        bad('Correo invalido')
    email = value.strip().lower()
    if not re.fullmatch(r'[a-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+', email):
        bad('Correo invalido')
    return email


def email_key(email):
    return 'EMAIL#' + hashlib.sha256(email.encode()).hexdigest()


def password_validate(value):
    if not isinstance(value, str) or not 12 <= len(value) <= 128:
        bad('La contraseña debe tener entre 12 y 128 caracteres')
    return value


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return {'salt': salt, 'password_hash': digest, 'iterations': ITERATIONS}


def password_matches(password, credentials):
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(credentials['salt']),
                                 int(credentials['iterations'])).hex()
    return hmac.compare_digest(digest, credentials['password_hash'])


class Auth:
    def __init__(self, repository, clock=time.time):
        self.repo, self.clock = repository, clock

    def session(self, user):
        token = secrets.token_urlsafe(32)
        expires = int(self.clock()) + SESSION_SECONDS
        key = 'SESSION#' + hashlib.sha256(token.encode()).hexdigest()
        self.repo.auth_put({'PK':key,'SK':'SESSION','user_id':user,'expires_at':expires})
        return {'access_token':token,'token_type':'Bearer','expires_in':SESSION_SECONDS,
                'user':self.repo.get(user,'PROFILE')}

    def authenticate(self, headers):
        value = headers.get('authorization', '')
        if not isinstance(value,str) or not re.fullmatch(r'Bearer [A-Za-z0-9_-]{43}',value):
            raise ApiError(401,'UNAUTHENTICATED','Inicia sesion para continuar')
        key='SESSION#'+hashlib.sha256(value[7:].encode()).hexdigest()
        session=self.repo.auth_get(key,'SESSION')
        if not session or session['expires_at'] <= int(self.clock()):
            raise ApiError(401,'UNAUTHENTICATED','La sesion no es valida o ha expirado')
        return session['user_id'],key

    def dispatch(self, route, body, headers):
        if route=='logout':
            _, key=self.authenticate(headers)
            self.repo.auth_delete(key,'SESSION')
            return {'ok':True}
        fields={'email','password','nombre'} if route=='register' else {'email','password'}
        if not isinstance(body,dict) or set(body)!=fields:
            bad('Campos de autenticacion invalidos')
        email=email_normalize(body['email'])
        password=password_validate(body['password'])
        pk=email_key(email)
        if route=='register':
            name=body['nombre']
            if not isinstance(name,str) or not 2<=len(name.strip())<=150:
                bad('Nombre invalido')
            user='user-'+uuid.uuid4().hex
            profile={'id':user,'nombre':name.strip(),'email':email,'profesion':'',
                     'ultimo_digito_ruc':None}
            creds=dict(password_hash(password),user_id=user)
            try:
                self.repo.create_account(pk,creds,profile)
            except Exception as error:
                if getattr(error,'response',{}).get('Error',{}).get('Code') in ('TransactionCanceledException','ConditionalCheckFailedException'):
                    # Verificar colision real de email; no esconder otros errores de transaccion.
                    if self.repo.auth_get(pk,'CREDENTIALS'):
                        raise ApiError(409,'EMAIL_ALREADY_EXISTS','El correo ya esta registrado')
                raise
            return self.session(user)
        creds=self.repo.auth_get(pk,'CREDENTIALS')
        # Trabajo PBKDF2 comparable incluso para un correo inexistente.
        candidate=creds or {'salt':'00'*16,'iterations':ITERATIONS,'password_hash':'00'*32}
        valid=password_matches(password,candidate)
        if not creds or not valid:
            raise ApiError(401,'INVALID_CREDENTIALS','Correo o contraseña incorrectos')
        return self.session(creds['user_id'])
