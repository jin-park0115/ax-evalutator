from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        # 1. DB에 신규 유저 생성 및 기본 저장
        user = super().save_user(request, sociallogin, form=form)

        # 2. 신규 가입자 역할(Role)을 무조건 PENDING으로 설정
        user.role = User.Role.PENDING
        user.save(update_fields=["role"])

        # 3. 신규 가입 완료 직후 세션이 생성(자동 로그인)되지 않도록 예외 발생 후 차단
        messages.info(
            request,
            "회원가입 신청이 완료되었습니다. 관리자 승인 및 역할 부여 후 로그인 가능합니다.",
        )
        raise ImmediateHttpResponse(redirect("login"))

    def pre_social_login(self, request, sociallogin):
        # 이미 DB에 존재하는 유저가 다시 로그인 시도할 때 검사
        if sociallogin.is_existing:
            user = sociallogin.user
            # STUDENT 또는 ADMIN 역할이 없는 경우 로그인 차단
            if user.role not in [User.Role.ADMIN, User.Role.STUDENT]:
                messages.error(
                    request,
                    "관리자 승인 대기 중이거나 역할이 부여되지 않은 계정입니다.",
                )
                raise ImmediateHttpResponse(redirect("login"))