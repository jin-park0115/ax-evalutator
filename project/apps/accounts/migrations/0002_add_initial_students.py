from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_initial_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    # 비밀번호 '000000' 암호화 해시 처리
    hashed_password = make_password("000000")

    # 1. 관리자 계정 생성 및 암호화 비밀번호 설정
    admin_email = "admin@example.com"
    admin_user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "username": "관리자",
            "role": "ADMIN",
            "password": hashed_password,
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if not created:
        admin_user.password = hashed_password
        admin_user.role = "ADMIN"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

    # 2. 수강생 10명 계정 생성 및 암호화 비밀번호 설정
    students_data = [
        {"name": "김철수", "email": "chulsoo@example.com"},
        {"name": "이영희", "email": "younghee@example.com"},
        {"name": "박민수", "email": "minsoo@example.com"},
        {"name": "정수진", "email": "sujin@example.com"},
        {"name": "최도현", "email": "dohyun@example.com"},
        {"name": "강지원", "email": "jiwon@example.com"},
        {"name": "조현우", "email": "hyunwoo@example.com"},
        {"name": "윤서연", "email": "seoyeon@example.com"},
        {"name": "임재민", "email": "jaemin@example.com"},
        {"name": "한지민", "email": "jimin@example.com"},
    ]

    for d in students_data:
        u, created = User.objects.get_or_create(
            email=d["email"],
            defaults={
                "username": d["name"],
                "role": "STUDENT",
                "password": hashed_password,
            }
        )
        if not created:
            u.password = hashed_password
            u.role = "STUDENT"
            u.save()

def remove_initial_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(email__endswith='@example.com').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_users, reverse_code=remove_initial_users),
    ]