import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from app import app, db
from models import User, Hospital, Patient, ChronicDisease, MedicalTest, Surgery, AuthorizedDevice
from ip_authorization import get_client_ip, add_authorized_device, remove_authorized_device, toggle_device_status


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('خطأ في اسم المستخدم أو كلمة المرور', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=remember)
        next_page = request.args.get('next')
        if not next_page or next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
        
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    
    hospitals = Hospital.query.all()
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        hospital_id = request.form.get('hospital_id')
        
       
        if not username or not email or not password or not full_name or not hospital_id:
            flash('جميع الحقول مطلوبة', 'danger')
            return render_template('register.html', hospitals=hospitals)
            
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة', 'danger')
            return render_template('register.html', hospitals=hospitals)
            
        
        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل', 'danger')
            return render_template('register.html', hospitals=hospitals)
            
        
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            hospital_id=hospital_id,
            role='staff'
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('تم إنشاء الحساب بنجاح، يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error registering user: {e}")
            flash('حدث خطأ أثناء إنشاء الحساب', 'danger')
            
    return render_template('register.html', hospitals=hospitals)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    
    patient_count = Patient.query.filter_by(hospital_id=current_user.hospital_id).count()
    tests_count = MedicalTest.query.filter_by(hospital_id=current_user.hospital_id).count()
    surgeries_count = Surgery.query.filter_by(hospital_id=current_user.hospital_id).count()
    
   
    recent_patients = Patient.query.filter_by(hospital_id=current_user.hospital_id).order_by(Patient.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          patient_count=patient_count, 
                          tests_count=tests_count, 
                          surgeries_count=surgeries_count,
                          recent_patients=recent_patients)


@app.route('/patients/register', methods=['GET', 'POST'])
@login_required
def patient_register():
    if request.method == 'POST':
        try:
           
            full_name = request.form.get('full_name')
            full_name_arabic = request.form.get('full_name_arabic')
            national_id = request.form.get('national_id')
            date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            gender = request.form.get('gender')
            blood_type = request.form.get('blood_type')
            phone = request.form.get('phone')
            address = request.form.get('address')
            emergency_contact = request.form.get('emergency_contact')
            emergency_phone = request.form.get('emergency_phone')
            
          
            if not full_name or not full_name_arabic or not date_of_birth or not gender or not phone:
                flash('الحقول المطلوبة غير مكتملة', 'danger')
                return redirect(url_for('patient_register'))
                
           
            if national_id:
                existing_patient = Patient.query.filter_by(national_id=national_id).first()
                if existing_patient:
                    flash('يوجد مريض مسجل بنفس الرقم الوطني', 'danger')
                    return redirect(url_for('patient_register'))
            
           
            new_patient = Patient(
                full_name=full_name,
                full_name_arabic=full_name_arabic,
                national_id=national_id,
                date_of_birth=date_of_birth,
                gender=gender,
                blood_type=blood_type,
                phone=phone,
                address=address,
                emergency_contact=emergency_contact,
                emergency_phone=emergency_phone,
                hospital_id=current_user.hospital_id
            )
            
            db.session.add(new_patient)
            db.session.commit()
            
         
            if 'disease_name' in request.form and request.form.getlist('disease_name')[0]:
                disease_names = request.form.getlist('disease_name')
                disease_names_arabic = request.form.getlist('disease_name_arabic')
                diagnosis_dates = request.form.getlist('diagnosis_date')
                disease_notes = request.form.getlist('disease_notes')
                
                for i in range(len(disease_names)):
                    if disease_names[i].strip():
                        try:
                            diag_date = diagnosis_dates[i] if diagnosis_dates[i] else None
                            if diag_date:
                                diag_date = datetime.strptime(diag_date, '%Y-%m-%d').date()
                                
                            disease = ChronicDisease(
                                patient_id=new_patient.id,
                                disease_name=disease_names[i],
                                disease_name_arabic=disease_names_arabic[i] if i < len(disease_names_arabic) else "",
                                diagnosis_date=diag_date,
                                notes=disease_notes[i] if i < len(disease_notes) else ""
                            )
                            db.session.add(disease)
                        except Exception as e:
                            logging.error(f"Error adding disease: {e}")
            
            db.session.commit()
            flash('تم تسجيل المريض بنجاح', 'success')
            return redirect(url_for('patient_view', patient_id=new_patient.id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error registering patient: {e}")
            flash('حدث خطأ أثناء تسجيل المريض', 'danger')
            return redirect(url_for('patient_register'))
            
    return render_template('patient_register.html')

@app.route('/patients/view/<int:patient_id>')
@login_required
def patient_view(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    
    chronic_diseases = ChronicDisease.query.filter_by(patient_id=patient_id).all()
    medical_tests = MedicalTest.query.filter_by(patient_id=patient_id).order_by(MedicalTest.test_date.desc()).all()
    surgeries = Surgery.query.filter_by(patient_id=patient_id).order_by(Surgery.surgery_date.desc()).all()
    
    return render_template('patient_view.html', 
                          patient=patient, 
                          chronic_diseases=chronic_diseases,
                          medical_tests=medical_tests,
                          surgeries=surgeries)

@app.route('/patients/search', methods=['GET', 'POST'])
@login_required
def patient_search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        if not search_term:
            flash('الرجاء إدخال معيار البحث', 'warning')
            return render_template('patient_search.html')
            
       
        patients = Patient.query.filter(
            or_(
                Patient.full_name.like(f'%{search_term}%'),
                Patient.full_name_arabic.like(f'%{search_term}%'),
                Patient.national_id.like(f'%{search_term}%'),
                Patient.phone.like(f'%{search_term}%')
            )
        ).all()
        
        return render_template('patient_search.html', patients=patients, search_term=search_term)
        
    return render_template('patient_search.html')

@app.route('/patients/list')
@login_required
def patient_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    patients = Patient.query.filter_by(hospital_id=current_user.hospital_id).order_by(Patient.full_name).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('patient_list.html', patients=patients)


@app.route('/patients/<int:patient_id>/add_test', methods=['POST'])
@login_required
def add_medical_test(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        test_name = request.form.get('test_name')
        test_name_arabic = request.form.get('test_name_arabic')
        test_date = datetime.strptime(request.form.get('test_date'), '%Y-%m-%d').date()
        test_result = request.form.get('test_result')
        normal_range = request.form.get('normal_range')
        doctor_name = request.form.get('doctor_name')
        notes = request.form.get('notes')
        
     
        if not test_name or not test_date or not test_result:
            flash('الحقول المطلوبة غير مكتملة', 'danger')
            return redirect(url_for('patient_view', patient_id=patient_id))
        
     
        test = MedicalTest(
            patient_id=patient_id,
            test_name=test_name,
            test_name_arabic=test_name_arabic,
            test_date=test_date,
            test_result=test_result,
            normal_range=normal_range,
            hospital_id=current_user.hospital_id,
            doctor_name=doctor_name,
            notes=notes
        )
        
        db.session.add(test)
        db.session.commit()
        flash('تم إضافة التحليل الطبي بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding medical test: {e}")
        flash('حدث خطأ أثناء إضافة التحليل الطبي', 'danger')
    
    return redirect(url_for('patient_view', patient_id=patient_id))

@app.route('/patients/<int:patient_id>/add_surgery', methods=['POST'])
@login_required
def add_surgery(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        surgery_name = request.form.get('surgery_name')
        surgery_name_arabic = request.form.get('surgery_name_arabic')
        surgery_date = datetime.strptime(request.form.get('surgery_date'), '%Y-%m-%d').date()
        surgeon_name = request.form.get('surgeon_name')
        description = request.form.get('description')
        notes = request.form.get('notes')
        
       
        if not surgery_name or not surgery_date:
            flash('الحقول المطلوبة غير مكتملة', 'danger')
            return redirect(url_for('patient_view', patient_id=patient_id))
        
       
        surgery = Surgery(
            patient_id=patient_id,
            surgery_name=surgery_name,
            surgery_name_arabic=surgery_name_arabic,
            surgery_date=surgery_date,
            hospital_id=current_user.hospital_id,
            surgeon_name=surgeon_name,
            description=description,
            notes=notes
        )
        
        db.session.add(surgery)
        db.session.commit()
        flash('تم إضافة العملية الجراحية بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding surgery: {e}")
        flash('حدث خطأ أثناء إضافة العملية الجراحية', 'danger')
    
    return redirect(url_for('patient_view', patient_id=patient_id))

@app.route('/patients/<int:patient_id>/add_disease', methods=['POST'])
@login_required
def add_disease(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        disease_name = request.form.get('disease_name')
        disease_name_arabic = request.form.get('disease_name_arabic')
        diagnosis_date_str = request.form.get('diagnosis_date')
        notes = request.form.get('notes')
        
   
        if not disease_name:
            flash('اسم المرض مطلوب', 'danger')
            return redirect(url_for('patient_view', patient_id=patient_id))
        
        diagnosis_date = None
        if diagnosis_date_str:
            diagnosis_date = datetime.strptime(diagnosis_date_str, '%Y-%m-%d').date()
        
       
        disease = ChronicDisease(
            patient_id=patient_id,
            disease_name=disease_name,
            disease_name_arabic=disease_name_arabic,
            diagnosis_date=diagnosis_date,
            notes=notes
        )
        
        db.session.add(disease)
        db.session.commit()
        flash('تم إضافة المرض المزمن بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding chronic disease: {e}")
        flash('حدث خطأ أثناء إضافة المرض المزمن', 'danger')
    
    return redirect(url_for('patient_view', patient_id=patient_id))


@app.route('/reports')
@login_required
def reports():
   
    total_patients = Patient.query.filter_by(hospital_id=current_user.hospital_id).count()
    total_tests = MedicalTest.query.filter_by(hospital_id=current_user.hospital_id).count()
    total_surgeries = Surgery.query.filter_by(hospital_id=current_user.hospital_id).count()
    
    
    blood_types = db.session.query(
        Patient.blood_type, db.func.count(Patient.id)
    ).filter(
        Patient.hospital_id == current_user.hospital_id,
        Patient.blood_type.isnot(None)
    ).group_by(Patient.blood_type).all()
    
   
    gender_distribution = db.session.query(
        Patient.gender, db.func.count(Patient.id)
    ).filter(
        Patient.hospital_id == current_user.hospital_id
    ).group_by(Patient.gender).all()
    
  
    common_diseases = db.session.query(
        ChronicDisease.disease_name, db.func.count(ChronicDisease.id)
    ).join(Patient).filter(
        Patient.hospital_id == current_user.hospital_id
    ).group_by(ChronicDisease.disease_name).order_by(
        db.func.count(ChronicDisease.id).desc()
    ).limit(10).all()
    
    return render_template('reports.html', 
                          total_patients=total_patients,
                          total_tests=total_tests,
                          total_surgeries=total_surgeries,
                          blood_types=blood_types,
                          gender_distribution=gender_distribution,
                          common_diseases=common_diseases)


@app.route('/api/chart_data', methods=['GET'])
@login_required
def chart_data():
    chart_type = request.args.get('type', 'blood_types')
    
    if chart_type == 'blood_types':
     
        blood_types = db.session.query(
            Patient.blood_type, db.func.count(Patient.id)
        ).filter(
            Patient.hospital_id == current_user.hospital_id,
            Patient.blood_type.isnot(None)
        ).group_by(Patient.blood_type).all()
        
        labels = [bt[0] for bt in blood_types]
        data = [bt[1] for bt in blood_types]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
        
    elif chart_type == 'gender':
       
        gender_distribution = db.session.query(
            Patient.gender, db.func.count(Patient.id)
        ).filter(
            Patient.hospital_id == current_user.hospital_id
        ).group_by(Patient.gender).all()
        
        labels = [g[0] for g in gender_distribution]
        data = [g[1] for g in gender_distribution]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
        
    elif chart_type == 'diseases':
        
        common_diseases = db.session.query(
            ChronicDisease.disease_name, db.func.count(ChronicDisease.id)
        ).join(Patient).filter(
            Patient.hospital_id == current_user.hospital_id
        ).group_by(ChronicDisease.disease_name).order_by(
            db.func.count(ChronicDisease.id).desc()
        ).limit(10).all()
        
        labels = [d[0] for d in common_diseases]
        data = [d[1] for d in common_diseases]
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    
    return jsonify({'error': 'Invalid chart type'})


@app.route('/devices')
@login_required
def device_list():
    """List all authorized devices for the hospital"""
   
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard'))
        
    devices = AuthorizedDevice.query.filter_by(hospital_id=current_user.hospital_id).all()
    return render_template('device_list.html', devices=devices)

@app.route('/devices/add', methods=['GET', 'POST'])
@login_required
def device_add():
    """Add a new authorized device"""
   
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        ip_address = request.form.get('ip_address')
        device_name = request.form.get('device_name')
        description = request.form.get('description')
        
      
        if not ip_address or not device_name:
            flash('الرجاء إدخال عنوان IP واسم الجهاز', 'danger')
            return redirect(url_for('device_add'))
            
      
        existing_device = AuthorizedDevice.query.filter_by(ip_address=ip_address).first()
        if existing_device:
            flash('عنوان IP هذا مسجل بالفعل', 'danger')
            return redirect(url_for('device_add'))
            
       
        new_device = AuthorizedDevice(
            ip_address=ip_address,
            device_name=device_name,
            description=description,
            hospital_id=current_user.hospital_id,
            is_active=True
        )
        
        try:
            db.session.add(new_device)
            db.session.commit()
            flash('تمت إضافة الجهاز بنجاح', 'success')
            return redirect(url_for('device_list'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding device: {e}")
            flash('حدث خطأ أثناء إضافة الجهاز', 'danger')
            
    return render_template('device_add.html')

@app.route('/devices/<int:device_id>/toggle', methods=['POST'])
@login_required
def device_toggle(device_id):
    """Toggle the active status of a device"""
  
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard'))
        
    device = AuthorizedDevice.query.get_or_404(device_id)
    
   
    if device.hospital_id != current_user.hospital_id:
        flash('غير مصرح لك بتعديل هذا الجهاز', 'danger')
        return redirect(url_for('device_list'))
        
    try:
        device.is_active = not device.is_active
        db.session.commit()
        status = 'تفعيل' if device.is_active else 'تعطيل'
        flash(f'تم {status} الجهاز بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling device: {e}")
        flash('حدث خطأ أثناء تعديل حالة الجهاز', 'danger')
        
    return redirect(url_for('device_list'))

@app.route('/devices/<int:device_id>/delete', methods=['POST'])
@login_required
def device_delete(device_id):
    """Delete an authorized device"""
  
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('dashboard'))
        
    device = AuthorizedDevice.query.get_or_404(device_id)
    
    
    if device.hospital_id != current_user.hospital_id:
        flash('غير مصرح لك بحذف هذا الجهاز', 'danger')
        return redirect(url_for('device_list'))
        
    try:
        db.session.delete(device)
        db.session.commit()
        flash('تم حذف الجهاز بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting device: {e}")
        flash('حدث خطأ أثناء حذف الجهاز', 'danger')
        
    return redirect(url_for('device_list'))


@app.route('/api/docs')
@login_required
def api_docs():
    """API Documentation page for mobile app developers"""
    return render_template('api_docs.html')


@app.route('/error/unauthorized_device')
def error_unauthorized_device():
    """Error page for unauthorized devices"""
    return render_template('error_unauthorized_device.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
