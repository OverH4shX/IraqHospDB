from app import app, db
from models import User, Hospital, Patient, ChronicDisease, MedicalTest, Surgery, AuthorizedDevice
from datetime import datetime, date
import logging

def initialize_database():
    """إنشاء بيانات أولية في قاعدة البيانات للاختبار"""
    
    try:
        with app.app_context():
          
            if Hospital.query.count() == 0:
                logging.info("إنشاء بيانات أولية للمستشفيات...")
                
            
                hospitals = [
                    Hospital(
                        name="Baghdad Medical City",
                        name_arabic="مدينة بغداد الطبية",
                        location="Baghdad, Iraq",
                        governorate="Baghdad",
                        phone="+964123456789",
                        email="info@baghdadmc.iq"
                    ),
                    Hospital(
                        name="Basra General Hospital",
                        name_arabic="مستشفى البصرة العام",
                        location="Basra, Iraq",
                        governorate="Basra",
                        phone="+964987654321",
                        email="info@basrahospital.iq"
                    ),
                    Hospital(
                        name="Mosul Teaching Hospital",
                        name_arabic="مستشفى الموصل التعليمي",
                        location="Mosul, Iraq",
                        governorate="Nineveh",
                        phone="+964123123123",
                        email="info@mosulteaching.iq"
                    )
                ]
                
                db.session.add_all(hospitals)
                db.session.commit()
                logging.info(f"تم إنشاء {len(hospitals)} مستشفيات")

         
            if User.query.count() == 0:
                logging.info("إنشاء حسابات مستخدمين...")
                
          
                admin_user = User(
                    username="admin",
                    email="admin@healthcare.iq",
                    full_name="System Administrator",
                    hospital_id=1,  
                    role="admin"
                )
                admin_user.set_password("admin123")  
                
                staff_user = User(
                    username="staff",
                    email="staff@healthcare.iq",
                    full_name="Staff User",
                    hospital_id=1,
                    role="staff"
                )
                staff_user.set_password("staff123")  
                
                db.session.add_all([admin_user, staff_user])
                db.session.commit()
                logging.info("تم إنشاء حسابات المستخدمين")
                
             
                local_device = AuthorizedDevice(
                    ip_address="127.0.0.1",
                    device_name="جهاز التطوير المحلي",
                    description="جهاز معتمد للتطوير والاختبار",
                    hospital_id=1,
                    is_active=True
                )
                
                db.session.add(local_device)
                db.session.commit()
                logging.info("تم إضافة جهاز معتمد للتطوير")
                
    except Exception as e:
        logging.error(f"حدث خطأ أثناء تهيئة قاعدة البيانات: {e}")
        db.session.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_database()
    logging.info("تمت تهيئة قاعدة البيانات بنجاح!")
