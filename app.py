from flask import Flask
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db, ma
from routes.blacklist_routes import blacklist_bp
from routes.health_routes import health_bp
 
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
 
    db.init_app(app)
    ma.init_app(app)
    JWTManager(app)
 
    app.register_blueprint(blacklist_bp)
    app.register_blueprint(health_bp)
 
    with app.app_context():
        db.create_all()
 
    return app
 
app = create_app()
###
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)