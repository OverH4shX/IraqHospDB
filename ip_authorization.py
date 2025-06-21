"""
نظام التحقق من الأجهزة المعتمدة عن طريق عنوان IP
تم تطويره لنظام قاعدة بيانات الرعاية الصحية المركزية في العراق
"""

import ipaddress
import logging
from functools import wraps
from flask import request, redirect, url_for, flash, session
from flask_login import current_user
from app import db
from models import AuthorizedDevice


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_client_ip():
    """
    الحصول على عنوان IP للعميل من الطلب HTTP
    يدعم التمرير من خلال الوسيط/البروكسي
    """
   
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        logger.debug(f"عنوان IP من X-Forwarded-For: {ip}")
        return ip
    
 
    ip = request.remote_addr
    logger.debug(f"عنوان IP من remote_addr: {ip}")
    return ip

def is_authorized_ip(ip_address, hospital_id=None):
    """
    التحقق مما إذا كان عنوان IP معتمداً للوصول
    
    المعلمات:
    - ip_address: عنوان IP المراد التحقق منه
    - hospital_id: معرف المستشفى للتحقق من القيود على مستوى المستشفى (اختياري)
    
    العائد:
    - True إذا كان العنوان معتمداً، False خلاف ذلك
    """
    try:
    
        client_ip = ipaddress.ip_address(ip_address)
        
  
        local_ips = ['127.0.0.1', '::1', 'localhost', ]
        if str(client_ip) in local_ips:
            logger.debug(f"السماح للوصول المحلي من {ip_address}")
            return True
        
    
        query = AuthorizedDevice.query.filter_by(is_active=True)
        
     
        if hospital_id:
            query = query.filter_by(hospital_id=hospital_id)
        
      
        device = query.filter_by(ip_address=str(client_ip)).first()
        if device:
            logger.debug(f"تم العثور على جهاز معتمد: {device.device_name}")
            return True
        
   
        
        logger.warning(f"عنوان IP غير معتمد: {ip_address}")
        return False
        
    except Exception as e:
        logger.error(f"خطأ أثناء التحقق من عنوان IP: {e}")
   
        return False

def require_authorized_device(view_func):
    """
    مُزخرف (decorator) للتحقق من اعتماد الجهاز قبل الوصول إلى الطريقة (route)
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
       
        excluded_paths = ['/login', '/logout', '/static', '/error_unauthorized_device']
        if any(request.path.startswith(path) for path in excluded_paths):
            return view_func(*args, **kwargs)
        
        client_ip = get_client_ip()
        
     
        if current_user.is_authenticated:
            hospital_id = current_user.hospital_id
            
        
            if current_user.role == 'admin' and request.path.startswith('/devices'):
                logger.debug(f"مسؤول يصل إلى إدارة الأجهزة من {client_ip}")
                return view_func(*args, **kwargs)
            
            if is_authorized_ip(client_ip, hospital_id):
          
                device = AuthorizedDevice.query.filter_by(
                    ip_address=client_ip, 
                    hospital_id=hospital_id
                ).first()
                if device:
                    import datetime
                    device.last_access = datetime.datetime.utcnow()
                    db.session.commit()
                return view_func(*args, **kwargs)
        else:
         
            if is_authorized_ip(client_ip):
                return view_func(*args, **kwargs)
        
   
        session['client_ip'] = client_ip
        flash('هذا الجهاز غير مصرح له بالوصول إلى النظام', 'danger')
        return redirect(url_for('error_unauthorized_device'))
    
    return decorated_function

def add_authorized_device(ip_address, device_name, hospital_id, description=None, is_active=True):
    """
    إضافة جهاز معتمد جديد إلى قاعدة البيانات
    
    المعلمات:
    - ip_address: عنوان IP للجهاز
    - device_name: اسم وصفي للجهاز
    - hospital_id: معرف المستشفى الذي ينتمي إليه الجهاز
    - description: وصف اختياري للجهاز
    - is_active: هل الجهاز نشط (True) أم معطل (False)
    
    العائد:
    - كائن AuthorizedDevice إذا تمت الإضافة بنجاح، None في حالة الفشل
    """
    try:
      
        existing_device = AuthorizedDevice.query.filter_by(ip_address=ip_address).first()
        if existing_device:
            logger.warning(f"الجهاز بعنوان IP {ip_address} موجود بالفعل")
            return None
        
     
        new_device = AuthorizedDevice(
            ip_address=ip_address,
            device_name=device_name,
            description=description,
            hospital_id=hospital_id,
            is_active=is_active
        )
        
        db.session.add(new_device)
        db.session.commit()
        
        logger.info(f"تمت إضافة جهاز معتمد جديد: {device_name} ({ip_address})")
        return new_device
        
    except Exception as e:
        logger.error(f"خطأ أثناء إضافة جهاز معتمد: {e}")
        db.session.rollback()
        return None

def remove_authorized_device(device_id):
    """
    حذف جهاز معتمد من قاعدة البيانات
    
    المعلمات:
    - device_id: معرف الجهاز المراد حذفه
    
    العائد:
    - True إذا تم الحذف بنجاح، False خلاف ذلك
    """
    try:
        device = AuthorizedDevice.query.get(device_id)
        if not device:
            logger.warning(f"الجهاز بالمعرف {device_id} غير موجود")
            return False
        
        db.session.delete(device)
        db.session.commit()
        
        logger.info(f"تم حذف الجهاز: {device.device_name} ({device.ip_address})")
        return True
        
    except Exception as e:
        logger.error(f"خطأ أثناء حذف الجهاز: {e}")
        db.session.rollback()
        return False

def toggle_device_status(device_id):
    """
    تبديل حالة الجهاز (نشط/معطل)
    
    المعلمات:
    - device_id: معرف الجهاز المراد تغيير حالته
    
    العائد:
    - (True, الحالة الجديدة) إذا تم التغيير بنجاح، (False, None) خلاف ذلك
    """
    try:
        device = AuthorizedDevice.query.get(device_id)
        if not device:
            logger.warning(f"الجهاز بالمعرف {device_id} غير موجود")
            return False, None
        
     
        device.is_active = not device.is_active
        db.session.commit()
        
        new_status = "نشط" if device.is_active else "معطل"
        logger.info(f"تم تغيير حالة الجهاز {device.device_name} إلى {new_status}")
        return True, device.is_active
        
    except Exception as e:
        logger.error(f"خطأ أثناء تغيير حالة الجهاز: {e}")
        db.session.rollback()
        return False, None
