from django.contrib import admin
from django.contrib.auth import get_user_model
from apps.teams.models import Team, TeamMember

User = get_user_model()


class TeamMemberInline(admin.TabularInline):
    """팀 상세 페이지 내에서 팀원을 함께 등록/관리하는 인라인 설정"""
    model = TeamMember
    extra = 1

    # 드롭다운 목록에 role='STUDENT'인 유저만 노출
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(role=User.Role.STUDENT)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "round_id", "presentation_order", "eval_status")
    list_filter = ("eval_status", "round_id")
    search_fields = ("name",)
    inlines = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "team", "student")
    list_filter = ("team",)

    # 단독 TeamMember 등록 페이지에서도 STUDENT만 노출
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "student":
            kwargs["queryset"] = User.objects.filter(role=User.Role.STUDENT)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)