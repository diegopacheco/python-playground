from django.db import models


class Profile(models.Model):
    full_name = models.CharField(max_length=80)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"
