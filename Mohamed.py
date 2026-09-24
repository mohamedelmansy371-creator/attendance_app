from datetime import datetime
import math
import pandas as pd
import streamlit as st
from streamlit_geolocation import streamlit_geolocation

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى فتح الرابط من متصفح الهاتف (مثل Google Chrome أو Safari) وتفعيل خدمة"
    " الموقع (GPS)."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك ---
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 30  # مسافة السماح بالمتر


# دالة دقيقة لحساب المسافة بالأمتار
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


# إدخال بيانات الطالب
student_name = st.text_input("اسم الطالب الثلاثي")
student_id = st.text_input("الرقم الجامعي / الأكاديمي")

st.markdown("---")
st.write("📍 **اضغط على الزر أدناه لجلب موقعك الحالي والتحقق من تواجدك:**")

# جلب الموقع الجغرافي
location = streamlit_geolocation()

if st.button("التحقق وتثبيت الحضور"):
  if not student_name or not student_id:
    st.error("الرجاء إدخال الاسم والرقم الجامعي أولاً!")
  elif not location or "latitude" not in location or not location["latitude"]:
    st.error(
        "❌ لم نتمكن من تحديد موقعك! يرجى التأكد من فتح الموقع (GPS) والسماح"
        " للمتصفح بالوصول إلى موقعك، ثم إعادة المحاولة."
    )
  else:
    student_lat = location["latitude"]
    student_lon = location["longitude"]

    # حساب المسافة الفعلية
    distance = calculate_distance(
        CLASS_LAT, CLASS_LON, student_lat, student_lon
    )

    # التحقق الصارم من النطاق
    if distance <= ALLOWED_RADIUS_METERS:
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
          f"🎉 أهلاً بك يا {student_name}. تم التحقق من تواجدك داخل القاعة (المسافة:"
          f" {round(distance)} متر) وتسجيل حضورك بنجاح!"
      )
    else:
      st.error(
          f"❌ عذراً يا {student_name}، أنت خارج نطاق القاعة الدراسية! المسافة"
          f" المقاسة هي {round(distance)} متراً (المسموح به {ALLOWED_RADIUS_METERS}"
          " متراً فقط). لا يمكن تسجيل الحضور."
      )

st.divider()

# --- لوحة تحكم الأستاذ ---
st.subheader("👨‍🏫 لوحة تحكم الأستاذ (سجل الحضور)")

try:
  log_df = pd.read_csv("attendance_log.csv")
  st.write(f"إجمالي الطلاب الحاضرين في القاعة: **{len(log_df)}** طالب")
  st.dataframe(log_df)

  csv = log_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 تحميل كشف الحضور (CSV)",
      data=csv,
      file_name="attendance.csv",
      mime="text/csv",
  )
except FileNotFoundError:
  st.info("لا توجد سجلات حضور مسجلة حتى الآن.")
