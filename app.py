from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')  # e.g. SECRET_KEY

    # import & register blueprints
    from auth.routes import auth_bp
    from main.routes import main_bp

    app.register_blueprint(auth_bp)               # mounts at /
    app.register_blueprint(main_bp, url_prefix='')# mounts at /add, /edit, /transactions, etc.

    return app

if __name__ == '__main__':
    create_app().run(debug=True, port=5001)
