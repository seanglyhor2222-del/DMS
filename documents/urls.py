from django.urls import path
from . import views
from .api_views import dashboard_api

urlpatterns = [
    path('', views.document_list, name='document_list'),

    path('upload/', views.document_upload, name='document_upload'),

    path('<int:document_id>/', views.document_detail, name='document_detail'),

    path('<int:document_id>/edit/', views.document_edit, name='document_edit'),

    path('<int:document_id>/delete/', views.document_delete, name='document_delete'),

    path('<int:document_id>/download/', views.document_download, name='document_download'),

    path('<int:document_id>/approve/', views.document_approve, name='document_approve'),

    path('<int:document_id>/reject/', views.document_reject, name='document_reject'),

    path('pending/', views.pending_approvals, name='pending_approvals'),

    path('categories/', views.category_manage, name='category_manage'),

    path('api/dashboard/', dashboard_api, name='dashboard_api'),

    path(
        'reports/',
        views.category_reports,
        name='reports'
    ),

    path(
        'reports/category/<int:category_id>/',
        views.category_report_detail,
        name='category_report_detail'
    ),

    path(
        'reports/user/<int:user_id>/',
        views.user_report_detail,
        name='user_report_detail'
    ),

    path(
    'reports/categories/',
    views.category_reports,
    name='category_reports'
    ),

    path(
        'reports/documents/',
        views.document_reports,
        name='document_reports'
    ),

    path(
        'reports/users/',
        views.user_activity_reports,
        name='user_activity_reports'
    ),

    path(
    'reports/user-detail/<int:user_id>/',
    views.user_activity_detail,
    name='user_activity_detail'
),
]