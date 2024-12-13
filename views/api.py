from django.http import JsonResponse
from .models import StudentLoginStatus

def get_student_machines(request):
    if not request.user.is_teacher:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    online_students = StudentLoginStatus.objects.filter(
        is_online=True
    ).select_related('student')
    
    data = [{
        'ip': status.student.ip_address,
        'name': status.student.name,
        'login_time': status.last_login.strftime('%Y-%m-d %H:%M:%S')
    } for status in online_students]
    
    return JsonResponse(data, safe=False) 