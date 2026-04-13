from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from marshmallow import ValidationError
from models.blacklist import BlacklistEntry
from schemas.blacklist_schema import BlacklistEntrySchema, BlacklistResponseSchema
from extensions import db
from config import Config

blacklist_bp = Blueprint("blacklist", __name__)
api = Api(blacklist_bp)

entry_schema    = BlacklistEntrySchema()
response_schema = BlacklistResponseSchema()


def verify_token():
    """Valida el Bearer token estático."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    token = auth_header.split(" ", 1)[1]
    return token == Config.STATIC_TOKEN


class BlacklistResource(Resource):
    """POST /blacklists — Agrega un email a la lista negra."""

    def post(self):
        if not verify_token():
            return {"msg": "Token de autorización inválido o ausente."}, 401

        json_data = request.get_json(silent=True)
        if not json_data:
            return {"msg": "El cuerpo de la solicitud debe ser JSON."}, 400

        # Validar y deserializar
        try:
            data = entry_schema.load(json_data)
        except ValidationError as err:
            return {"msg": "Datos inválidos.", "errors": err.messages}, 400

        # Verificar si el email ya existe
        existing = BlacklistEntry.query.filter_by(email=json_data["email"]).first()
        if existing:
            return {"msg": f"El email '{json_data['email']}' ya está en la lista negra."}, 409

        # Capturar IP del cliente (considera proxy reverso)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if client_ip and "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Crear entrada
        new_entry = BlacklistEntry(
            email          = json_data["email"],
            app_uuid       = json_data["app_uuid"],
            blocked_reason = json_data.get("blocked_reason"),
            request_ip     = client_ip or "unknown"
        )

        db.session.add(new_entry)
        db.session.commit()

        return {
            "msg": f"El email '{new_entry.email}' fue agregado a la lista negra exitosamente.",
            "id":  new_entry.id
        }, 201


class BlacklistQueryResource(Resource):
    """GET /blacklists/<email> — Consulta si un email está en la lista negra."""

    def get(self, email):
        if not verify_token():
            return {"msg": "Token de autorización inválido o ausente."}, 401

        entry = BlacklistEntry.query.filter_by(email=email).first()

        if entry:
            return {
                "is_blacklisted": True,
                "email":          entry.email,
                "blocked_reason": entry.blocked_reason,
                "app_uuid":       entry.app_uuid,
                "created_at":     entry.created_at.isoformat()
            }, 200
        else:
            return {
                "is_blacklisted": False,
                "email":          email,
                "blocked_reason": None
            }, 200


api.add_resource(BlacklistResource,      "/blacklists")
api.add_resource(BlacklistQueryResource, "/blacklists/<string:email>")
