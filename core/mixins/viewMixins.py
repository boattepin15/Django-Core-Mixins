from django.views.generic import CreateView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins.form import FormsetMixin

class BaseCreateView(FormsetMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    success_url = None
    success_message = "สร้างข้อมูลสำเร็จแล้ว"
    error_message = "กรุณาตรวจสอบข้อมูล"


class BaseUpdateView(FormsetMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    success_message = "แก้ไขข้อมูลสำเร็จแล้ว"


class BaseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        return queryset

    def get_permission_required(self):
        model = self.model
        return [f"{model._meta.app_label}.view_{model._meta.model_name}"]
