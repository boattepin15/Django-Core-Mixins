from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from core.serviecs.runningNumber import RunningNumberService
from core.fields import RunningNumberField

class FormsetMixin:
    """
    Mixin สำหรับ CBV ที่รองรับ
      • parent + inline-formset ได้หลายชุดภายใต้ transaction เดียว
      • สร้างเลขรันให้อัตโนมัติทุก RunningNumberField
      • แจ้งข้อความสำเร็จ / ผิดพลาด
    """

    success_url = None
    success_message = "สร้างข้อมูลสำเร็จแล้ว"
    error_message = "กรุณาตรวจสอบข้อมูล"
    status = None

    formset_names = ("formset", )

    # ---------- permission / helper ----------
    def get_object_if_exists(self):
        if hasattr(self, "get_object"):
            try:
                return self.get_object()
            except Exception:  # noqa: E722
                return None
        return None

    def get_permission_required(self):
        model = self.model
        mode = (
            "add"
            if self.request.method.lower() == "post" and not self.get_object_if_exists()
            else "change"
        )
        return [f"{model._meta.app_label}.{mode}_{model._meta.model_name}"]

    def get_status_value(self):
        if self.status is not None:
            return self.status
        return self.request.POST.get("status") or self.request.GET.get("status")
    
    # ---------- running-number helper ----------
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
        """
        ตั้งค่าลง obj.status ถ้ามีค่าที่ได้จาก get_status_value()
        """
        value = self.get_status_value()
        if value and hasattr(obj, "status"):
            obj.status = value
    
    # ---------- core flow ----------
    def form_valid(self, form):
        context = self.get_context_data(form=form)

        # รวม formset
        formsets = [
            context.get(name) for name in self.formset_names if context.get(name) is not None
        ]

        # ถ้ามีสักชุดไม่ผ่าน validation → invalid
        if any(not fs.is_valid() for fs in formsets):
            messages.error(self.request, self.error_message)
            return self.render_to_response(context)

        with transaction.atomic():
            # parent
            self.object = form.save(commit=False)
            if hasattr(self.model, "created_by") and not self.object.pk:
                self.object.created_by = self.request.user
            self._assign_running_numbers(self.object)
            self._assign_status(self.object)
            self.object.save()
            form.save_m2m()

            # children
            for fs in formsets:
                for f in fs.forms:
                    if f.cleaned_data.get("DELETE"):
                        continue
                    self._assign_running_numbers(f.instance)
                fs.instance = self.object
                fs.save()

        messages.success(self.request, self.success_message)
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        # --- ฟอร์มหลัก ---
        print("Main form errors ➜", form.errors, flush=True)

        # --- ฟอร์มเซ็ต (ถ้ามี) ---
        context = self.get_context_data(form=form)
        for name in self.formset_names:
            fs = context.get(name)
            if fs is not None:
                print(f"{name} errors ➜", fs.errors, flush=True)

        messages.error(self.request, self.error_message)
        return self.render_to_response(context)

    def get_success_url(self):
        return self.success_url or "/"