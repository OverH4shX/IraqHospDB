from app import app, db
from models import User, Hospital
import logging

def create_new_user(username, email, full_name, password, hospital_id, role='staff'):
    """إنشاء مستخدم جديد"""
    try:
        with app.app_context():
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                logging.warning(f"المستخدم {username} موجود بالفعل!")
                return False
                
            
            hospital = Hospital.query.get(hospital_id)
            if not hospital:
                logging.error(f"المستشفى برقم {hospital_id} غير موجود!")
                return False
                
         
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                hospital_id=hospital_id,
                role=role
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            logging.info(f"تم إنشاء المستخدم {username} بنجاح!")
            return True
            
    except Exception as e:
        logging.error(f"حدث خطأ أثناء إنشاء المستخدم: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
  
    create_new_user(
        username="admin_basra",
        email="admin@basra.hospital.iq",
        full_name="مدير مستشفى البصرة",
        password="secure_password",  
        hospital_id=2,  
        role="admin"
    )
    
  
    create_new_user(
        username="doctor_ahmed",
        email="ahmed@baghdad.hospital.iq",
        full_name="الدكتور أحمد علي",
        password="doctor_password", 
        hospital_id=1, 
        role="staff"
    )
