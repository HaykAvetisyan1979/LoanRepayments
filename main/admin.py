"""
admin.py — Rich admin interface for all configuration models.
Admins can manage menu items, calculation parameters, data source queries,
and report definitions without touching any Python code.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Home, CalculationParameter, DataSourceConfig, Report, ParameterStore

admin.site.register(Home)

@admin.register(CalculationParameter)
class CalculationParameterAdmin(admin.ModelAdmin):
    list_display = ('key', 'typed_value_display', 'param_type', 'category', 'last_modified')
    list_filter = ('param_type', 'category')
    search_fields = ('key', 'description', 'category')
    list_editable = ()
    readonly_fields = ('last_modified',)
    fieldsets = (
        ('Parameter Definition', {
            'fields': ('key', 'value', 'param_type', 'category')
        }),
        ('Documentation', {
            'fields': ('description',)
        }),
        ('Meta', {
            'fields': ('last_modified',),
            'classes': ('collapse',)
        }),
    )

    def typed_value_display(self, obj):
        """Show the typed value with colour-coding by type."""
        val = obj.typed_value()
        colours = {
            'float': '#2563eb', 'integer': '#7c3aed',
            'string': '#059669', 'boolean': '#d97706', 'json': '#dc2626'
        }
        colour = colours.get(obj.param_type, '#6b7280')
        return format_html(
            '<span style="color:{}; font-weight:600">{}</span>', colour, val
        )
    typed_value_display.short_description = 'Typed Value'

    def save_model(self, request, obj, form, change):
        """Invalidate the parameter cache when an admin saves a change."""
        super().save_model(request, obj, form, change)
        ParameterStore.invalidate()

    # Provide helpful example data
    class Media:
        css = {'all': ['admin/extra.css']}


@admin.register(DataSourceConfig)
class DataSourceConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'cache_timeout_seconds', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Query', {
            'fields': ('sql_query', 'cache_timeout_seconds'),
            'description': (
                'Write a parameterised SQL query executed against the external SQL Server. '
                'Use %(key)s placeholders for safe parameter injection.'
            )
        }),
        ('Meta', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'calculation_type', 'data_source', 'is_active', 'show_in_menu')
    list_editable = ('is_active', 'show_in_menu')
    list_filter = ('calculation_type', 'is_active', 'show_in_menu')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        ('Identity', {
            'fields': ('name', 'slug')
        }),
        ('Data & Calculation', {
            'fields': ('data_source', 'calculation_type')
        }),
        ('Visibility', {
            'fields': ('is_active', 'show_in_menu')
        }),
    )
