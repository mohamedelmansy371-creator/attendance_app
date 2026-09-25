from datetime import datetime
import math
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى إدخال اسمك وكود الطالب (8 أرقام)، ثم الضغط على زر التحقق والتسجيل."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.718881
CLASS_LON = 31.244633
ALLOWED_RADIUS_METERS = 100

EXCEL_FILE = "attendance_log.xlsx"


# دالة لتهيئة ملف الإكسيل إذا لم يكن موجوداً
def init_excel():
  if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(
        columns=[
            "اسم الطالب",
            "كود الطالب",
            "وقت الحضور",
            "خط العرض",
            "خط الطول",
            "المسافة (متر)",
        ]
    )
    df.to_excel(EXCEL_FILE, index=False)


init_excel()

# معالجة استقبال البيانات المرسلة من JavaScript المحتوي على الـ GPS
query_params = st.query_params
if "action" in query_params and query_params["action"] == "save":
  s_name = query_params.get("name", "")
  s_id = query_params.get("id", "")
  lat = query_params.get("lat", "")
  lon = query_params.get("lon", "")
  dist = query_params.get("dist", "")

  if s_name and s_id:
    # قراءة الملف الحالي
    df = pd.read_excel(EXCEL_FILE)

    # التحقق مما إذا كان الطالب قد سجل مسبقاً
    if str(s_id) in df["كود الطالب"].astype(str).values:
      st.warning(
          f"⚠️ الطالب ذو الكود ({s_id}) مسجل مسبقاً في كشف الحضور بالفعل!"
      )
    else:
      # إضافة البيانات الجديدة
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      new_row = {
          "اسم الطالب": s_name,
          "كود الطالب": str(s_id),
          "وقت الحضور": now_str,
          "خط العرض": lat,
          "خط الطول": lon,
          "المسافة (متر)": dist,
      }
      df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
      df.to_excel(EXCEL_FILE, index=False)
      st.success(
          f"✅ تم تسجيل حضور الطالب: **{s_name}** (الكود: {s_id}) بنجاح في الكشف!"
      )

# واجهة إدخال البيانات والتحقق من الجغرافيا عبر JavaScript
form_html = (
    """
<div style="font-family: Tahoma, sans-serif; padding: 15px; direction: rtl; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">اسم الطالب الثلاثي:</label>
        <input type="text" id="s_name" placeholder="أدخل اسمك الثلاثي هنا" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
    </div>
    
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 5px; color: #333;">كود الطالب (8 أرقام إنجليزية):</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="8" id="s_id" placeholder="أدخل 8 أرقام بالضبط" style="width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;">
    </div>

    <button onclick="verifyAndRegister()" style="background-color: #ff4b4b; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 تحقق من الموقع وسجل الحضور</button>
    
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
        msg.innerHTML = "❌ الرجاء إدخال الاسم وكود الطالب أولاً!";
        return;
    }

    if (id.length !== 8 || isNaN(id)) {
        msg.style.color = "red";
        msg.innerHTML = "❌ خطأ: يجب أن يكون كود الطالب مكوناً من 8 أرقام بالضبط!";
        return;
    }

    if (!navigator.geolocation) {
        msg.style.color = "red";
        msg.innerHTML = "❌ متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.";
        return;
    }

    msg.style.color = "blue";
    msg.innerHTML = "⏳ جاري تحديد موقعك بدقة، يرجى الانتظار...";

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

            if (distance <= ALLOWED_RADIUS) {
                msg.style.color = "green";
                msg.innerHTML = "🎉 مطابقة صحيحة! جاري حفظ الحضور في الكشف...";
                
                // إعادة توجيه الصفحة لتمرير البيانات وبمحافظتها على الـ Streamlit state
                const currentUrl = window.location.href.split('?')[0];
                const targetUrl = currentUrl + "?action=save&name=" + encodeURIComponent(name) + "&id=" + encodeURIComponent(id) + "&lat=" + lat + "&lon=" + lon + "&dist=" + Math.round(distance);
                
                setTimeout(() => {
                    window.location.href = targetUrl;
                }, 1000);

            } else {
                msg.style.color = "red";
                msg.innerHTML = "❌ عذراً، أنت خارج النطاق المسموح! (المسافة: " + Math.round(distance) + " متر والمسموح 100 متر).";
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

components.html(form_html, height=350)

# --- قسم خاص للأستاذ (عرض وتحميل كشف الحضور) ---
st.markdown("---")
st.subheader("👨‍🏫 لوحة تحكم المحاضر (كشف الحضور)")

if os.path.exists(EXCEL_FILE):
  df_view = pd.read_excel(EXCEL_FILE)
  st.metric(label="إجمالي الطلاب المسجلين حتى الآن", value=len(df_view))
  st.dataframe(df_view, use_container_width=True)

  # زر لتحميل الملف بصيغة Excel
  with open(EXCEL_FILE, "rb") as f:
    st.download_button(
        label="📥 تحميل كشف الحضور (Excel)",
        data=f,
        file_name="Attendance_Report.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
else:
  st.info("لا توجد سجلات حضور حتى الآن.")
