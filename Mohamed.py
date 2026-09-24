from datetime import datetime
import math
import pandas as pd
import streamlit as st

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور الذكي")
st.write(
    "أدخل بياناتك ثم اضغط على زر التسجيل (يجب أن تكون متواجداً داخل القاعة)."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك (تم تحديدها مسبقاً) ---
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 30  # مسافة السماح بالمتر

# نموذج مدخلات الطالب
with st.form("attendance_form"):
  student_name = st.text_input("اسم الطالب الثلاثي")
  student_id = st.text_input("الرقم الجامعي / الأكاديمي")

  st.info("⚠️ تأكد من تواجدك داخل القاعة والسماح للمتصفح بتحديد الموقع.")

  submitted = st.form_submit_button("تسجيل الحضور الآن")

  if submitted:
    if not student_name or not student_id:
      st.error("الرجاء إدخال الاسم والرقم الجامعي أولاً!")
    else:
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      new_data = pd.DataFrame(
          [[student_name, student_id, timestamp]],
          columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
      )

      try:
        df = pd.read_csv("attendance_log.csv")
        df = pd.concat([df, new_data], ignore_index=True)
      except FileNotFoundError:
        df = new_data

      df.to_csv("attendance_log.csv", index=False)
      st.success(
          f"تم تسجيل حضورك بنجاح يا {student_name}! تم حفظ البيانات في السجل."
      )

st.divider()

# --- لوحة تحكم الأستاذ (تظهر مباشرة واضحة في الأسفل) ---
st.subheader("👨‍🏫 لوحة تحكم الأستاذ (سجل الحضور)")

try:
  log_df = pd.read_csv("attendance_log.csv")
  st.write(f"إجمالي الطلاب المسجلين: **{len(log_df)}** طالب")
  st.dataframe(log_df)

  csv = log_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 تحميل كشف الحضور (CSV)",
      data=csv,
      file_name="attendance.csv",
      mime="text/csv",
  )
except FileNotFoundError:
  st.info(
      "لا توجد سجلات حضور مسجلة حتى الآن. ستظهر الأسماء هنا فور تسجل أول طالب."
  )
