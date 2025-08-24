from django import template

register = template.Library()

@register.filter(name="get_value")
def get_value(obj, attr):
    try:
        return getattr(obj, attr, "")
    except Exception:
        return ""
    
@register.filter(name="dict_get")
def dict_get(d: dict, key: str):
    try:
        return d.get(key, key)
    except Exception:
        return key