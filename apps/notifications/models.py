from django.db import models


class Announcement(models.Model):
    class TYPES(models.TextChoices):
        INFO = "INFO"
        DANGER = "DANGER"
        WARNING = "WARNING"

    a_type = models.CharField(max_length=20, choices=TYPES.choices, default=TYPES.INFO)
    text = models.CharField(max_length=300)
    is_visible = models.BooleanField(default=False)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.text
