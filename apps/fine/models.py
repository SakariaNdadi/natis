from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)

    def __str__(self):
        return self.name.capitalize()

    class Meta:
        verbose_name_plural = "categories"


class Fine(models.Model):
    category = models.ForeignKey(
        Category, related_name="fines", on_delete=models.PROTECT
    )
    code = models.PositiveIntegerField()
    description = models.TextField()
    fine = models.CharField(max_length=4)
