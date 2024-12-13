from django.shortcuts import render
from .models import StudentLoginStatus, Student

def teacher_dashboard(request):
    # 获取所有在线的学生状态
    online_students = StudentLoginStatus.objects.filter(
        is_online=True
    ).select_related('student')
    
    # 将在线学生的信息转换为显示格式
    student_machines = []
    for status in online_students:
        student_machines.append({
            'ip': status.student.ip_address,  # 假设Student模型中有ip_address字段
            'name': status.student.name,
            'login_time': status.last_login
        })
    
    context = {
        'student_machines': student_machines,
        # 其他现有的context数据...
    }
    return render(request, 'teacher/dashboard.html', context) 