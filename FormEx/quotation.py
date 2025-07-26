from core.mixins.viewMixins import (
    BaseListView,
    BaseCreateView,
    BaseUpdateView,
    BaseDeleteView          
)
from quotation.models import Quotation, QuotationItem
from django.views.generic import DetailView
from ..forms.quotation import QuotationForm, QuotationItemInlineFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins.formset import DynamicFormSetView
from django.urls import reverse_lazy
from itertools import groupby
from operator import attrgetter


class QuotationListView(BaseListView):
    model = Quotation
    template_name = 'quotation/quotation_list.html'
    context_object_name = 'quotations'

class BaseQuotationView:
    model = Quotation
    form_class = QuotationForm
    template_name = "quotation/quotation_form.html"
    success_url = reverse_lazy("quotation:quotation_list")
    formset_class = QuotationItemInlineFormSet
    formset_names = ("item_set",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["item_set"] = self.get_item_formset()
        return context
    

class QuotationCreateView(BaseQuotationView, BaseCreateView):
    pass

class QuotationUpdateView(BaseQuotationView, BaseUpdateView):
    pass

class QuotationDeleteView(BaseDeleteView):
    model = Quotation
    success_url = reverse_lazy("quotation:quotation_list")
    success_message = "ลบใบเสนอราคาแล้ว"

class QuotationPrintView(LoginRequiredMixin, DetailView):
    model = Quotation
    template_name = "quotation/print_quotation.html"
    context_object_name = "quotation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quotation = self.object

        # โหลดรายการทั้งหมดที่เกี่ยวข้องกับใบเสนอราคานี้
        items = QuotationItem.objects.filter(quotation=quotation).order_by("section_title", "id")

        # Group by section_title (groupby ต้องเรียงมาก่อน)
        grouped_items = []
        for section, group in groupby(items, key=attrgetter("section_title")):
            grouped_items.append((section, list(group)))

        context["grouped_items"] = grouped_items
        return context
    

class QuotationItemFormsetView(DynamicFormSetView):
    """
    HTMX endpoint สำหรับเพิ่ม/ลบฟอร์ม QuotationItem แบบ dynamic
    """
    form_class = QuotationForm
    formset_class = QuotationItemInlineFormSet
    formset_prefix = "item_set"
    template_name = "quotation/quotation_form.html"
    partial_template = "quotation/partials/item_formset.html"
    success_url = reverse_lazy("quotation:quotation_list")