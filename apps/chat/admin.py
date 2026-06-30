from django.contrib import admin
from .models import Room, RoomMember, Message


class RoomMemberInline(admin.TabularInline):
    model = RoomMember
    extra = 0


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'room_type', 'created_by', 'created_at', 'updated_at')
    list_filter = ('room_type',)
    search_fields = ('name',)
    inlines = [RoomMemberInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'short_content', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)
    search_fields = ('content', 'sender__username')

    def short_content(self, obj):
        return obj.content[:50]
    short_content.short_description = 'Content'
