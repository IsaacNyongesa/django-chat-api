from django.urls import path
from .views import NotificationListView, MarkReadView, MarkAllReadView, UnreadCountView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/read/', MarkReadView.as_view(), name='notification_mark_read'),
    path('read-all/', MarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('unread-count/', UnreadCountView.as_view(), name='notification_unread_count'),
]
