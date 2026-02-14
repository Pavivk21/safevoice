import random
import string
import json

from django.shortcuts import render, get_object_or_404
from .models import Notification
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse
from .legal_data import LEGAL_RIGHTS
from django.db.models import Count
from django.db.models.functions import TruncDate
from .models import Report, Message, StatusLog, Notification
from .ai_utils import analyze_report
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
# ----------------------------
# Generate Unique Case ID
# ----------------------------
def generate_case_id():
    return 'SV-' + ''.join(
        random.choices(string.digits, k=6)
    )


# ----------------------------
# Main Report Form
# ----------------------------
def detect_law_category(text):

    text = text.lower()

    if any(w in text for w in ["rape", "raped", "molest", "sexual"]):
        return "rape"

    if any(w in text for w in ["stalk", "follow"]):
        return "stalking"

    if any(w in text for w in ["blackmail", "extort"]):
        return "blackmail"

    if any(w in text for w in ["threat", "kill", "murder"]):
        return "threat"

    if any(w in text for w in ["hack", "fake", "morph", "leak"]):
        return "cyber abuse"

    if any(w in text for w in ["husband", "dowry", "beat", "family"]):
        return "domestic violence"

    return "harassment"


def detect_severity(text):

    text = text.lower()

    high_keywords = [
        "kill", "rape", "attack", "knife", "threat",
        "suicide", "danger", "murder", "acid", "weapon"
    ]

    medium_keywords = [
        "harass", "stalk", "abuse", "follow",
        "blackmail", "bully", "threaten"
    ]

    for word in high_keywords:
        if word in text:
            return "high"

    for word in medium_keywords:
        if word in text:
            return "medium"

    return "low"



def report_form(request):

    if request.method == 'POST':

        case_id = generate_case_id()

        description = request.POST.get('description', '')
        
        print("DESC:", description) 
        incident_date = request.POST.get('incident_date') or None


        # ---------- AI Analysis (Existing) ----------
        try:
            analysis = analyze_report(description)
        except:
            analysis = ""

        confidence = 50

        for line in analysis.split("\n"):
            if "Confidence" in line:
                digits = ''.join(filter(str.isdigit, line))
                if digits:
                    confidence = int(digits)


        # ---------- NEW: AI Keyword Severity ----------
        ai_severity = detect_severity(description)


        # ---------- Save Report ----------
        report = Report.objects.create(

            case_id=case_id,

            category=request.POST.get('category'),

            description=description,

            incident_date=incident_date,

            location=request.POST.get('location'),

            latitude=request.POST.get("lat") or None,
            longitude=request.POST.get("lng") or None,

            evidence=request.FILES.get('evidence'),

            # AI Values
            severity=ai_severity,
            confidence_score=confidence
        )


        # ---------- Timeline ----------
        StatusLog.objects.create(
            report=report,
            status="submitted",
            note="Report submitted successfully"
        )


        return render(
            request,
            'reports/success.html',
            {'case_id': case_id}
        )


    return render(request, 'reports/report_form.html')

# ----------------------------
# Track Case
# ----------------------------
def track_case(request):

    report = None

    if request.method == 'POST':

        case_id = request.POST.get('case_id')

        try:
            report = Report.objects.get(case_id=case_id)
        except Report.DoesNotExist:
            report = None

    return render(
        request,
        'reports/track.html',
        {'report': report}
    )


