from datetime import datetime
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import (
    SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS,
    SECRET_KEY,
    CORS_ORIGINS,
    SEED_DEMO_DATA,
    UPLOAD_DIR,
)
from models import db, Admin, MCQAnswer, OpenAnswer, User, UserProfile
from utils import load_admins, load_users, hash_password, read_json_file


def seed_initial_super_admin():
    """Create the configured first supervisor once, without overwriting existing credentials."""
    admins_data = load_admins() or {}
    super_admin_data = admins_data.get('super_admin') or {}
    email = (super_admin_data.get('email') or '').strip().lower()
    password = super_admin_data.get('password')
    if not email or not password or Admin.query.filter_by(email=email).first():
        return
    db.session.add(Admin(
        full_name=super_admin_data.get('full_name') or 'المدير العام',
        phone=super_admin_data.get('phone') or '',
        email=email,
        city=super_admin_data.get('city') or '',
        password_hash=hash_password(password),
        is_super_admin=True,
        is_active=True,
    ))
    db.session.commit()


def seed_demo_candidates():
    """Seed complete, approved trial candidates once when local demo mode is enabled."""
    if not SEED_DEMO_DATA:
        return 0
    inserted = 0
    for entry in read_json_file('demo_candidates.json') or []:
        code = entry.get('code')
        if not code or User.query.filter_by(code=code).first():
            continue
        user = User(
            code=code,
            full_name=entry['full_name'],
            phone=entry.get('phone'),
            email=entry.get('email'),
            birthday=datetime.strptime(entry['birthday'], '%Y-%m-%d').date(),
            gender=entry['gender'],
            country=entry['country'],
            status='approved',
        )
        db.session.add(user)
        db.session.flush()
        answers = entry.get('mcq_answers') or {}
        db.session.add(UserProfile(user_id=user.id, details=entry.get('profile_details') or {}))
        db.session.add(MCQAnswer(
            user_id=user.id,
            q1=answers.get('q1'), q2=answers.get('q2'), q3=answers.get('q3'), q4=answers.get('q4'),
            answers=answers,
        ))
        open_answers = entry.get('open_answers') or {}
        db.session.add(OpenAnswer(
            user_id=user.id,
            q1=open_answers.get('q1'), q2=open_answers.get('q2'),
            q3=open_answers.get('q3'), q4=open_answers.get('q4'),
        ))
        inserted += 1
    if inserted:
        db.session.commit()
    return inserted


def create_app():
    """إنشاء وتهيئة تطبيق Flask، وتسجيل جميع مسارات API"""
    from routes import register_routes

    flask_app = Flask(__name__)

    flask_app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    flask_app.config['SECRET_KEY'] = SECRET_KEY

    cors_kwargs = {"origins": CORS_ORIGINS}

    if CORS_ORIGINS != '*':
        cors_kwargs["supports_credentials"] = True

    cors_kwargs["allow_headers"] = [
        "Content-Type",
        "X-Admin-Id",
        "X-User-Code"
    ]

    CORS(flask_app, resources={r"/api/*": cors_kwargs})

    db.init_app(flask_app)
    register_routes(flask_app)

    @flask_app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(UPLOAD_DIR, filename)

    with flask_app.app_context():
        db.create_all()
        seed_initial_super_admin()
        seed_demo_candidates()

    return flask_app


def seed_database():
    """نقل البيانات من ملفات JSON إلى قاعدة بيانات PostgreSQL"""
    with app.app_context():
        # 1. إدراج الإداريين (Admins)
        admins_data = load_admins()
        if admins_data:
            super_admin_data = admins_data.get('super_admin')
            if super_admin_data and not Admin.query.filter_by(email=super_admin_data['email']).first():
                super_admin = Admin(
                    full_name=super_admin_data['full_name'],
                    phone=super_admin_data['phone'],
                    email=super_admin_data['email'],
                    city=super_admin_data['city'],
                    password_hash=hash_password(super_admin_data['password']),
                    is_super_admin=True,
                    is_active=True
                )
                db.session.add(super_admin)

            for admin_info in admins_data.get('admins', []):
                if not Admin.query.filter_by(email=admin_info['email']).first():
                    new_admin = Admin(
                        full_name=admin_info['full_name'],
                        phone=admin_info['phone'],
                        email=admin_info['email'],
                        city=admin_info['city'],
                        password_hash=hash_password(admin_info['password']),
                        is_super_admin=False,
                        is_active=True
                    )
                    db.session.add(new_admin)

            db.session.commit()
            print("تم نقل الإداريين إلى PostgreSQL بنجاح.")

        # 2. إدراج المستخدمين (Users)
        users_data = load_users()
        if users_data:
            inserted = 0
            for entry in users_data:
                code = (entry.get('code') or '').strip()
                if not code or User.query.filter_by(code=code).first():
                    continue

                new_user = User(
                    code=code,
                    full_name=entry.get('full_name', 'متقدم جديد'),
                    phone=entry.get('phone'),
                    email=entry.get('email'),
                    gender=entry.get('gender'),
                    country=entry.get('country'),
                    status=entry.get('status', 'pending')
                )
                db.session.add(new_user)
                inserted += 1

            db.session.commit()
            if inserted > 0:
                print(f"تم نقل {inserted} مستخدمين إلى PostgreSQL بنجاح.")


def test_db_connection():
    """اختبار الاتصال بقاعدة البيانات بدلاً من JSON"""
    with app.app_context():
        admin_count = Admin.query.count()
        user_count = User.query.count()
        print("حالة قاعدة البيانات:")
        print(f" - عدد الإداريين: {admin_count}")
        print(f" - عدد المستخدمين: {user_count}")


app = create_app()

if __name__ == '__main__':
    # شغّل هذا السطر مرة واحدة فقط لنقل البيانات من JSON إلى PostgreSQL، ثم أعد تعليقه
    # seed_database()

    test_db_connection()
    print("\nالخادم جاهز للعمل.")
    app.run(debug=True)
