from django.db.models import Q

class BaseListMixin:
    """
    ใช้กับ ListView ทั่วไป:
      - กำหนด list_display, field_labels, search_fields, filter_fields
      - พร้อมส่ง context ให้ base_list.html ใช้งาน
    """
    list_display = ()
    field_labels = {}
    ordering = ()
    search_fields = ()
    filter_fields = ()

    def get_queryset(self):
        queryset = super().get_queryset()

        # Search
        q = self.request.GET.get("q")
        if q and self.search_fields:
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f"{field}__icontains": q})
            queryset = queryset.filter(query)

        # Filter
        for field in self.filter_fields:
            value = self.request.GET.get(field)
            if value:
                queryset = queryset.filter(**{field: value})

        # Ordering
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "list_display": self.list_display,
            "field_labels": self.get_field_labels(),
            "create_url_name": getattr(self, "create_url_name", None),
            "update_url_name": getattr(self, "update_url_name", None),
            "delete_url_name": getattr(self, "delete_url_name", None),
        })
        return context

    def get_field_labels(self):
        if self.field_labels:
            return self.field_labels
        return {
            field: self.model._meta.get_field(field).verbose_name.title()
            for field in self.list_display
        }
