from django.core.exceptions import ImproperlyConfigured
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
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

    formset_names = ("formset", )
    formset_classes = {}  # ✅ mapping หลาย formset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for name in self.formset_names:
            if name not in context:
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
        if not self.formset_names:
            return None
        if hasattr(self, "formset_class") and len(self.formset_names) == 1:
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
        formsets = [
            context[name] for name in self.formset_names if name in context
        ]
        if any(not fs.is_valid() for fs in formsets):
            messages.error(self.request, self.error_message)
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
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        print("Main form errors ➜", form.errors, flush=True)
        for name in self.formset_names:
            fs = context.get(name)
            if fs:
                print(f"{name} errors ➜", fs.errors, flush=True)
        messages.error(self.request, self.error_message)
        return self.render_to_response(context)

    def get_success_url(self):
        return self.success_url or "/"
