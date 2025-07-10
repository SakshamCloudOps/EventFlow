from django.contrib import admin
from .models import Event, UserProfile

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'organizer')
    list_filter = ('date', 'organizer')
    search_fields = ('title', 'location', 'address', 'organizer__username')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'user__email', 'phone')
