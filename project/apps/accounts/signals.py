# apps/accounts/signals.py
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(social_account_added)
def set_pending_role_for_social_user(request, sociallogin, **kwargs):
    user = sociallogin.user
    # 구글로 처음 들어온 사용자 기본 role 설정
    if not user.role:
        user.role = User.Role.PENDING
        user.save()