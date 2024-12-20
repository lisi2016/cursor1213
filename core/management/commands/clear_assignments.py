from django.core.management.base import BaseCommand
from core.models import Assignment
import os
from django.conf import settings

class Command(BaseCommand):
    help = '清除所有批改任务及相关文件'

    def handle(self, *args, **options):
        try:
            # 获取所有作业记录
            assignments = Assignment.objects.all()
            count = assignments.count()
            
            # 删除每个作业的文件
            for assignment in assignments:
                if assignment.file_path:
                    try:
                        # 删除文件
                        if os.path.exists(assignment.file_path.path):
                            os.remove(assignment.file_path.path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'删除文件失败: {str(e)}'))

            # 删除所有作业记录
            assignments.delete()
            
            # 清空 media/assignments 目录
            assignments_dir = os.path.join(settings.MEDIA_ROOT, 'assignments')
            if os.path.exists(assignments_dir):
                for file in os.listdir(assignments_dir):
                    file_path = os.path.join(assignments_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'删除文件失败: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'成功删除 {count} 个批改任务及相关文件'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'清除失败: {str(e)}')) 