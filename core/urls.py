from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('import-students/', views.import_students, name='import_students'),
    path('distribute-assignments/', views.distribute_assignments, name='distribute_assignments'),
    path('download-assignment/<int:assignment_id>/', views.download_assignment, name='download_assignment'),
    path('grade-assignment/<int:assignment_id>/', views.grade_assignment, name='grade_assignment'),
    path('export-grades/', views.export_grades, name='export_grades'),
    path('machine-status/', views.update_machine_status, name='machine_status'),
    path('download-template/', views.download_import_template, name='download_template'),
    path('delete-assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    path('delete-assignments/', views.delete_assignments, name='delete_assignments'),
    path('student/assignments/', views.get_student_assignments, name='student_assignments'),
    path('test/', views.test_websocket, name='test_websocket'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 