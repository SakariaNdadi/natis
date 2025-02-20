from django.contrib import admin

from .models import Category, Fine

class FineInline(admin.StackedInline):
    model = Fine

class CategoryAdmin(admin.ModelAdmin):
    model = Category
    inlines = (FineInline,)

admin.site.register(Category, CategoryAdmin)