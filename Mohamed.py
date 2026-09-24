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
CLASS_LAT = 30.4682  # خط العرض للقاعة
CLASS_LON = 31.1856  # خط الطول للقاعة
ALLOWED_RADIUS_METERS = 100  # مسافة السماح

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
                msg.innerHTML = "✅ تم التحقق من تواجدك داخل النطاق (المسافة: " + Math.round(distance) + " متر). جاري تسجيل الحضور...";
                
                // استخدام آلية آمنة لتمرير البيانات وحفظها فوراً دون فقدان
                const baseUrl = window.parent.location.href.split('?')[0];
                window.parent.location.href = baseUrl + "?reg_name=" + encodeURIComponent(name) + "&reg_id=" + encodeURIComponent(id) + "&reg_dist=" + Math.round(distance);
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

# استقبال البيانات وحفظها بشكل مباشر ودائم في ملف الـ CSV
query_params = st.query_params
reg_name = query_params.get("reg_name")
reg_id = query_params.get("reg_id")

if reg_name and reg_id:
  try:
    # التأكد من صحة الرقم (8 أرقام) من جهة السيرفر
    if len(str(reg_id)) == 8 and str(reg_id).isdigit():
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      # قراءة أو إنشاء ملف السجل
      try:
        df = pd.read_csv("attendance_log.csv")
      except FileNotFoundError:
        df = pd.DataFrame(columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"])

      # التحقق مما إذا كان الطالب قد تسجل مسبقاً
      if reg_id not in df["الرقم الجامعي"].astype(str).values:
        new_row = pd.DataFrame(
            [[reg_name, reg_id, timestamp]],
            columns=["الاسم", "الرقم الجامعي", "وقت التسجيل"],
        )
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv("attendance_log.csv", index=False)
        st.success(
            f"🎉 أهلاً بك يا {reg_name} (رقم: {reg_id}). تم تسجيل حضورك بنجاح في"
            " السجل!"
        )
      else:
        st.info(f"ℹ️ الطالب {reg_name} مسجل مسبقاً في كشف الحضور بالفعل.")

      # تنظيف رابط الصفحة بعد الحفظ لتجنب التكرار عند التحديث
      st.query_params.clear()
  except Exception as e:
    st.error(f حدث خطأ أثناء الحفظ: {e})

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
