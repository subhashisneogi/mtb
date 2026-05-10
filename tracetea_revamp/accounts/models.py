from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your models here.

class LoginLogoutLoggedTable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    token=models.CharField(max_length=255, blank=True, null=True)
    ip_address=models.CharField(max_length=255, blank=True, null=True)
    login_time=models.DateTimeField(auto_now_add=True)
    logout_time=models.DateTimeField(auto_now=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='lg_created_by',on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 't_log_signin_signout'