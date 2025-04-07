import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db
from werkzeug.middleware.proxy_fix import ProxyFix

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import routes after app creation to avoid circular imports
    from app import routes
    
    # Create database tables
    db.create_all()
    
    # Import models to ensure they're registered with SQLAlchemy
    import models

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
