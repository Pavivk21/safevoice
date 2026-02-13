import uuid
from django.db import models


# =========================
# MAIN REPORT MODEL
# =========================

class Report(models.Model):
    email = models.EmailField(null=True, blank=True)
    is_emergency = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('review', 'Under Review'),
        ('investigation', 'Investigation'),
        ('action', 'Action Taken'),
        ('closed', 'Closed'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case_id = models.CharField(max_length=20, unique=True)

    category = models.CharField(max_length=100)

    description = models.TextField()

    incident_date = models.DateField(null=True, blank=True)

    location = models.CharField(max_length=200)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    evidence = models.FileField(
        upload_to='evidence/',
        null=True,
        blank=True
    )

    # AI / NLP Fields
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='low'
    )

    confidence_score = models.IntegerField(default=0)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    burn_flag = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.case_id


# =========================
# STATUS TIMELINE
# =========================

class StatusLog(models.Model):

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )

    status = models.CharField(max_length=50)

    note = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report.case_id} - {self.status}"


# =========================
# ANONYMOUS CHAT
# =========================

class Message(models.Model):

    SENDER_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.CharField(
        max_length=10,
        choices=SENDER_CHOICES
    )

    text = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.report.case_id}"


# =========================
# LEGAL GUIDANCE
# =========================

class LegalGuide(models.Model):

    category = models.CharField(max_length=100)

    law_name = models.CharField(max_length=200)

    section = models.CharField(max_length=100)

    description = models.TextField()

    helpline = models.CharField(max_length=50)

    def __str__(self):
        return self.category

class Notification(models.Model):

    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    def __str__(self):
        return self.message
    
