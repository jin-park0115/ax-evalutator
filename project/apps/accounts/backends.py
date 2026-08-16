# accounts/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class RoleBasedAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if email is None:
            return None
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        # 비밀번호 확인 및 승인 상태 체크 (PENDING 상태는 로그인 불가)
        if user.check_password(password) and self.user_can_authenticate(user):
            if user.role in [User.Role.APPROVED, User.Role.ADMIN, User.Role.STUDENT]:
                return user
        return None