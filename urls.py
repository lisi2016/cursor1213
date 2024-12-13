from django.urls import path
from . import views

urlpatterns = [
    path('api/student-machines/', views.api.get_student_machines, name='student_machines'),
] 