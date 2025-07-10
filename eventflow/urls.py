from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from events import views as event_views
from events.views import CustomLoginView
from events import views
from django.urls import path, include



urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Home
    path('', event_views.home, name='home'),

    # Event Operations
    path('create/', event_views.create_event, name='create_event'),
    path('event/<int:event_id>/', event_views.event_detail, name='event_detail'),
    path('event/<int:event_id>/download-ticket/', event_views.download_ticket, name='download_ticket'),
    path('event/<int:event_id>/update/', event_views.update_event, name='update_event'),
    path('event/<int:event_id>/delete/', event_views.delete_event, name='delete_event'),
    path('event/<int:event_id>/register/', event_views.register_for_event, name='register_for_event'),
    path('event/<int:event_id>/registrations/', event_views.view_registrations, name='view_registrations'),
    # Authentication
    path('signup/', event_views.signup_view, name='signup'),
    path('login/', CustomLoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # User Dashboard and Profile
    path('dashboard/', event_views.user_dashboard, name='user_dashboard'),
    path('profile/', event_views.edit_profile, name='edit_profile'),
    # Registrations
    path('my-registrations/', event_views.my_registrations, name='my_registrations'),
    # in urls.py
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('my-events/', views.my_events, name='my_events'),
     path('', include('events.urls')),
     
]

#  Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
