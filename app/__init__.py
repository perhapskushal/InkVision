from flask import Flask
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize PaddleOCR here to avoid multiple initializations
    from paddleocr import PaddleOCR
    app.ocr = PaddleOCR(use_angle_cls=True, lang='ne', show_log=False)

    from app.routes import main
    app.register_blueprint(main)

    return app