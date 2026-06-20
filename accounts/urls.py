from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('profile/', views.profile_view, name='profile'),
]

urlpatterns += [
    path('sessions/', views.active_sessions, name='active_sessions'),
    path('sessions/force-logout/<str:session_key>/', views.force_logout_session, name='force_logout_session'),
    path('sessions/force-logout-all/', views.force_logout_all_sessions, name='force_logout_all'),
]

urlpatterns += [
    path('change-password-logout-all/', views.change_password_and_logout_all, name='change_password_and_logout_all'),
]

urlpatterns += [
    path('google-login/', views.google_login, name='google_login'),
]

urlpatterns += [
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/verify/', views.verify_2fa, name='verify_2fa'),
]
