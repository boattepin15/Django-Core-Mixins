from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from core.serviecs.runningNumber import RunningNumberService
from core.fields import RunningNumberField


class FormsetMixin:
    """
    รองรับ CBV + inline formset หลายชุด
    ใช้ร่วมกับ:
      - formset_names = ("image_formset", "note_formset")
      - formset_classes = { "image_formset": AssetImageInlineFormSet, ... }
    """

    success_url = None
    success_message = "สร้างข้อมูลสำเร็จแล้ว"
    error_message = "กรุณาตรวจสอบข้อมูล"
    status = None

    # ปรับ: ให้ None แล้วดึงชื่อจาก formset_classes อัตโนมัติ
    formset_names = None
    formset_classes = {}

    # ---------- helpers (เพิ่มเฉพาะส่วน error ของ formset) ----------
    def _flatten_formset_errors(self, formset, *, label=""):
        """
        แปลง error ของ formset เป็น list[str] อ่านง่าย
        """
        lines = []

        # non_form_errors ของ formset
        for e in formset.non_form_errors():
            lines.append(f"{label}: {e}" if label else str(e))

        # รายฟอร์ม
        for idx, f in enumerate(formset.forms, start=1):
            if not f.errors and not f.non_field_errors():
                continue
            prefix = f"{label} #{idx}" if label else f"#{idx}"

            # field errors
            for name, errs in f.errors.items():
                field_label = getattr(f.fields.get(name), "label", name)
                for e in errs:
                    lines.append(f"{prefix} → {field_label}: {e}")

            # non_field_errors ของฟอร์มเดี่ยว
            for e in f.non_field_errors():
                lines.append(f"{prefix}: {e}")

        return lines

    def _add_formset_errors_to_messages(self, formsets_by_name):
        """
        รวม error ของทุก formset แล้วส่งเข้า messages.error แบบ HTML ที่อ่านง่าย
        """
        blocks = []
        for name, fs in formsets_by_name.items():
            if not fs:
                continue
            errs = self._flatten_formset_errors(fs, label=name)
            if errs:
                blocks.append(
                    f"<strong>{name}</strong><ul>"
                    + "".join(f"<li>{e}</li>" for e in errs)
                    + "</ul>"
                )

        if blocks:
            html = f"{self.error_message}<div class='mt-2'>" + "".join(blocks) + "</div>"
            messages.error(self.request, mark_safe(html))
        else:
            # ถ้าไม่มีข้อความเฉพาะ ก็ส่ง error_message ปกติ
            messages.error(self.request, self.error_message)

    # ---------- โค้ดเดิม ----------
    def get_formset_names(self):
        """คืนชื่อชุดฟอร์มที่ต้องใช้ ตรวจจาก formset_names หรือ formset_classes"""
        if self.formset_names:
            return tuple(self.formset_names)
        if self.formset_classes:
            return tuple(self.formset_classes.keys())
        return tuple()

    def _is_htmx(self):
        return getattr(self.request, "htmx", False) or bool(self.request.META.get("HTTP_HX_REQUEST"))

    def get_success_url(self):
        return self.request.POST.get("next") or self.request.GET.get("next") or self.success_url or "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for name in self.get_formset_names():
            if name in context:
                continue
            formset_class = self.get_formset_class(name)
            if not formset_class:
                continue
            if self.request.method == "POST":
                context[name] = formset_class(
                    self.request.POST,
                    self.request.FILES,
                    instance=getattr(self, "object", None),
                    prefix=name,
                )
            else:
                context[name] = formset_class(
                    instance=getattr(self, "object", None),
                    prefix=name,
                )
        return context

    def get_formset_class(self, name):
        names = self.get_formset_names()
        if not names:
            return None
        if hasattr(self, "formset_class") and len(names) == 1:
            return self.formset_class
        if name in self.formset_classes:
            return self.formset_classes[name]
        raise ImproperlyConfigured(
            f"{self.__class__.__name__} ต้องกำหนด formset_class หรือ formset_classes['{name}']"
        )

    def get_object_if_exists(self):
        if hasattr(self, "get_object"):
            try:
                return self.get_object()
            except Exception:
                return None
        return None

    def get_permission_required(self):
        model = getattr(self, "model", None)
        if not model:
            obj = self.get_object_if_exists()
            if obj:
                model = obj.__class__
            else:
                raise ImproperlyConfigured("Permission system requires model or get_object()")
        mode = (
            "add" if self.request.method.lower() == "post" and not self.get_object_if_exists()
            else "change"
        )
        return [f"{model._meta.app_label}.{mode}_{model._meta.model_name}"]

    def get_status_value(self):
        return self.status or self.request.POST.get("status") or self.request.GET.get("status")

    def _assign_running_numbers(self, obj):
        for field in obj._meta.get_fields(include_hidden=False):
            if isinstance(field, RunningNumberField) and not getattr(obj, field.name):
                number = RunningNumberService.next(
                    model=obj.__class__,
                    field=field.name,
                    pattern=field.pattern,
                )
                setattr(obj, field.name, number)

    def _assign_status(self, obj):
        value = self.get_status_value()
        if value and hasattr(obj, "status"):
            obj.status = value

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        names = self.get_formset_names()
        formsets = [context[name] for name in names if name in context]

        # validate formset
        invalid = [fs for fs in formsets if not fs.is_valid()]
        if invalid:
            formsets_by_name = {name: context.get(name) for name in names}
            self._add_formset_errors_to_messages(formsets_by_name)
            return self.render_to_response(context)  

        with transaction.atomic():
            self.object = form.save(commit=False)
            if hasattr(self.model, "created_by") and not self.object.pk:
                self.object.created_by = self.request.user
            self._assign_running_numbers(self.object)
            self._assign_status(self.object)
            self.object.save()
            form.save_m2m()

            for fs in formsets:
                for f in fs.forms:
                    if f.cleaned_data.get("DELETE"):
                        continue
                    self._assign_running_numbers(f.instance)
                fs.instance = self.object
                fs.save()

        messages.success(self.request, self.success_message)

        if self._is_htmx():
            resp = HttpResponse(status=204)
            resp["HX-Redirect"] = self.get_success_url()
            return resp

        return redirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        # debug print เดิม
        print("Main form errors ➜", form.errors, flush=True)
        for name in self.get_formset_names():
            fs = context.get(name)
            if fs:
                print(f"{name} errors ➜", fs.errors, flush=True)

        names = self.get_formset_names()
        formsets_by_name = {name: context.get(name) for name in names}
        self._add_formset_errors_to_messages(formsets_by_name)

        return self.render_to_response(context) 
