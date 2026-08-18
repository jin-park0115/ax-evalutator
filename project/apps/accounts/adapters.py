from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def save_user(self, request, sociallogin, form=None):
        # 유저 생성 및 기본 저장 (이 안에서 SocialAccount 연결까지 완료됨)
        user = super().save_user(request, sociallogin, form=form)

        # 소셜 신규 가입자의 역할은 무조건 PENDING으로 설정
        user.role = User.Role.PENDING
        user.save(update_fields=["role"])

        # [추가] 회원가입(계정 생성)은 위에서 이미 끝났으니, 여기서는
        # 자동 로그인 세션만 막는다. 다음에 같은 구글 계정으로 다시
        # 시도하면 이미 연결된 계정으로 인식되어 pre_social_login의
        # 승인 상태 검사로 자연스럽게 넘어간다.
        messages.error(
            request,
            "회원가입이 완료되었습니다. 관리자 승인 후 로그인할 수 있습니다.",
        )
        raise ImmediateHttpResponse(redirect("login"))

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