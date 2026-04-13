from flask import Blueprint, jsonify
from extensions import db

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Endpoint de health check para AWS Elastic Beanstalk.
    Verifica conectividad con la base de datos.
    Flask-SQLAlchemy 2.5.x / SQLAlchemy 1.x: se usa string directo en execute().
    """
    try:
        db.session.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = "error: {}".format(str(e))

    status = "healthy" if db_status == "ok" else "unhealthy"
    code   = 200 if db_status == "ok" else 503

    return jsonify({
        "status":   status,
        "database": db_status,
        "service":  "blacklist-api"
    }), code
