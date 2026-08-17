# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수 입력 항목입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        # self.model을 통한 안전한 Role 참조로 수정
        extra_fields.setdefault("role", self.model.Role.ADMIN)

        if extra_fields.get("role") != self.model.Role.ADMIN:
            raise ValueError("Superuser의 role은 반드시 ADMIN이어야 합니다.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        PENDING = "PENDING", "승인대기"
        APPROVED = "APPROVED", "승인완료(역할미부여)"
        ADMIN = "ADMIN", "관리자"
        STUDENT = "STUDENT", "학생"

    # 한글을 허용하는 커스텀 username 검증기 정의
    username_validator = RegexValidator(
        regex=r"^[\w가-힣.@+-]+$",
        message="한글, 영문, 숫자 및 특수문자(.@+-)만 사용할 수 있습니다.",
    )

    # username 필드 재정의 (커스텀 validator 적용)
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_/Korean only.",
        validators=[username_validator],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )

    # 로그인 ID로 사용할 unique 이메일
    email = models.EmailField(unique=True)

    # 역할/승인 상태 통합 관리
    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.PENDING
    )

    # 커스텀 유저 매니저 설정
    objects = CustomUserManager()

    # 이메일을 로그인 ID로 지정
    USERNAME_FIELD = "email"

    # createsuperuser 실행 시 이메일/비밀번호 외에 추가로 필수 입력을 받을 필드
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        # 화면 출력 시 username(실제 이름)과 이메일을 함께 표시
        return f"{self.username} ({self.email}) - {self.get_role_display()}"