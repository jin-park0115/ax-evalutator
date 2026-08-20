import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "CSV(이름,이메일,비밀번호,role)로부터 학생 계정을 생성합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path", # CSV 경로 추가
            nargs="?",
            default=str(Path(settings.BASE_DIR) / "data" / "seed" / "students_accounts.csv"),
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]) # CSV 경로 추가
        if not csv_path.exists():
            raise CommandError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

        User = get_user_model()
        created, skipped = 0, 0

        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["이름"].strip()
                email = row["이메일"].strip()
                password = row["비밀번호"].strip()
                role = (row.get("role") or "STUDENT").strip()

                if User.objects.filter(email=email).exists() or User.objects.filter(username=name).exists():
                    skipped += 1
                    self.stdout.write(f"skip (already exists): {name} <{email}>")
                    continue

                User.objects.create_user(
                    username=name,
                    email=email,
                    password=password,
                    role=role,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"완료: {created}명 생성, {skipped}명 스킵"))
