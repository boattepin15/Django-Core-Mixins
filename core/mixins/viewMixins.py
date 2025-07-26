from django.views.generic import CreateView, UpdateView, ListView, View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from core.mixins.form import FormsetMixin
from django.shortcuts import redirect

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

class BaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    model = None
    success_url = None
    success_message = "ลบข้อมูลสำเร็จแล้ว"
    error_message = "ไม่สามารถลบข้อมูลได้"

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        try:
            obj.delete()
            messages.success(self.request, self.success_message)
        except Exception:
            messages.error(self.request, self.error_message)
        return redirect(self.get_success_url())

    def get_object(self):
        return self.model.objects.get(pk=self.kwargs["pk"])

    def get_success_url(self):
        return self.success_url or "/"

    def get_permission_required(self):
        model = self.model
        return [f"{model._meta.app_label}.delete_{model._meta.model_name}"]