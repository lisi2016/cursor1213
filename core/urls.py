from django.urls import path
from core import views

urlpatterns = [
    path('student/assignments/', views.get_student_assignments, name='student_assignments'),
] 