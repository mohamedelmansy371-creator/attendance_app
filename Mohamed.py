from datetime import datetime
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى كتابة اسمك ورقمك الجامعي (8 أرقام)، ثم الضغط على زر تحديد الموقع والتسجيل."
)

# --- إحداثيات قاعة المحاضرات الخاصة بك ---
CLASS_LAT = 30.718833  # خط العرض للقاعة
CLASS_LON = 31.244533  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 100  # مسافة السماح بالمتر

# استقبال وحفظ البيانات في البداية فور إعادة تحميل الصفحة
if "reg_name" in st.query_params and "reg_id" in st.query_params:
  reg_name = st.query_params["reg_name"]
  reg_id = str(st.query_params["reg_id"])

  if len(reg_id) == 8 and reg_id.isdigit():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
      df = pd.read_csv("attendance_log.csv")
    except FileNotFoundError:
      df = pd.DataFrame(columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"])

    # توحيد نوع البيانات إلى نص لضمان المقارنة الصحيحة
    df["الرقم الجامعي"] = df["الرقم الجامعي"].astype(str)

    if reg_id not in df["الرقم الجامعي"].values:
      new_row = pd.DataFrame(
          [[reg_name, reg_id, timestamp]],
          columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
      )
      df = pd.concat([df, new_row], ignore_index=True)
      df.to_csv("attendance_log.csv", index=False)
      st.success(
          f"🎉 تم تسجيل الطالب ({reg_name}) برقم ({reg_id}) في السجل بنجاح!"
      )
    else:
      st.info(f"ℹ️ الطالب ذو الرقم ({reg_id}) مسجل مسبقاً في كشف الحضور.")

    # مسح البارامترات من الرابط وتحديث الصفحة فوراً لظهر الاسم بالجدول
    st.query_params.clear()
    st.rerun()

# واجهة المدخلات وزر الجي بي إس المدمج
form_html = (
    """
<div style="font-family: Tahoma, sans-serif; padding: 15px; direction: rtl; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">اسم الطالب الثلاثي:</label>
        <input type="text" id="s_name" placeholder="أدخل اسمك الثلاثي هنا" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
    </div>
    
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">الرقم الجامعي / الأكاديمي (8 أرقام إنجليزية):</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="8" id="s_id" placeholder="أدخل 8 أرقام بالضبط" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
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

    if (id.length !== 8 || isNaN(id)) {
        msg.style.color = "red";
        msg.innerHTML = "❌ خطأ: يجب أن يكون الرقم الجامعي مكوناً من 8 أرقام بالضبط!";
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
                msg.innerHTML = "✅ تم التحقق من تواجدك داخل النطاق (المسافة: " + Math.round(distance) + " متر). جاري حفظ الحضور...";
                
                const baseUrl = window.parent.location.href.split('?')[0];
                window.parent.location.href = baseUrl + "?reg_name=" + encodeURIComponent(name) + "&reg_id=" + encodeURIComponent(id);
            } else {
                msg.style.color = "red";
                msg.innerHTML = "❌ عذراً، لم يتم تسجيل حضورك! أنت خارج النطاق (المسافة: " + Math.round(distance) + " متر والمسموح 100 متر).";
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
)

components.html(form_html, height=360)

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
