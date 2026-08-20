import csv
import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.evaluations.models import EvaluationRound, IndividualEvaluation
from apps.evaluations.services import save_individual_evaluation

User = get_user_model()


class Command(BaseCommand):
    help = "서비스 함수 기반 비즈니스 규칙 검증 및 최초 1회 개인 평가 제출 저장 스크립트"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="evaluations.csv",
            help="입력할 CSV 파일 경로",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="해당 라운드의 기존 개인 평가 데이터를 모두 삭제합니다.",
        )

    def handle(self, *args, **options):
        try:
            round_obj = EvaluationRound.objects.get(id=1)
        except EvaluationRound.DoesNotExist:
            self.stdout.write(self.style.ERROR("Round ID=1 이 존재하지 않습니다."))
            return

        if options["clear"]:
            deleted_count, _ = IndividualEvaluation.objects.filter(round=round_obj).delete()
            self.stdout.write(
                self.style.SUCCESS(f"[초기화 완료] Round 1의 개인 평가 데이터 {deleted_count}건이 삭제되었습니다.")
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
                target_name = row[2].strip()
                raw_scores = row[3:8]

                try:
                    scores = [int(s.strip()) for s in raw_scores]
                except ValueError:
                    self.stdout.write(
                        self.style.WARNING(f"[{idx}행 Skip] 점수 누락 또는 형식 오류: {row}")
                    )
                    rule_violation_skip_count += 1
                    continue

                try:
                    evaluator = User.objects.get(username=evaluator_name)
                    target = User.objects.get(username=target_name)
                except User.DoesNotExist as e:
                    self.stdout.write(
                        self.style.WARNING(f"[{idx}행 Skip] 유저를 찾을 수 없음: {e}")
                    )
                    rule_violation_skip_count += 1
                    continue

                evaluator_membership = (
                    evaluator.team_memberships.filter(team__round_id=round_obj.id)
                    .select_related("team")
                    .first()
                )

                if not evaluator_membership:
                    self.stdout.write(
                        self.style.WARNING(f"[{idx}행 Skip] {evaluator_name}의 팀 소속 정보를 찾을 수 없음")
                    )
                    rule_violation_skip_count += 1
                    continue

                team_id = evaluator_membership.team_id
                responses = {f"q{i+1}": {"score": scores[i]} for i in range(5)}
                avg_score = sum(scores) / float(len(scores))

                # [BR-03, BR-07] 서비스 함수 호출 (같은 팀 구성원에 관한 개인 평가 저장)
                try:
                    save_individual_evaluation(
                        round_id=round_obj.id,
                        team_id=team_id,
                        evaluator_id=evaluator.id,
                        target_id=target.id,
                        score=avg_score,
                        responses=responses,
                        is_final=True,
                    )
                    success_count += 1

                except ValueError as ve:
                    error_msg = str(ve)
                    
                    # [BR-05] 동일한 평가자가 동일한 평가 대상을 중복 평가할 수 없음
                    if "최종 제출된 평가는 수정할 수 없습니다" in error_msg:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{idx}행 Skip / BR-05 위반] 중복 평가 불가 ({evaluator_name} -> {target_name})"
                            )
                        )
                        duplicate_skip_count += 1
                    
                    # [BR-02] 학생은 다른 팀의 개인 구성원을 평가할 수 없습니다.
                    # [BR-04] 학생은 자기 자신을 개인 평가할 수 없습니다.
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{idx}행 Skip / BR 규칙 위반] ({evaluator_name} -> {target_name}): {error_msg}"
                            )
                        )
                        rule_violation_skip_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"[{idx}행 Error] 저장 처리 중 예외 발생 ({evaluator_name} -> {target_name}): {e}"
                        )
                    )
                    rule_violation_skip_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[개인 평가 일괄 등록 완료] 성공: {success_count}건 / BR-05(중복제출) Skip: {duplicate_skip_count}건 / BR-02, BR-04(규칙위반) Skip: {rule_violation_skip_count}건"
            )
        )