# ----------------------------
# Timeline View
# ----------------------------
def timeline_view(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    logs = report.status_logs.all().order_by('timestamp')

    return render(
        request,
        "reports/timeline.html",
        {
            "report": report,
            "logs": logs
        }
    )


# ----------------------------
# Chat View
# ----------------------------
def chat_view(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    messages = Message.objects.filter(
        report=report
    ).order_by('timestamp')

    if request.method == "POST":

        text = request.POST.get("text")

        sender = "user"

        if request.user.is_authenticated and request.user.is_staff:
            sender = "admin"

        Message.objects.create(
            report=report,
            sender=sender,
            text=text
        )

    return render(
        request,
        "reports/chat.html",
        {
            "report": report,
            "messages": messages
        }
    )


# ----------------------------
# Heatmap View
# ----------------------------
def heatmap_view(request):

    reports = Report.objects.exclude(
        latitude__isnull=True,
        longitude__isnull=True
    )

    points = []

    for r in reports:
        points.append({
            "lat": float(r.latitude),
            "lng": float(r.longitude),
            "severity": r.severity
        })

    points_json = json.dumps(points)

    return render(
        request,
        "reports/heatmap.html",
        {"points": points_json}
    )


# ----------------------------
# Test
# ----------------------------
def test_view(request):
    return HttpResponse("SafeVoice is working!")

def admin_dashboard(request):

    reports = Report.objects.all().order_by('-created_at')

    total = reports.count()
    high = reports.filter(severity='high').count()
    medium = reports.filter(severity='medium').count()
    low = reports.filter(severity='low').count()

    return render(
        request,
        "reports/dashboard.html",
        {
            "reports": reports,
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
        }
    )

@staff_member_required
def update_case(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    if request.method == "POST":

        new_status = request.POST.get("status")
        new_severity = request.POST.get("severity")

        old_status = report.status
        old_severity = report.severity

        status_changed = False
        severity_changed = False


        # ---------- Status Change ----------
        if new_status and new_status != old_status:

            report.status = new_status
            status_changed = True

            # Notification
            Notification.objects.create(
                report=report,
                message=f"Your case {report.case_id} status is now {new_status}"
            )

            # Timeline
            StatusLog.objects.create(
                report=report,
                status=new_status,
                note=f"Status updated to {new_status}"
            )


        # ---------- Severity Change ----------
        if new_severity and new_severity != old_severity:

            report.severity = new_severity
            severity_changed = True

            # Notification
            Notification.objects.create(
                report=report,
                message=f"Your case {report.case_id} severity is now {new_severity}"
            )


        # Save
        report.save()


        # ---------- Email ----------
        if getattr(report, "email", None) and (status_changed or severity_changed):

            print("EMAIL SENDING TO:", report.email)   # Debug

            subject = "SafeVoice Case Update"

            message = f"""
Hello,

Your case {report.case_id} has been updated.

Status: {report.status.upper()}
Severity: {report.severity.upper()}
Category: {report.category}

Please check your dashboard.

SafeVoice Team
"""

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [report.email],
                fail_silently=False,
            )


    return redirect("/dashboard/")


def legal_view(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    category = detect_law_category(report.description)

    laws = LEGAL_RIGHTS.get(category, [])

    return render(request, "reports/legal.html", {
        "report": report,
        "laws": laws,
        "category": category
    })


def public_dashboard(request):

    reports = Report.objects.all()

    total = reports.count()
    high = reports.filter(severity="high").count()
    medium = reports.filter(severity="medium").count()
    low = reports.filter(severity="low").count()
    severity_data = json.dumps([high, medium, low])

    # Trend data
    trend_qs = reports.annotate(
        day=TruncDate("created_at")
    ).values("day").annotate(c=Count("id")).order_by("day")

    labels = []
    values = []

    for t in trend_qs:
        labels.append(str(t["day"]))
        values.append(t["c"])

    return render(
        request,
        "reports/public_dashboard.html",
        {
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "labels": json.dumps(labels),
            "values": json.dumps(values),
            "severity_data": severity_data,

        }
    )

@staff_member_required
def admin_dashboard(request):

    reports = Report.objects.all()

    # Filters
    status = request.GET.get("status")
    severity = request.GET.get("severity")

    if status:
        reports = reports.filter(status=status)

    if severity:
        reports = reports.filter(severity=severity)

    total = reports.count()
    high = reports.filter(severity="high").count()
    medium = reports.filter(severity="medium").count()
    low = reports.filter(severity="low").count()

    return render(request, "reports/dashboard.html", {
        "reports": reports,
        "total": total,
        "high": high,
        "medium": medium,
        "low": low,
    })

@staff_member_required
def case_detail(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    messages = Message.objects.filter(report=report).order_by("timestamp")
    logs = report.status_logs.all().order_by("timestamp")

    return render(request, "reports/case_detail.html", {
        "report": report,
        "messages": messages,
        "logs": logs,
    })

@staff_member_required
def admin_analytics(request):

    reports = Report.objects.all()

    # Summary
    total = reports.count()
    submitted = reports.filter(status="submitted").count()
    review = reports.filter(status="review").count()
    resolved = reports.filter(status="resolved").count()

    high = reports.filter(severity="high").count()
    medium = reports.filter(severity="medium").count()
    low = reports.filter(severity="low").count()

    # Trend
    trend = reports.annotate(
        day=TruncDate("created_at")
    ).values("day").annotate(c=Count("id")).order_by("day")

    labels = [str(t["day"]) for t in trend]
    values = [t["c"] for t in trend]

    return render(request, "reports/admin_analytics.html", {
        "total": total,
        "submitted": submitted,
        "review": review,
        "resolved": resolved,

        "high": high,
        "medium": medium,
        "low": low,

        "labels": json.dumps(labels),
        "values": json.dumps(values),

        "status_data": json.dumps([submitted, review, resolved]),
        "severity_data": json.dumps([high, medium, low]),
    })

def notifications(request):

    notes = Notification.objects.all().order_by("-created_at")

    return render(request, "reports/notifications.html", {
        "notes": notes
    })

def trigger_sos(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)

    # Prevent double trigger
    if report.is_emergency:
        return redirect('case_detail', case_id=case_id)

    # Mark as emergency
    report.is_emergency = True
    report.severity = "high"
    report.status = "investigation"
    report.save()

    # Save notification
    Notification.objects.create(
        report=report,
        message=f"🚨 EMERGENCY: SOS triggered for {report.case_id}"
    )

    # Timeline log
    StatusLog.objects.create(
        report=report,
        status="EMERGENCY",
        note="SOS button pressed"
    )

    return redirect('case_detail', case_id=case_id)

def download_pdf(request, case_id):

    report = get_object_or_404(Report, case_id=case_id)
    logs = report.status_logs.all()

    template = get_template("reports/case_pdf.html")

    html = template.render({
        "report": report,
        "logs": logs
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{case_id}.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response

