from django import template

register = template.Library()

@register.filter
def get_field(form, name):
    """
    รับ field name (string) แล้วคืนค่าฟิลด์จาก form
    """
    try:
        return form[name]
    except Exception:
        return None