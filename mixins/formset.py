from django.views import View
from django.http import HttpResponse
from django.template.loader import render_to_string


class DynamicFormSetView(View):
    """Parent Add Formset """
    form_class = None
    formset_class = None
    template_name = None
    partial_template = None
    success_url = None
    formset_prefix = 'formset'

    def get_formset_prefix(self):
        """
        ใช้ใน subclass หรือ query param เพื่อควบคุม prefix
        """
        return getattr(self, 'formset_prefix', 'formset')

    def get(self, request, *args, **kwargs):
        if request.htmx and request.GET.get("add-form"):
            return self.render_new_form()
    
    def render_new_form(self):
        print("Render New Form")
        prefix = self.get_formset_prefix()
        formset = self.formset_class(prefix=prefix) 
        form = formset.empty_form                   
        form.prefix = f"{prefix}-{self.request.GET.get('form_count', 0)}"
        html = render_to_string(self.partial_template, {'form': form})
        return HttpResponse(html)