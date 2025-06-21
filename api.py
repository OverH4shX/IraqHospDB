"""
نظام واجهة برمجة التطبيقات (API) للتطبيق المصاحب للهاتف المحمول
تم تطويره لنظام قاعدة بيانات الرعاية الصحية المركزية في العراق
"""

import os
import jwt
import json
import logging
import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from app import db
from models import User, Patient, MedicalTest, Surgery, ChronicDisease, Hospital, AuthorizedDevice
from ip_authorization import get_client_ip, is_authorized_ip


api_bp = Blueprint('api', __name__, url_prefix='/api')


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "default_jwt_secret_key_for_development")
JWT_EXPIRATION = datetime.timedelta(days=1)  # صلاحية الرمز ليوم واحد



def token_required(f):
    """
    مزخرف (decorator) للتحقق من صحة رمز JWT في طلبات API
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
   
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'رمز المصادقة غير صالح'}), 401
        
        if not token:
            return jsonify({'message': 'رمز المصادقة مفقود!'}), 401
        
        try:
       
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'المستخدم غير موجود!'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'انتهت صلاحية رمز المصادقة!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'رمز المصادقة غير صالح!'}), 401
        
     
        return f(current_user, *args, **kwargs)
    
    return decorated

def device_auth_required(f):
    """
    مزخرف (decorator) للتحقق من الجهاز المعتمد في طلبات API
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        client_ip = get_client_ip()
        
    
        if not is_authorized_ip(client_ip, current_user.hospital_id):
            return jsonify({
                'message': 'هذا الجهاز غير مصرح له بالوصول إلى النظام',
                'client_ip': client_ip
            }), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated



