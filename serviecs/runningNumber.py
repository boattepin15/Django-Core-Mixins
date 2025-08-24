import re
from django.db import transaction
from django.utils import timezone

class RunningNumberService:
    VARS = {
        "YYYY": lambda n: f"{n.year:04}",
        "YY":   lambda n: f"{n.year:04}"[-2:],
        "THYY": lambda n: f"{n.year + 543}"[-2:],
        "MM":   lambda n: f"{n:%m}",
    }

    @classmethod
    def next(cls, model, field, pattern: str) -> str:
        """
        รับ pattern เช่น '{YYYY}{SEQ:04}'  แล้วคืนค่าหมายเลขถัดไป (safe-concurrency)
        """
        now = timezone.now()
        # แทน year / month ล่วงหน้าเพื่อสร้าง prefix ค้นหา
        prefix = pattern
        for k, fn in cls.VARS.items():
            prefix = prefix.replace(f"{{{k}}}", fn(now))
        # เปลี่ยน {SEQ:n} เป็น empty เพื่อใช้เป็น startswith
        prefix = re.sub(r"\{SEQ:\d+\}", "", prefix)

        with transaction.atomic():
            latest = (model.objects.select_for_update()
                      .filter(**{f"{field}__startswith": prefix})
                      .order_by(f"-{field}")
                      .values_list(field, flat=True)
                      .first())

            seq_pad = int(re.search(r"\{SEQ:(\d+)\}", pattern).group(1))
            curr_seq = int(latest[-seq_pad:]) if latest else 0
            next_seq = str(curr_seq + 1).zfill(seq_pad)

        # ประกอบผลลัพธ์จริง
        number = pattern
        for k, fn in cls.VARS.items():
            number = number.replace(f"{{{k}}}", fn(now))
        number = re.sub(r"\{SEQ:\d+\}", next_seq, number)
        return number
