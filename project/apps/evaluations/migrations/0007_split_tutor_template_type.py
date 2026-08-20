from django.db import migrations, models


def tutor_to_tutor_team(apps, schema_editor):
    # 기존 TUTOR 템플릿은 튜터 팀 평가로 간주하고 옮긴다
    # (기존에는 튜터 팀/개인 평가가 같은 템플릿을 공유했음)
    EvaluationTemplate = apps.get_model("evaluations", "EvaluationTemplate")
    EvaluationTemplate.objects.filter(type="TUTOR").update(type="TUTOR_TEAM")


def tutor_team_to_tutor(apps, schema_editor):
    EvaluationTemplate = apps.get_model("evaluations", "EvaluationTemplate")
    EvaluationTemplate.objects.filter(type="TUTOR_TEAM").update(type="TUTOR")


class Migration(migrations.Migration):

    dependencies = [
        ("evaluations", "0006_individualevaluation_uq_individual_evaluation_once_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evaluationtemplate",
            name="type",
            field=models.CharField(
                choices=[
                    ("TEAM", "학생 팀 평가"),
                    ("INDIVIDUAL", "학생 개인 평가"),
                    ("TUTOR_TEAM", "튜터 팀 평가"),
                    ("TUTOR_INDIVIDUAL", "튜터 개인 평가"),
                ],
                max_length=20,
                verbose_name="템플릿 유형",
            ),
        ),
        migrations.RunPython(tutor_to_tutor_team, tutor_team_to_tutor),
    ]
