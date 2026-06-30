from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('id', 'email', 'username', 'is_online', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_online', 'email_notifications')
    search_fields = ('email', 'username')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Chat Profile', {'fields': ('avatar', 'bio', 'is_online', 'last_seen', 'email_notifications')}),
    )
