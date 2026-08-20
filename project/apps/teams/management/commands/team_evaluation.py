import csv
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.evaluations.models import EvaluationRound, TeamEvaluation
from apps.teams.models import Team
from apps.scoring.services import get_team_eval_violations

User = get_user_model()


class Command(BaseCommand):
    help = "CSV 파일 기반 팀 평가 DB 일괄 입력 스크립트 (BR 규칙 검증)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="team_evaluations.csv",
            help="입력할 CSV 파일 경로",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="해당 라운드의 기존 팀 평가 데이터를 모두 삭제합니다.",
        )

    def handle(self, *args, **options):
        try:
            round_obj = EvaluationRound.objects.get(id=1)
        except EvaluationRound.DoesNotExist:
            self.stdout.write(self.style.ERROR("Round ID=1 이 존재하지 않습니다."))
            return

        if options["clear"]:
            deleted_count, _ = TeamEvaluation.objects.filter(round=round_obj).delete()
            self.stdout.write(
                self.style.SUCCESS(f"[초기화 완료] Round 1의 팀 평가 데이터 {deleted_count}건이 삭제되었습니다.")
            )
            return

        csv_file_path = options["file"]
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f"CSV 파일을 찾을 수 없습니다: {csv_file_path}"))
            return

        success_count = 0
        duplicate_skip_count = 0
        rule_violation_skip_count = 0

        with open(csv_file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)  # CSV 헤더(1행) Skip

            for idx, row in enumerate(reader, 2):
                if not row or not any(row) or len(row) < 8:
                    rule_violation_skip_count += 1
                    continue

                evaluator_name = row[0].strip()
                target_team_name = row[2].strip()
                raw_scores = row[3:8]

                try:
                    scores = [int(s.strip()) for s in raw_scores]
                    if any(s < 1 or s > 5 for s in scores):
                        rule_violation_skip_count += 1
                        continue
                except ValueError:
                    rule_violation_skip_count += 1
                    continue

                try:
                    evaluator = User.objects.get(username=evaluator_name)
                except User.DoesNotExist:
                    rule_violation_skip_count += 1
                    continue

                evaluator_membership = (
                    evaluator.team_memberships.filter(team__round_id=round_obj.id)
                    .select_related("team")
                    .first()
                )

                if not evaluator_membership:
                    rule_violation_skip_count += 1
                    continue

                evaluator_team = evaluator_membership.team

                clean_target_name = target_team_name.replace("팀", "")
                target_team = Team.objects.filter(
                    round=round_obj,
                    name__icontains=clean_target_name
                ).first()

                if not target_team:
                    rule_violation_skip_count += 1
                    continue

                # [BR-01] 학생은 자기 팀을 팀 평가할 수 없습니다.
                if evaluator_team.id == target_team.id:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{idx}행 Skip / BR-01 위반] 자기 팀 평가 불가 ({evaluator_name} -> {target_team.name})"
                        )
                    )
                    rule_violation_skip_count += 1
                    continue

                # [BR-05] 동일한 평가자가 동일한 평가 대상을 중복 평가할 수 없습니다.
                existing_eval = TeamEvaluation.objects.filter(
                    round=round_obj,
                    submitted_by=evaluator,
                    target_team=target_team
                ).first()

                if existing_eval:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{idx}행 Skip / BR-05 위반] 중복 평가 불가 ({evaluator_name} -> {target_team.name})"
                        )
                    )
                    duplicate_skip_count += 1
                    continue

                # [BR-06] 팀 점수는 다른 팀으로부터 받은 평가를 기반으로 계산하기 위해 수집
                responses = {f"q{i+1}": {"score": scores[i]} for i in range(5)}
                avg_score = sum(scores) / float(len(scores))

                try:
                    TeamEvaluation.objects.create(
                        round=round_obj,
                        submitted_by=evaluator,
                        evaluator_team=evaluator_team,
                        target_team=target_team,
                        score=avg_score,
                        responses=responses,
                        is_final=True,
                    )
                    success_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[{idx}행 Error] 저장 예외 ({evaluator_name} -> {target_team.name}): {e}"
                        )
                    )
                    rule_violation_skip_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[팀 평가 일괄 등록 완료] 성공: {success_count}건 / BR-05(중복제출) Skip: {duplicate_skip_count}건 / BR-01(자기팀평가) 및 기타 Skip: {rule_violation_skip_count}건"
            )
        )

        # 다른 팀 전체를 평가하지 않았거나 자기 팀을 평가하려 한 학생은
        # 위반자로 보고, 이 학생들이 제출한 평가는 점수 집계 시 전부 결측값
        # 처리된다(apps/scoring/services.py 참고). 여기서는 등록 직후
        # 누가 위반자인지 바로 확인할 수 있도록 명단을 같이 출력한다.
        violations = get_team_eval_violations(round_obj.id)
        if violations:
            violator_users = {u.id: u for u in User.objects.filter(id__in=violations.keys())}
            self.stdout.write(
                self.style.WARNING(f"\n[팀 평가 위반자 {len(violations)}명 - 제출한 평가 전부 집계에서 제외됨]")
            )
            for user_id, reason in violations.items():
                name = violator_users[user_id].username if user_id in violator_users else user_id
                self.stdout.write(f"  - {name}: {reason}")
        else:
            self.stdout.write(self.style.SUCCESS("\n[팀 평가 위반자 없음]"))