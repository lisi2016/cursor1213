from django.db import models
from django.utils import timezone

class StudentLoginStatus(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True)
    last_logout = models.DateTimeField(null=True)

    class Meta:
        db_table = 'student_login_status'

    def login(self):
        self.is_online = True
        self.last_login = timezone.now()
        self.save()

    def logout(self):
        self.is_online = False
        self.last_logout = timezone.now()
        self.save() 