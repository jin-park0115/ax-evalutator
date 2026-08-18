from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        # 유저 생성 및 기본 저장
        user = super().save_user(request, sociallogin, form=form)

        # 소셜 신규 가입자의 역할은 무조건 PENDING으로 설정
        user.role = User.Role.PENDING
        user.save(update_fields=["role"])
        return user

    def pre_social_login(self, request, sociallogin):
        # 이미 존재하는 유저가 소셜 로그인을 시도할 때 승인 상태 검사
        if sociallogin.is_existing:
            user = sociallogin.user
            if user.role in [User.Role.PENDING, User.Role.APPROVED]:
                messages.error(
                    request,
                    "관리자 승인 대기 중이거나 역할이 부여되지 않은 계정입니다.",
                )
                raise ImmediateHttpResponse(redirect("login"))