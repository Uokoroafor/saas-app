from django.db import models

# Create your models here.
class Subscription(models.Model):
    name = models.CharField(max_length=120)

    class Meta:
        permissions=[
            ("advanced", "Advanced Permissions"), # subscriptions.advanced
            ("pro", "Pro Permissions"),  # subscriptions.pro
            ("basic", "Basic Permissions"),  # subscriptions.basic
            ("basic_ai", "Basic AI Permissions"),  # subscriptions.basic
        ]