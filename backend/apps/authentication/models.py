from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminRequestModel(models.Model):
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_request')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} → {self.status}"
    
    class Meta:
        verbose_name        = 'Admin Request'
        verbose_name_plural = 'Admin Requests'