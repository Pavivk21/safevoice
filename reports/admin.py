from django.contrib import admin
from .models import Report, StatusLog, Message, LegalGuide


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    list_display = (
        'case_id',
        'category',
        'severity',
        'confidence_score',
        'status',
        'created_at'
    )

    list_filter = ('severity', 'status')

    search_fields = ('case_id', 'category')


@admin.register(StatusLog)
class StatusLogAdmin(admin.ModelAdmin):

    list_display = (
        'report',
        'status',
        'timestamp'
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = (
        'report',
        'sender',
        'timestamp'
    )


@admin.register(LegalGuide)
class LegalGuideAdmin(admin.ModelAdmin):

    list_display = (
        'category',
        'law_name',
        'section',
        'helpline'
    )
