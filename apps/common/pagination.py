from rest_framework.pagination import CursorPagination


class StandardCursorPagination(CursorPagination):
    """
    Cursor pagination is used (rather than offset/limit) because message and
    notification lists are append-heavy and constantly growing — offset
    pagination would skip/duplicate rows as new rows are inserted.
    """
    page_size = 50
    max_page_size = 200
    ordering = '-created_at'
    cursor_query_param = 'cursor'
