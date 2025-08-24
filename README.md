Core App for Django

🇹🇭 คำอธิบายภาษาไทย
ภาพรวม

core คือชุดเครื่องมือกลาง App (layer) สำหรับพัฒนา Django 5.2 ERP Application โดยออกแบบให้ทำงานร่วมกับ CBV (Class-Based View), Bootstrap 5, Crispy Forms, และ HTMX

ลดความซ้ำซ้อนในการเขียนโค้ด view/formset
จัดการ Running Number อัตโนมัติ

รองรับ Inline Formset หลายชุดใน transaction เดียว

มี BaseView และ Mixin ที่นำกลับมาใช้ใหม่ได้ในทุกโมดูล
Mixins

FormsetMixin

รวม parent form + inline formset หลายชุดใน transaction เดียว

เติม Running Number ให้อัตโนมัติ

แสดงข้อความสำเร็จ/ล้มเหลวผ่าน messages

BaseCreateView / BaseUpdateView / BaseListView / BaseDetail / BaseDelete
สืบทอดจาก FormsetMixin + Django CBV
1.มี permission checking อัตโนมัติ
2.ListView รองรับ pagination
3.DynamicFormSetView
4.ใช้ร่วมกับ HTMX เพื่อเพิ่ม/ลบ formset dynamically
5.ใช้ partial template ในการโหลดฟอร์มใหม่
6.Running Number
  RunningNumberField
  ฟิลด์พิเศษที่สร้างเลขรันตาม pattern เช่น:
  job_number = RunningNumberField(pattern="{THYY}{MM}{SEQ:04}")
  ตัวอย่าง: 68080123 (ปีไทย 68, เดือน 08, running seq 0123)
  RunningNumberService
  ควบคุมเลขรันให้ไม่ชนกัน (concurrency-safe)
