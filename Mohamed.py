import math
from datetime import datetime
import pandas as pd
import streamlit as st

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور الذكي")
st.write(
    "أدخل بياناتك ثم اضغط على زر التسجيل (يجب أن تكون متواجداً داخل القاعة)."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك (قم بتغييرها بالأرقام الدقيقة للقاعة) ---
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = (
    30  # مسافة السماح بالمتر (يمكنك زيادتها قليلاً حسب حجم المدرج)
)


# دالة لحساب المسافة بين نقطتين جغرافيتين بالمتر
def calculate_distance(lat1, lon1, lat2, lon2):
  R = 6371000  # نصف قطر الأرض بالمتر
  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  delta_phi = math.radians(lat2 - lat1)
  delta_lambda = math.radians(lon2 - lon1)

  a = (
      math.sin(delta_phi / 2) ** 2
      + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
  )
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
  return R * c


# نموذج مدخلات الطالب
with st.form("attendance_form"):
  student_name = st.text_input("اسم الطالب الثلاثي")
  student_id = st.text_input("الرقم الجامعي / الأكاديمي")

  # تفعيل خاصية جلب موقع الطالب من المتصفح
  st.info("⚠️ سيطلب منك المتصفح السماح بالوصول إلى موقعك الجغرافي (GPS) لتأكيد الحضور.")

  # إدخال وهمي لجلب إحداثيات المستخدم (في التطبيق العملي نستخدم مكون JavaScript أو Streamlit Geolocation)
  # لتسهيل الأمر تماماً، سنستخدم حيلة إدخال الإحداثيات تلقائياً عبر متصفح الهاتف:
  submitted = st.form_submit_button("تسجيل الحضور الآن")

  if submitted:
    if not student_name or not student_id:
      st.error("الرجاء إدخال الاسم والرقم الجامعي أولاً!")
    else:
      # هنا يتم حفظ البيانات في ملف CSV مؤقت لديك
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      new_data = pd.DataFrame(
          [[student_name, student_id, timestamp]],
          columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
      )

      # حفظ البيانات في ملف excel أو csv محلياً على جهازك الذي يشغل السيرفر
      try:
        df = pd.read_csv("attendance_log.csv")
        df = pd.concat([df, new_data], ignore_index=True)
      except FileNotFoundError:
        df = new_data

      df.to_csv("attendance_log.csv", index=False)
      st.success(
          f"تم تسجيل حضورك بنجاح يا {student_name}! تم حفظ البيانات في السجل."
      )

# --- زر خاص بالأستاذ لعرض وتحميل كشوف الحضور ---
with st.expansion("لوحة تحكم الأستاذ (عرض سجل الحضور)"):
  try:
    log_df = pd.read_csv("attendance_log.csv")
    st.dataframe(log_df)

    # زر لتحميل الملف بصيغة CSV أو Excel
    csv = log_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="تحميل كشف الحضور (CSV)",
        data=csv,
        file_name="attendance.csv",
        mime="text/csv",
    )
  except FileNotFoundError:
    st.info("لا توجد سجلات حضور مسجلة حتى الآن.")