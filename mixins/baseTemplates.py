from django.db.models import Q

class BaseListMixin:
    """
    Generic ListView helper:
      • list_display, field_labels, search_fields, filter_fields
      • optional date-range filter: ?start_date=YYYY-MM-DD & ?end_date=YYYY-MM-DD
    """

    # table / search config
    list_display   = ()
    field_labels   = {}
    ordering       = ()
    search_fields  = ()
    filter_fields  = ()

    # 🔹 date-range config (override per-view if field names differ)
    date_start_param = "start_date"
    date_end_param   = "end_date"
    date_start_field = "start"       # model field ≥
    date_end_field   = "end"         # model field ≤

    # ------------------------------------------------------------------ queryset
    def get_queryset(self):
        qs = super().get_queryset()

        # keyword search
        q = self.request.GET.get("q")
        if q and self.search_fields:
            queries = Q()
            for f in self.search_fields:
                queries |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(queries)

        # exact-match filters
        for f in self.filter_fields:
            val = self.request.GET.get(f)
            if val:
                qs = qs.filter(**{f: val})

        # date-range filter
        start_val = self.request.GET.get(self.date_start_param)
        end_val   = self.request.GET.get(self.date_end_param)
        if start_val:
            qs = qs.filter(**{f"{self.date_start_field}__gte": start_val})
        if end_val:
            qs = qs.filter(**{f"{self.date_end_field}__lte": end_val})

        # ordering
        if self.ordering:
            qs = qs.order_by(*self.ordering)
        return qs

    # ------------------------------------------------------------------ context
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "list_display": self.list_display,
                "field_labels": self.get_field_labels(),
                "create_url_name": getattr(self, "create_url_name", None),
                "update_url_name": getattr(self, "update_url_name", None),
                "delete_url_name": getattr(self, "delete_url_name", None),
                "detail_url_name": getattr(self, "detail_url_name", None),
                # pass current date filters back to template
                "start_date": self.request.GET.get(self.date_start_param, ""),
                "end_date": self.request.GET.get(self.date_end_param, ""),
            }
        )
        return ctx

    # ------------------------------------------------------------------ helpers
    def get_field_labels(self):
        if self.field_labels:
            return self.field_labels
        return {
            f: self.model._meta.get_field(f).verbose_name.title()
            for f in self.list_display
        }