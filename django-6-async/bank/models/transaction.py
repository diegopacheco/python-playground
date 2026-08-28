from django.db import models


class Kind(models.TextChoices):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


class Transaction(models.Model):
    account = models.ForeignKey(
        "bank.Account", on_delete=models.CASCADE, related_name="transactions"
    )
    counterparty = models.ForeignKey(
        "bank.Account", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance_after = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["account", "-created_at"])]

    def __str__(self):
        return f"{self.kind} {self.amount} -> {self.balance_after}"
