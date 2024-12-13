from django.shortcuts import render
from .models import StudentLoginStatus

def student_login(request):
    # 现有的登录验证代码...
    
    if login_success:
        student_status, created = StudentLoginStatus.objects.get_or_create(
            student=student
        )
        student_status.login()
    
    # 继续现有的代码...

def student_logout(request):
    # 现有的登出代码...
    
    student_status = StudentLoginStatus.objects.get(student=request.user.student)
    student_status.logout()
    
    # 继续现有的代码... 