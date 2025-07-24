from core.mixins.viewMixins import (
    BaseListView,
    BaseCreateView          
)
from ..models import Quotation
from django.views.generic import DetailView
from ..forms.quotation import QuotationForm, QuotationItemInlineFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
from core.mixins.formset import DynamicFormSetView
from django.urls import reverse_lazy

class QuotationListView(BaseListView):
    model = Quotation
    template_name = 'quotation/quotation_list.html'
    context_object_name = 'quotations'
class QuotationPrintView(LoginRequiredMixin, DetailView):
    """
    แสดงใบเสนอราคาในรูปแบบ “พร้อมพิมพ์”  (Printable view)

    ✓  Prefetch `items` เพื่อลด query
    ✓  ส่งยอดรวม (subtotal / discount / vat / grand_total) พร้อมไปใน context
    ✓  แนบข้อมูลบริษัท (Pacharasub) ไว้ใน context ให้ template ใช้งานได้ครบทุกช่อง
    """

    model = Quotation
    template_name = "quotation/print_quotation.html"   
    context_object_name = "quotation"

    # --------------------------------------------------------------------- #
    # optimise queries                                                      #
    # --------------------------------------------------------------------- #
    def get_queryset(self):
        return (
            Quotation.objects
            .select_related("created_by")        # ถ้าต้องโชว์ผู้สร้าง
            .prefetch_related("items")           # รายการสินค้า / service
        )

    # --------------------------------------------------------------------- #
    # context                                                               #
    # --------------------------------------------------------------------- #
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.object

        # ข้อมูลรายการ
        ctx["items"] = q.items.all()

        # ยอดรวมต่าง ๆ
        ctx["subtotal"]     = q.subtotal
        ctx["discount"]     = q.discount
        ctx["vat"]          = q.vat
        ctx["grand_total"]  = q.grand_total
        return ctx
    
class QuotationCreateView(BaseCreateView):
    """
    สร้างใบเสนอราคา + รายการสินค้า/บริการ (inline formset)
    """
    model = Quotation
    form_class = QuotationForm
    template_name = "quotation/quotation_form.html"
    success_url = reverse_lazy("quotation:quotation_list")

    # ---------- inline formset ----------
    formset_class = QuotationItemInlineFormSet
    formset_names = ("item_set",)

    # ---------- extra context ----------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # เตรียม formset สำหรับตารางรายการ
        if self.request.method == "POST":
            context["item_set"] = self.formset_class(
                self.request.POST, self.request.FILES, prefix="item_set"
            )
        else:
            context["item_set"] = self.formset_class(prefix="item_set")

        context["page_title"] = "สร้างใบเสนอราคา"
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