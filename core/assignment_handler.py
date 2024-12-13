import os
from typing import List
from django.db import transaction
from .models import User, Assignment, DistributionLog

class AssignmentDistributor:
    def __init__(self, teacher: User, files: List[str], online_students: List[User]):
        self.teacher = teacher
        self.files = files
        self.online_students = online_students
        
    @transaction.atomic
    def distribute(self):
        try:
            assignments = []
            for idx, file in enumerate(self.files):
                student_idx = idx % len(self.online_students)
                student = self.online_students[student_idx]
                
                assignment = Assignment.objects.create(
                    file_name=file,
                    assigned_to=student
                )
                
                DistributionLog.objects.create(
                    teacher=self.teacher,
                    student=student,
                    assignment=assignment
                )
                
                assignments.append(assignment)
                
            return True, assignments
        except Exception as e:
            return False, str(e) 