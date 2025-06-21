from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import ipaddress

class User(UserMixin, db.Model):
    """Model for hospital staff users"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class Hospital(db.Model):
    """Model for hospitals in Iraq"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_arabic = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    governorate = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    users = db.relationship('User', backref='hospital', lazy=True)
    patients = db.relationship('Patient', backref='registered_hospital', lazy=True)
    
    def __repr__(self):
        return f'<Hospital {self.name}>'

class Patient(db.Model):
    """Model for patient information"""
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    full_name_arabic = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_type = db.Column(db.String(10))
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
  
    chronic_diseases = db.relationship('ChronicDisease', backref='patient', lazy=True)
    medical_tests = db.relationship('MedicalTest', backref='patient', lazy=True)
    surgeries = db.relationship('Surgery', backref='patient', lazy=True)
    
    def __repr__(self):
        return f'<Patient {self.full_name}>'

class ChronicDisease(db.Model):
    """Model for chronic diseases of patients"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    disease_name = db.Column(db.String(100), nullable=False)
    disease_name_arabic = db.Column(db.String(100))
    diagnosis_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChronicDisease {self.disease_name} - Patient ID: {self.patient_id}>'

class MedicalTest(db.Model):
    """Model for medical tests of patients"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    test_name = db.Column(db.String(100), nullable=False)
    test_name_arabic = db.Column(db.String(100))
    test_date = db.Column(db.Date, nullable=False)
    test_result = db.Column(db.Text, nullable=False)
    normal_range = db.Column(db.String(100))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    doctor_name = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
  
    hospital = db.relationship('Hospital')
    
    def __repr__(self):
        return f'<MedicalTest {self.test_name} - Patient ID: {self.patient_id}>'

class Surgery(db.Model):
    """Model for surgeries of patients"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    surgery_name = db.Column(db.String(100), nullable=False)
    surgery_name_arabic = db.Column(db.String(100))
    surgery_date = db.Column(db.Date, nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    surgeon_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   
    hospital = db.relationship('Hospital')
    
    def __repr__(self):
        return f'<Surgery {self.surgery_name} - Patient ID: {self.patient_id}>'


class AuthorizedDevice(db.Model):
    """Model for authorized devices/IPs that can access the system"""
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)  
    device_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_access = db.Column(db.DateTime)
    
    
    hospital = db.relationship('Hospital', backref='authorized_devices')
    
    @staticmethod
    def is_ip_authorized(ip, hospital_id=None):
        """Check if an IP is authorized"""
        query = AuthorizedDevice.query.filter_by(ip_address=ip, is_active=True)
        if hospital_id:
            query = query.filter_by(hospital_id=hospital_id)
        return query.first() is not None
    
    @staticmethod
    def is_ip_in_network(ip, network_list):
        """Check if IP is in any of the authorized networks"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for network in network_list:
                try:
                    if ip_obj in ipaddress.ip_network(network):
                        return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False
    
    def __repr__(self):
        return f'<AuthorizedDevice {self.device_name} ({self.ip_address})>'
