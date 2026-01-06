"""
Configuration de l'admin Django pour l'application home.
"""
from django.contrib import admin
from .models import ExampleModel


@admin.register(ExampleModel)
class ExampleModelAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour ExampleModel.
    """
    list_display = ['name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
