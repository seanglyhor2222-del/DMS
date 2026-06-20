from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from documents import views
from accounts.views import dashboard, login_view, logout_view, register_view
from documents.api_views import dashboard_api

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

    path('api/dashboard/', dashboard_api),

    path('documents/', include('documents.urls')),
    path('activities/', include('activities.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),

    path('reports/', views.reports, name='reports'),
    path(
        'reports/user/<int:user_id>/',
        views.user_report_detail,
        name='user_report_detail'
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
    