from django.db import models


class BaseTime(models.Model):
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='สร้างเมื่อ / Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='แก้ไขเมื่อ / Updated At')

    class Meta:
        abstract = True
