from datetime import datetime
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى كتابة اسمك ورقماً جامحاً مكوناً من 8 أرقام، ثم الضغط على زر تحديد"
    " الموقع."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك ---
CLASS_LAT = 30.718881  # خط العرض للقاعة
CLASS_LON = 31.244518  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 100  # مسافة السماح بالمتر

# مدخلات التطبيق المباشرة (باستخدام عناصر Streamlit الأصلية لضمان ظهور الأزرار فوراً)
student_name = st.text_input(
    "اسم الطالب الثلاثي:", placeholder="أدخل اسمك الثلاثي هنا"
).strip()
student_id = st.text_input(
    "الرقم الجامعي / الأكاديمي (8 أرقام إنجليزية):",
    placeholder="أدخل 8 أرقام بالضبط",
    max_chars=8,
).strip()

# زر التحقق من الرقم أولاً قبل فتح الجي بي إس
if student_name and student_id:
  if len(student_id) != 8 or not student_id.isdigit():
    st.error(
        "❌ خطأ: يجب أن يكون الرقم الجامعي مكوناً من 8 أرقام إنجليزية بالضبط!"
    )
  else:
    st.success(
        "✅ تم التحقق من الرقم الجامعي بنجاح. الآن اضغط على زر تحديد الموقع"
        " أدناه:"
    )

    # مكون الجي بي إس البسيط والمباشر
    gps_html = (
        """
    <div style="text-align: center; font-family: Tahoma, sans-serif; margin-top: 10px;">
        <button onclick="getLocation()" style="background-color: #ff4b4b; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 اضغط هنا لتحديد موقعك الجغرافي وتسجيل الحضور</button>
        <p id="gps_msg" style="margin-top: 10px; font-weight: bold; font-size: 15px;"></p>
    </div>

    <script>
    const CLASS_LAT = __LAT__;
    const CLASS_LON = __LON__;
    const ALLOWED_RADIUS = __RADIUS__;

    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371000;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    function getLocation() {
        const msg = document.getElementById("gps_msg");
        if (!navigator.geolocation) {
            msg.style.color = "red";
            msg.innerHTML = "❌ متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.";
            return;
        }

        msg.style.color = "blue";
        msg.innerHTML = "⏳ جاري تحديد موقعك بدقة، يرجى الانتظار والسماح بالصلاحية...";

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

                if (distance <= ALLOWED_RADIUS) {
                    msg.style.color = "green";
                    msg.innerHTML = "✅ تم التحقق من تواجدك داخل النطاق (المسافة: " + Math.round(distance) + " متر). جاري حفظ الحضور تلقائياً...";
                    
                    // إرسال البيانات فوراً لتسجيلها
                    const baseUrl = window.parent.location.href.split('?')[0];
                    window.parent.location.href = baseUrl + "?done_name=" + encodeURIComponent("__NAME__") + "&done_id=" + encodeURIComponent("__ID__");
                } else {
                    msg.style.color = "red";
                    msg.innerHTML = "❌ عذراً، أنت خارج النطاق المحدد (المسافة: " + Math.round(distance) + " متر والمسموح 100 متر).";
                }
            },
            (error) => {
                msg.style.color = "red";
                msg.innerHTML = "❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.";
            },
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
        );
    }
    </script>
    """
        .replace("__LAT__", str(CLASS_LAT))
        .replace("__LON__", str(CLASS_LON))
        .replace("__RADIUS__", str(ALLOWED_RADIUS_METERS))
        .replace("__NAME__", student_name)
        .replace("__ID__", student_id)
    )

    components.html(gps_html, height=130)

# استقبال بيانات النجاح وحفظها بشكل نهائي ومباشر في السجل
query_params = st.query_params
if "done_name" in query_params and "done_id" in query_params:
  d_name = query_params["done_name"]
  d_id = str(query_params["done_id"])

  if len(d_id) == 8 and d_id.isdigit():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
      df = pd.read_csv("attendance_log.csv")
    except FileNotFoundError:
      df = pd.DataFrame(columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"])

    df["الرقم الجامعي"] = df["الرقم الجامعي"].astype(str)

    if d_id not in df["الرقم الجامعي"].values:
      new_row = pd.DataFrame(
          [[d_name, d_id, timestamp]],
          columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
      )
      df = pd.concat([df, new_row], ignore_index=True)
      df.to_csv("attendance_log.csv", index=False)
      st.success(
          f"🎉 تهانينا يا {d_name}! تم تسجيل حضورك بنجاح في السجل الرسمي للقاعة."
      )
    else:
      st.info(f"ℹ️ الطالب ذو الرقم ({d_id}) مسجل مسبقاً في كشف الحضور.")

    st.query_params.clear()

st.divider()

# --- لوحة تحكم الأستاذ (عرض السجل وتحميله) ---
st.subheader("👨‍🏫 لوحة تحكم الأستاذ (سجل الحضور)")

try:
  log_df = pd.read_csv("attendance_log.csv")
  st.write(f"إجمالي الطلاب الحاضرين: **{len(log_df)}** طالب")
  st.dataframe(log_df, use_container_width=True)

  csv = log_df.to_csv(index=False).encode("utf-8-sig")
  st.download_button(
      label="📥 تحميل كشف الحضور (CSV)",
      data=csv,
      file_name="attendance.csv",
      mime="text/csv",
  )
except FileNotFoundError:
  st.info("لا توجد سجلات حضور مسجلة حتى الآن. سيظهر هنا أسماء الطلاب فور تسجيلهم.")
