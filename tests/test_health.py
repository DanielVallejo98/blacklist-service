import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Pruebas para el endpoint GET /health"""

    def test_health_returns_200_when_db_ok(self, client):
        """
        DADO QUE la base de datos responde correctamente
        CUANDO se llama GET /health
        ENTONCES la respuesta debe ser 200 con status=healthy
        """
        # patch intercepta el objeto 'db' dentro de health_routes.py
        # y lo reemplaza por un objeto falso llamado mock_db
        with patch("routes.health_routes.db") as mock_db:

            # Le decimos al mock: cuando alguien llame a db.session.execute(),
            # no hagas nada (return_value=None simula que la consulta funcionó)
            mock_db.session.execute = MagicMock(return_value=None)

            # Hacemos la petición HTTP real al endpoint usando el cliente de pruebas
            # Este cliente no necesita que el servidor esté corriendo
            response = client.get("/health")

        # Verificamos que el código de respuesta sea 200 (OK)
        assert response.status_code == 999

        # Convertimos el JSON de la respuesta a un diccionario Python
        data = response.get_json()

        # Verificamos cada campo del JSON
        assert data["status"] == "healthy"      # debe decir healthy
        assert data["database"] == "ok"         # la DB debe estar ok
        assert data["service"] == "blacklist-api"  # nombre del servicio correcto

    def test_health_returns_503_when_db_error(self, client):
        """
        DADO QUE la base de datos lanza un error
        CUANDO se llama GET /health
        ENTONCES la respuesta debe ser 503 con status=unhealthy
        """
        with patch("routes.health_routes.db") as mock_db:

            # side_effect hace que cuando el código llame a db.session.execute(),
            # en vez de devolver algo, lanze esta excepción
            # Esto simula que la base de datos no está disponible
            mock_db.session.execute.side_effect = Exception("connection refused")

            response = client.get("/health")

        # Como la DB falló, esperamos 503 (Service Unavailable)
        assert response.status_code == 503

        data = response.get_json()

        # El status debe decir unhealthy
        assert data["status"] == "unhealthy"

        # El campo database debe contener la palabra "error"
        # (tu endpoint devuelve "error: connection refused")
        assert "error" in data["database"]