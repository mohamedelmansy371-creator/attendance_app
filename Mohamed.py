from datetime import datetime
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى كتابة اسمك ورقمك الجامعي، ثم الضغط على زر تحديد الموقع والتسجيل."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك ---
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 30  # مسافة السماح بالمتر

# واجهة المدخلات وزر الجي بي إس المدمج
form_html = (
    """
<div style="font-family: Tahoma, sans-serif; padding: 10px; direction: rtl; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">اسم الطالب الثلاثي:</label>
        <input type="text" id="s_name" placeholder="أدخل اسمك الثلاثي هنا" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
    </div>
    
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">الرقم الجامعي / الأكاديمي (أرقام إنجليزية مثل 1234):</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" id="s_id" placeholder="أدخل الرقم بالأرقام الإنجليزية" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
    </div>

    <button onclick="verifyAndRegister()" style="background-color: #ff4b4b; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 تحديد الموقع وتسجيل الحضور</button>
    
    <p id="msg" style="margin-top: 15px; font-weight: bold; text-align: center; font-size: 15px;"></p>
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

function verifyAndRegister() {
    const name = document.getElementById("s_name").value.trim();
    const id = document.getElementById("s_id").value.trim();
    const msg = document.getElementById("msg");

    if (!name || !id) {
        msg.style.color = "red";
        msg.innerHTML = "❌ الرجاء إدخال الاسم والرقم الجامعي أولاً!";
        return;
    }

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
                msg.innerHTML = "✅ تم التحقق من تواجدك داخل القاعة (" + Math.round(distance) + " متر). جاري الحفظ...";
                
                const baseUrl = window.parent.location.href.split('?')[0];
                window.parent.location.href = baseUrl + "?name=" + encodeURIComponent(name) + "&id=" + encodeURIComponent(id) + "&lat=" + lat + "&lon=" + lon;
            } else {
                msg.style.color = "red";
                msg.innerHTML = "❌ عذراً، لم يتم تسجيل حضورك! أنت خارج النطاق المحدد (المسافة: " + Math.round(distance) + " متر والمسموح 30 متر).";
            }
        },
        (error) => {
            msg.style.color = "red";
            msg.innerHTML = "❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.";
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
    );
}
</script>
"""
    .replace("__LAT__", str(CLASS_LAT))
    .replace("__LON__", str(CLASS_LON))
    .replace("__RADIUS__", str(ALLOWED_RADIUS_METERS))
)

components.html(form_html, height=330)

# استقبال البيانات المسجلة والتحقق منها في الخلفية لحفظها بالسجل
query_params = st.query_params
name_param = query_params.get("name")
id_param = query_params.get("id")
lat_param = query_params.get("lat")
lon_param = query_params.get("lon")

if name_param and id_param and lat_param and lon_param:
  try:
    u_lat = float(lat_param)
    u_lon = float(lon_param)

    # حساب المسافة للتأكد أماناً على السيرفر
    R = 6371000
    phi1 = math.radians(CLASS_LAT)
    phi2 = math.radians(u_lat)
    delta_phi = math.radians(u_lat - CLASS_LAT)
    delta_lambda = math.radians(u_lon - CLASS_LON)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    if distance <= ALLOWED_RADIUS_METERS:
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      new_data = pd.DataFrame(
          [[name_param, id_param, timestamp]],
          columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
      )

      try:
        df = pd.read_csv("attendance_log.csv")
        if id_param not in df["الرقم الجامعي"].astype(str).values:
          df = pd.concat([df, new_data], ignore_index=True)
          df.to_csv("attendance_log.csv", index=False)
          st.success(
              f"🎉 أهلاً بك يا {name_param}. تم التحقق من تواجدك داخل القاعة"
              f" بنجاح وتسجيل حضورك!"
          )
        else:
          st.info(f"ℹ️ الطالب {name_param} مسجل مسبقاً في كشف الحضور.")
      except FileNotFoundError:
        new_data.to_csv("attendance_log.csv", index=False)
        st.success(
            f"🎉 أهلاً بك يا {name_param}. تم تسجيل حضورك بنجاح داخل القاعة!"
        )
  except Exception as e:
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
