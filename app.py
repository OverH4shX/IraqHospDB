import os
import logging

from flask import Flask, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user


logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///healthcare.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'

with app.app_context():

    import models 
    
 
    db.create_all()
    
   
    from init_db import initialize_database
    initialize_database()


from models import User, AuthorizedDevice

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


from ip_authorization import get_client_ip, is_authorized_ip, require_authorized_device


@app.before_request
def check_device_authorization():

    if (request.path.startswith('/static') or 
        request.path == '/login' or 
        request.path == '/logout' or
        request.path.startswith('/error')):
        return
    
    client_ip = get_client_ip()
    logging.debug(f"Client IP: {client_ip}")
    

    if client_ip in ['127.0.0.1', 'localhost', '::1']:
        logging.debug(f"Development access from {client_ip} allowed")
        return
    # ====================================================
    
   
    if current_user.is_authenticated:
        hospital_id = current_user.hospital_id
        
   
        if current_user.role == 'admin' and request.path.startswith('/devices'):
            logging.debug(f"Admin access to device management from {client_ip} allowed")
            return
            
        if is_authorized_ip(client_ip, hospital_id):
         
            device = AuthorizedDevice.query.filter_by(
                ip_address=client_ip, 
                hospital_id=hospital_id
            ).first()
            if device:
                import datetime
                device.last_access = datetime.datetime.utcnow()
                db.session.commit()
            logging.debug(f"Authorized access from {client_ip}")
            return
        
        logging.warning(f"Unauthorized access attempt from {client_ip}")
        flash('هذا الجهاز غير مصرح له بالوصول إلى النظام', 'danger')
        return redirect(url_for('error_unauthorized_device'))
