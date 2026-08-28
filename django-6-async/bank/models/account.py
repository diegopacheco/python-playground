from django.db import models


class Account(models.Model):
    profile = models.OneToOneField(
        "bank.Profile", on_delete=models.CASCADE, related_name="account"
    )
    number = models.CharField(max_length=12, unique=True)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.number} ({self.balance})"
