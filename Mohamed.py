from datetime import datetime
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى إدخال بياناتك ثم الضغط على زر تحديد الموقع للتحقق من تواجدك داخل"
    " القاعة."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك ---
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 30  # مسافة السماح بالمتر


# دالة حساب المسافة بالأمتار
def calculate_distance(lat1, lon1, lat2, lon2):
  R = 6371000
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


# مدخلات الطالب
student_name = st.text_input("اسم الطالب الثلاثي")
student_id = st.text_input("كود الطالب")

st.markdown("---")
st.write("📍 **التحقق من الموقع الجغرافي:**")

# استخدام جافا سكريبت لجلب إحداثيات هاتف الطالب مباشرة بطريقة آمنة وفعالة
location_code = """
<div style="text-align: center; margin: 10px;">
    <button onclick="getLocation()" style="background-color: #ff4b4b; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 اضغط هنا لتحديد موقعك الحالي تلقائياً</button>
    <p id="status" style="margin-top: 10px; font-weight: bold; color: #333;"></p>
</div>

<script>
function getLocation() {
    const status = document.getElementById("status");
    if (!navigator.geolocation) {
        status.innerHTML = "متصفحك لا يدعم تحديد الموقع الجغرافي.";
        return;
    }
    
    status.innerHTML = "جاري تحديد موقعك، يرجى الانتظار والسماح بالصلوحية...";
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            status.innerHTML = "✅ تم تحديد الموقع بنجاح! جاري التسجيل...";
            
            // إعادة توجيه الإحداثيات تلقائياً إلى تطبيق ستريمليت
            const streamlit_url = window.location.href.split('?')[0];
            window.location.href = `${streamlit_url}?lat=${lat}&lon=${lon}`;
        },
        () => {
            status.innerHTML = "❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح.";
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}
</script>
"""

components.html(location_code, height=120)

# استقبال الإحداثيات المرسلة من متصفح الطالب
query_params = st.query_params
user_lat = query_params.get("lat")
user_lon = query_params.get("lon")

if user_lat and user_lon:
  try:
    u_lat = float(user_lat)
    u_lon = float(user_lon)

    if not student_name or not student_id:
      st.warning(
          "⚠️ يرجى كتابة (اسم الطالب) و(الرقم الجامعي) في الخانات بالأعلى أولاً"
          " قبل الضغط على زر تحديد الموقع!"
      )
    else:
      distance = calculate_distance(CLASS_LAT, CLASS_LON, u_lat, u_lon)

      if distance <= ALLOWED_RADIUS_METERS:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_data = pd.DataFrame(
            [[student_name, student_id, timestamp]],
            columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
        )

        try:
          df = pd.read_csv("attendance_log.csv")
          # منع تكرار نفس الرقم الجامعي في نفس المحاضرة
          if student_id not in df["الرقم الجامعي"].astype(str).values:
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv("attendance_log.csv", index=False)
            st.success(
                f"🎉 أهلاً بك يا {student_name}. تم التحقق من تواجدك داخل القاعة"
                f" (المسافة: {round(distance)} متر) وتسجيل حضورك بنجاح!"
            )
          else:
            st.info("ℹ️ أنت مسجل مسبقاً في كشف الحضور.")
        except FileNotFoundError:
          new_data.to_csv("attendance_log.csv", index=False)
          st.success(
              f"🎉 أهلاً بك يا {student_name}. تم تسجيل حضورك بنجاح داخل القاعة!"
          )
      else:
        st.error(
            f"❌ عذراً يا {student_name}، أنت خارج نطاق القاعة الدراسية! المسافة"
            f" المقاسة: {round(distance)} متراً (الحد المسموح: {ALLOWED_RADIUS_METERS}"
            " متر)."
        )
  except ValueError:
    pass

st.divider()

# --- لوحة تحكم الأستاذ ---
st.subheader("👨‍🏫 لوحة تحكم الأستاذ (سجل الحضور)")

try:
  log_df = pd.read_csv("attendance_log.csv")
  st.write(f"إجمالي الطلاب الحاضرين: **{len(log_df)}** طالب")
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
