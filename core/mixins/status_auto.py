# core/mixins/status_auto.py
from django.db import models, transaction


class AutoStatusMixin:
    """
    ตัวอย่างใช้งาน ↓
        status_fields = ['Done', 'Paid']        # self = Done, relation#1 = Paid
        status_fields = ['Done', None]          # อัปเดตแค่ self
        status_fields = [None, 'Done']          # ข้าม self, ไปอัปเดต relation#1
    """
    status_fields: list[str | None] = []
    status_attr: str = "status"     

    # ---------- hook ----------
    def form_valid(self, form):
        response = super().form_valid(form) 
        self._cascade_status()
        return response

    # ---------- core ----------
    def _cascade_status(self):
        if not self.status_fields:
            return

        rel_objects: list[models.Model | models.Manager] = []

        # self.object เป็นลำดับที่ 0 เสมอ
        rel_objects.append(self.object)

        # ลำดับต่อ ๆ ไปจาก relation fields
        for field in self.object._meta.get_fields():
            # OneToMany / ManyToMany accessors  (invoice_set / invoices ฯลฯ)
            if field.auto_created and (field.one_to_many or field.many_to_many):
                rel_objects.append(getattr(self.object, field.get_accessor_name()))
            # FK / OneToOne ที่ประกาศตรง ๆ
            elif field.is_relation and not field.auto_created:
                rel_objects.append(getattr(self.object, field.name, None))

        # 2) จับคู่ status_fields ↔ rel_objects แล้วอัปเดต
        with transaction.atomic():
            for idx, status in enumerate(self.status_fields):
                if status is None or idx >= len(rel_objects):
                    continue

                target = rel_objects[idx]

                # ----- A) relation manager -----
                if isinstance(target, models.Manager):
                    model_cls = target.model
                    if hasattr(model_cls, self.status_attr):
                        # M2M ปลายทางมี field status ➜ อัปเดต bulk ได้เลย
                        target.update(**{self.status_attr: status})
                    else:
                        # M2M มี through modelกำหนดเอง ➜ หา through ที่มี status
                        rel_field = target.field
                        through   = rel_field.remote_field.through
                        if hasattr(through, self.status_attr):
                            from_fk = rel_field.m2m_field_name()
                            through.objects.filter(**{from_fk: self.object})\
                                            .update(**{self.status_attr: status})
                        # ถ้าไม่เจอ status เลยก็ข้าม
                    continue

                # ----- B) instance (FK / O2O) -----
                if target is not None and hasattr(target, self.status_attr):
                    setattr(target, self.status_attr, status)
                    target.save(update_fields=[self.status_attr])
