from django.db.models import CharField


class RunningNumberField(CharField):
    def __init__(self, *args, pattern: str = "{YYYY}{SEQ:06}", **kwargs):
        self.pattern = pattern
        kwargs.setdefault("max_length", len(pattern.replace("{SEQ:06}", "0"*6)))
        kwargs.setdefault("blank", True)
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["pattern"] = self.pattern 
        return name, path, args, kwargs

"""
ตัวอย่างการใช้งาน
"""
# class Invoice(models.Model):
#     invoice_number = RunningNumberField(
#         pattern="INV{YYYY}{SEQ:04}",   # ➜ 20250001, 20250002, …
#         verbose_name="เลขใบจ่ายเงิน",
#     )