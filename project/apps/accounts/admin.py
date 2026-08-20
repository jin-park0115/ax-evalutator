from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # 어드민 사용자 목록 화면에 표시할 필드
    list_display = ("id", "username", "email", "role", "is_staff", "is_active")
    
    # 우측 필터링 옵션
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    
    # 검색창 대상 필드
    search_fields = ("username", "email")
    
    # 정렬 순서
    ordering = ("id",)

    # 기존 Django UserAdmin 폼에 커스텀 필드(role) 추가
    fieldsets = BaseUserAdmin.fieldsets + (
        ("추가 정보", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("추가 정보", {"fields": ("role",)}),
    )