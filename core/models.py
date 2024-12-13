from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    ip_address = models.CharField(max_length=15, blank=True, null=True)
    class_name = models.CharField(max_length=50, blank=True)
    student_id = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({'教师' if self.is_teacher else '学生'})"

class Assignment(models.Model):
    GRADE_CHOICES = [
        ('A', '优'),
        ('B', '良'),
        ('C', '合格'),
        ('D', '差'),
    ]
    
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='assignments/')
    upload_time = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    grade = models.CharField(max_length=1, choices=GRADE_CHOICES, null=True, blank=True)
    download_status = models.BooleanField(default=False)
    download_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.file_name} - {self.assigned_to.username}"

class DistributionLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='distributed_assignments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_assignments')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.timestamp}: {self.teacher} -> {self.student}" 