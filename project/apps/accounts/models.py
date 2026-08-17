# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        PENDING = 'PENDING', '승인대기'
        APPROVED = 'APPROVED', '승인완료(역할미부여)'
        ADMIN = 'ADMIN', '관리자'
        STUDENT = 'STUDENT', '학생'

    # 로그인 ID로 사용할 unique 이메일
    email = models.EmailField(unique=True)
    
    # 역할/승인 상태 통합 관리
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PENDING
    )

    # 이메일을 로그인 ID로 지정
    USERNAME_FIELD = 'email'
    
    # createsuperuser 실행 시 이메일/비밀번호 외에 추가로 필수 입력을 받을 필드
    # username(이름)만 필수로 받도록 설정 (first_name, last_name 제외)
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # 화면 출력 시 username(실제 이름)과 이메일을 함께 표시
        return f"{self.username} ({self.email}) - {self.get_role_display()}"