import pytest
from unittest.mock import patch, MagicMock


# Payload válido que reutilizamos en varias pruebas
# Es un email de ejemplo con todos los campos requeridos
VALID_PAYLOAD = {
    "email": "spammer@evil.com",
    "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "blocked_reason": "spam",
}


class TestPostBlacklist:
    """Pruebas para el endpoint POST /blacklists"""

    def test_add_email_success_returns_201(self, client, auth_headers):
        """
        DADO QUE el email no existe en la lista negra y el token es válido
        CUANDO se hace POST /blacklists con datos correctos
        ENTONCES la respuesta debe ser 201 con el id del registro creado
        """
        # Usamos 3 patches simultáneos:
        # 1. verify_token → siempre devuelve True (token válido)
        # 2. BlacklistEntry → reemplaza el modelo de base de datos
        # 3. db → reemplaza la sesión de base de datos
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model, \
             patch("routes.blacklist_routes.db") as mock_db:

            # Simulamos que el email NO existe en la DB todavía
            # .first() devuelve None = no encontrado
            mock_model.query.filter_by.return_value.first.return_value = None

            # Creamos un objeto falso que simula el nuevo registro creado
            mock_instance = MagicMock()
            mock_instance.id = 42                        # id que devolvería la DB
            mock_instance.email = VALID_PAYLOAD["email"] # email del registro
            mock_model.return_value = mock_instance       # cuando se llame BlacklistEntry(...) devuelve esto

            # Simulamos que db.session.add() y commit() funcionan sin errores
            mock_db.session.add.return_value = None
            mock_db.session.commit.return_value = None

            response = client.post("/blacklists", json=VALID_PAYLOAD, headers=auth_headers)

        # Debe devolver 201 Created
        assert response.status_code == 201
        data = response.get_json()

        # La respuesta debe tener un campo "id"
        assert "id" in data

        # El mensaje debe mencionar el email
        assert VALID_PAYLOAD["email"] in data["msg"]

    def test_add_email_without_token_returns_401(self, client):
        """
        DADO QUE no se envía el header Authorization
        CUANDO se hace POST /blacklists
        ENTONCES la respuesta debe ser 401 Unauthorized
        """
        # No pasamos auth_headers — la petición va sin token
        response = client.post("/blacklists", json=VALID_PAYLOAD)

        # Sin token debe rechazar con 401
        assert response.status_code == 401

    def test_add_email_with_invalid_token_returns_401(self, client):
        """
        DADO QUE se envía un token Bearer incorrecto
        CUANDO se hace POST /blacklists
        ENTONCES la respuesta debe ser 401 Unauthorized
        """
        response = client.post(
            "/blacklists",
            json=VALID_PAYLOAD,
            # Token diferente al configurado en conftest.py
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_add_duplicate_email_returns_409(self, client, auth_headers):
        """
        DADO QUE el email ya existe en la lista negra
        CUANDO se hace POST /blacklists con ese mismo email
        ENTONCES la respuesta debe ser 409 Conflict
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            # Simulamos que el email YA existe en la DB
            # .first() devuelve un objeto (no None) = ya existe
            mock_model.query.filter_by.return_value.first.return_value = MagicMock()

            response = client.post("/blacklists", json=VALID_PAYLOAD, headers=auth_headers)

        # Como ya existe, debe devolver 409 Conflict
        assert response.status_code == 409

    def test_add_email_with_non_json_body_returns_400(self, client, auth_headers):
        """
        DADO QUE el cuerpo de la petición no es JSON
        CUANDO se hace POST /blacklists
        ENTONCES la respuesta debe ser 400 Bad Request
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True):
            response = client.post(
                "/blacklists",
                data="not json at all",       # texto plano, no JSON
                content_type="text/plain",    # tipo de contenido incorrecto
                headers=auth_headers,
            )
        # El endpoint no puede parsear el body → 400
        assert response.status_code == 400

    def test_add_email_missing_required_field_returns_400(self, client, auth_headers):
        """
        DADO QUE el payload no tiene el campo requerido app_uuid
        CUANDO se hace POST /blacklists
        ENTONCES la respuesta debe ser 400 con errores de validación
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            mock_model.query.filter_by.return_value.first.return_value = None

            response = client.post(
                "/blacklists",
                # Solo enviamos email, falta app_uuid que es obligatorio
                json={"email": "test@test.com"},
                headers=auth_headers,
            )
        # Marshmallow detecta el campo faltante → 400
        assert response.status_code == 400


class TestGetBlacklist:
    """Pruebas para el endpoint GET /blacklists/<email>"""

    def test_get_blacklisted_email_returns_true(self, client, auth_headers):
        """
        DADO QUE el email SÍ está en la lista negra
        CUANDO se hace GET /blacklists/<email>
        ENTONCES la respuesta debe ser 200 con is_blacklisted=True
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            # Creamos un objeto falso que simula el registro encontrado en DB
            mock_entry = MagicMock()
            mock_entry.email = "spammer@evil.com"
            mock_entry.blocked_reason = "spam"
            mock_entry.app_uuid = "550e8400-e29b-41d4-a716-446655440000"
            # isoformat() convierte datetime a string — simulamos esa conversión
            mock_entry.created_at.isoformat.return_value = "2024-01-01T00:00:00"

            # Cuando el endpoint busque el email, devuelve nuestro objeto falso
            mock_model.query.filter_by.return_value.first.return_value = mock_entry

            response = client.get("/blacklists/spammer@evil.com", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # El email SÍ está bloqueado
        assert data["is_blacklisted"] is True
        assert data["email"] == "spammer@evil.com"

    def test_get_clean_email_returns_false(self, client, auth_headers):
        """
        DADO QUE el email NO está en la lista negra
        CUANDO se hace GET /blacklists/<email>
        ENTONCES la respuesta debe ser 200 con is_blacklisted=False
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            # .first() devuelve None = email no encontrado en la DB
            mock_model.query.filter_by.return_value.first.return_value = None

            response = client.get("/blacklists/clean@safe.com", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # El email NO está bloqueado
        assert data["is_blacklisted"] is False
        assert data["blocked_reason"] is None

    def test_get_email_without_token_returns_401(self, client):
        """
        DADO QUE no se envía el header Authorization
        CUANDO se hace GET /blacklists/<email>
        ENTONCES la respuesta debe ser 401 Unauthorized
        """
        # Sin token → debe rechazar
        response = client.get("/blacklists/anyone@test.com")
        assert response.status_code == 401