from flask import Flask, redirect
from app.config import Config
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)
    
    # 简化CORS配置
    CORS(app, resources=r'/*')

    @app.route('/')
    def index():
        return redirect('/auth/login')
    
    from .routes.qa.routes import qa_bp
    app.register_blueprint(qa_bp, url_prefix='/qa')
    
    from .routes.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    for rule in app.url_map.iter_rules():
        print(rule)

    return app
