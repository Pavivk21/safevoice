from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    
    path('', TemplateView.as_view(template_name="intro.html"), name="home"),
    path('report/', views.report_form, name='report'),
    path('track/', views.track_case, name='track'),
    path('test/', views.test_view),
    path('chat/<str:case_id>/', views.chat_view, name='chat'),
    path('timeline/<str:case_id>/', views.timeline_view, name='timeline'),
    path('heatmap/', views.heatmap_view, name='heatmap'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('update/<str:case_id>/', views.update_case, name='update_case'),
    path('legal/<str:case_id>/', views.legal_view, name='legal'),
    path('public/', views.public_dashboard, name='public_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    path('case/<str:case_id>/', views.case_detail, name='case_detail'),
    path('notifications/', views.notifications, name='notifications'),
    path('sos/<str:case_id>/', views.trigger_sos, name='trigger_sos'),
    path('pdf/<str:case_id>/', views.download_pdf, name='download_pdf'),

]

