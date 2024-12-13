from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = '创建测试用的教师和学生账号'

    def handle(self, *args, **kwargs):
        # 创建教师账号
        teacher = User.objects.create_user(
            username='teacher',
            password='teacher123',
            first_name='张老师',
            is_teacher=True,
            email='teacher@example.com'
        )
        self.stdout.write(self.style.SUCCESS(f'成功创建教师账号: {teacher.username}'))

        # 创建学生账号
        student = User.objects.create_user(
            username='2024001',
            password='2024001',
            first_name='李同学',
            is_teacher=False,
            student_id='2024001',
            class_name='计算机1班',
            ip_address='127.0.0.1'  # 添加IP地址
        )
        self.stdout.write(self.style.SUCCESS(f'成功创建学生账号: {student.username}')) 