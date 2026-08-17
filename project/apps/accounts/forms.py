# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username')  # email을 로그인 ID로, username을 한국어 이름으로 사용

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PENDING  # 가입 시 기본 상태를 '승인대기'로 지정
        if commit:
            user.save()
        return user