@api_bp.route('/login', methods=['POST'])
def login():
    """
    مسار تسجيل الدخول وإصدار رمز JWT
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'بيانات غير مكتملة!'}), 400
        
        user = User.query.filter_by(username=data.get('username')).first()
        
        if not user or not user.check_password(data.get('password')):
            return jsonify({'message': 'اسم المستخدم أو كلمة المرور غير صحيحة!'}), 401
        
   
        token_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'hospital_id': user.hospital_id,
            'exp': datetime.datetime.utcnow() + JWT_EXPIRATION
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm="HS256")
        
     
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role,
                'hospital_id': user.hospital_id,
                'hospital_name': user.hospital.name_arabic
            }
        }), 200
        
    except Exception as e:
        logger.error(f"خطأ في تسجيل الدخول: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/patients', methods=['GET'])
@token_required
@device_auth_required
def get_patients(current_user):
    """
    الحصول على قائمة المرضى في المستشفى
    """
    try:
    
        search_query = request.args.get('q', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
    
        query = Patient.query.filter_by(hospital_id=current_user.hospital_id)
        
     
        if search_query:
            query = query.filter((Patient.full_name.ilike(f'%{search_query}%')) | 
                                (Patient.full_name_arabic.ilike(f'%{search_query}%')) |
                                (Patient.national_id.ilike(f'%{search_query}%')))
        
    
        patients = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=per_page)
        

        result = {
            'total': patients.total,
            'pages': patients.pages,
            'current_page': patients.page,
            'per_page': per_page,
            'patients': [{
                'id': patient.id,
                'full_name': patient.full_name,
                'full_name_arabic': patient.full_name_arabic,
                'national_id': patient.national_id,
                'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
                'gender': patient.gender,
                'blood_type': patient.blood_type,
                'phone': patient.phone
            } for patient in patients.items]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب المرضى: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500

@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
@token_required
@device_auth_required
def get_patient(current_user, patient_id):
    """
    الحصول على معلومات مريض محدد
    """
    try:
      
        patient = Patient.query.filter_by(id=patient_id, hospital_id=current_user.hospital_id).first()
        
        if not patient:
            return jsonify({'message': 'المريض غير موجود!'}), 404
        
     
        patient_data = {
            'id': patient.id,
            'full_name': patient.full_name,
            'full_name_arabic': patient.full_name_arabic,
            'national_id': patient.national_id,
            'date_of_birth': patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else None,
            'gender': patient.gender,
            'blood_type': patient.blood_type,
            'phone': patient.phone,
            'address': patient.address,
            'emergency_contact': patient.emergency_contact,
            'emergency_phone': patient.emergency_phone,
            'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': patient.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            
         
            'chronic_diseases': [{
                'id': disease.id,
                'disease_name': disease.disease_name,
                'disease_name_arabic': disease.disease_name_arabic,
                'diagnosis_date': disease.diagnosis_date.strftime('%Y-%m-%d') if disease.diagnosis_date else None,
                'notes': disease.notes
            } for disease in patient.chronic_diseases],
            
            'medical_tests': [{
                'id': test.id,
                'test_name': test.test_name,
                'test_name_arabic': test.test_name_arabic,
                'test_date': test.test_date.strftime('%Y-%m-%d') if test.test_date else None,
                'test_result': test.test_result,
                'normal_range': test.normal_range,
                'doctor_name': test.doctor_name,
                'notes': test.notes,
                'hospital_name': test.hospital.name_arabic if test.hospital else ''
            } for test in patient.medical_tests],
            
            'surgeries': [{
                'id': surgery.id,
                'surgery_name': surgery.surgery_name,
                'surgery_name_arabic': surgery.surgery_name_arabic,
                'surgery_date': surgery.surgery_date.strftime('%Y-%m-%d') if surgery.surgery_date else None,
                'surgeon_name': surgery.surgeon_name,
                'description': surgery.description,
                'notes': surgery.notes,
                'hospital_name': surgery.hospital.name_arabic if surgery.hospital else ''
            } for surgery in patient.surgeries]
        }
        
        return jsonify(patient_data), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب معلومات المريض: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500

@api_bp.route('/patients', methods=['POST'])
@token_required
@device_auth_required
def add_patient(current_user):
    """
    إضافة مريض جديد
    """
    try:
        data = request.get_json()
        
      
        required_fields = ['full_name', 'full_name_arabic', 'gender', 'date_of_birth', 'phone']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'الحقل {field} مطلوب!'}), 400
        

        if data.get('national_id'):
            existing_patient = Patient.query.filter_by(national_id=data['national_id']).first()
            if existing_patient:
                return jsonify({'message': 'يوجد مريض مسجل بنفس الرقم الوطني!'}), 400
        
   
        date_of_birth = datetime.datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        
 
        new_patient = Patient(
            full_name=data['full_name'],
            full_name_arabic=data['full_name_arabic'],
            national_id=data.get('national_id'),
            date_of_birth=date_of_birth,
            gender=data['gender'],
            blood_type=data.get('blood_type'),
            phone=data['phone'],
            address=data.get('address'),
            emergency_contact=data.get('emergency_contact'),
            emergency_phone=data.get('emergency_phone'),
            hospital_id=current_user.hospital_id
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
  
        return jsonify({
            'message': 'تم إضافة المريض بنجاح',
            'patient_id': new_patient.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطأ في إضافة مريض جديد: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/patients/<int:patient_id>/tests', methods=['POST'])
@token_required
@device_auth_required
def add_test(current_user, patient_id):
    """
    إضافة فحص طبي جديد للمريض
    """
    try:
        data = request.get_json()
        
    
        patient = Patient.query.filter_by(id=patient_id, hospital_id=current_user.hospital_id).first()
        if not patient:
            return jsonify({'message': 'المريض غير موجود!'}), 404
        
    
        required_fields = ['test_name', 'test_date', 'test_result']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'الحقل {field} مطلوب!'}), 400
        
  
        test_date = datetime.datetime.strptime(data['test_date'], '%Y-%m-%d').date()
        
     
        new_test = MedicalTest(
            patient_id=patient_id,
            test_name=data['test_name'],
            test_name_arabic=data.get('test_name_arabic'),
            test_date=test_date,
            test_result=data['test_result'],
            normal_range=data.get('normal_range'),
            doctor_name=data.get('doctor_name'),
            notes=data.get('notes'),
            hospital_id=current_user.hospital_id
        )
        
        db.session.add(new_test)
        db.session.commit()
        
        return jsonify({
            'message': 'تم إضافة الفحص الطبي بنجاح',
            'test_id': new_test.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطأ في إضافة فحص طبي: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/patients/<int:patient_id>/diseases', methods=['POST'])
@token_required
@device_auth_required
def add_disease(current_user, patient_id):
    """
    إضافة مرض مزمن للمريض
    """
    try:
        data = request.get_json()
        
     
        patient = Patient.query.filter_by(id=patient_id, hospital_id=current_user.hospital_id).first()
        if not patient:
            return jsonify({'message': 'المريض غير موجود!'}), 404
        
     
        if 'disease_name' not in data:
            return jsonify({'message': 'اسم المرض مطلوب!'}), 400
        
    
        diagnosis_date = None
        if data.get('diagnosis_date'):
            diagnosis_date = datetime.datetime.strptime(data['diagnosis_date'], '%Y-%m-%d').date()
        
    
        new_disease = ChronicDisease(
            patient_id=patient_id,
            disease_name=data['disease_name'],
            disease_name_arabic=data.get('disease_name_arabic'),
            diagnosis_date=diagnosis_date,
            notes=data.get('notes')
        )
        
        db.session.add(new_disease)
        db.session.commit()
        
        return jsonify({
            'message': 'تم إضافة المرض المزمن بنجاح',
            'disease_id': new_disease.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطأ في إضافة مرض مزمن: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/patients/<int:patient_id>/surgeries', methods=['POST'])
@token_required
@device_auth_required
def add_surgery(current_user, patient_id):
    """
    إضافة عملية جراحية للمريض
    """
    try:
        data = request.get_json()
        
       
        patient = Patient.query.filter_by(id=patient_id, hospital_id=current_user.hospital_id).first()
        if not patient:
            return jsonify({'message': 'المريض غير موجود!'}), 404
        
  
        required_fields = ['surgery_name', 'surgery_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'الحقل {field} مطلوب!'}), 400
        
      
        surgery_date = datetime.datetime.strptime(data['surgery_date'], '%Y-%m-%d').date()
        
    
        new_surgery = Surgery(
            patient_id=patient_id,
            surgery_name=data['surgery_name'],
            surgery_name_arabic=data.get('surgery_name_arabic'),
            surgery_date=surgery_date,
            surgeon_name=data.get('surgeon_name'),
            description=data.get('description'),
            notes=data.get('notes'),
            hospital_id=current_user.hospital_id
        )
        
        db.session.add(new_surgery)
        db.session.commit()
        
        return jsonify({
            'message': 'تم إضافة العملية الجراحية بنجاح',
            'surgery_id': new_surgery.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"خطأ في إضافة عملية جراحية: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/hospitals', methods=['GET'])
@token_required
def get_hospitals(current_user):
    """
    الحصول على قائمة المستشفيات
    """
    try:
        hospitals = Hospital.query.all()
        
        hospitals_list = [{
            'id': hospital.id,
            'name': hospital.name,
            'name_arabic': hospital.name_arabic,
            'location': hospital.location,
            'governorate': hospital.governorate,
            'phone': hospital.phone,
            'email': hospital.email
        } for hospital in hospitals]
        
        return jsonify(hospitals_list), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب المستشفيات: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500



@api_bp.route('/stats', methods=['GET'])
@token_required
@device_auth_required
def get_hospital_stats(current_user):
    """
    الحصول على إحصائيات المستشفى
    """
    try:
   
        total_patients = Patient.query.filter_by(hospital_id=current_user.hospital_id).count()
        total_tests = MedicalTest.query.filter_by(hospital_id=current_user.hospital_id).count()
        total_surgeries = Surgery.query.filter_by(hospital_id=current_user.hospital_id).count()
        
     
        blood_types = db.session.query(
            Patient.blood_type, db.func.count(Patient.id)
        ).filter(
            Patient.hospital_id == current_user.hospital_id,
            Patient.blood_type.isnot(None)
        ).group_by(Patient.blood_type).all()
        
        blood_type_data = {bt[0]: bt[1] for bt in blood_types}
        
   
        gender_distribution = db.session.query(
            Patient.gender, db.func.count(Patient.id)
        ).filter(
            Patient.hospital_id == current_user.hospital_id
        ).group_by(Patient.gender).all()
        
        gender_data = {gender[0]: gender[1] for gender in gender_distribution}
        
        stats = {
            'total_patients': total_patients,
            'total_tests': total_tests,
            'total_surgeries': total_surgeries,
            'blood_type_distribution': blood_type_data,
            'gender_distribution': gender_data
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"خطأ في جلب إحصائيات المستشفى: {e}")
        return jsonify({'message': 'حدث خطأ في النظام'}), 500
