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
    "يرجى إدخال البيانات المطلوبة، ثم الضغط على زر التحقق من الموقع."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.718881
CLASS_LON = 31.244633
ALLOWED_RADIUS_METERS = 100

EXCEL_FILE = "attendance_log.xlsx"


def init_excel():
  if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(
        columns=[
            "اسم الطالب",
            "كود الطالب",
            "اسم المادة",
            "الفرقة",
            "التوجه",
            "المكان",
            "وقت الحضور",
            "خط العرض",
            "خط الطول",
            "المسافة (متر)",
        ]
    )
    df.to_excel(EXCEL_FILE, index=False)


init_excel()

# معالجة حفظ البيانات عند استقبالها عبر الـ query_params بشكل مدعوم للغة العربية
query_params = st.query_params
if "action" in query_params and query_params["action"] == "save":
  # استخدام decode للتعامل السليم مع الحروف العربية والمسافات المرسلة من الابتكار البرمجي
  import urllib.parse

  s_name = urllib.parse.unquote(query_params.get("name", ""))
  s_id = query_params.get("id", "")
  s_course = urllib.parse.unquote(query_params.get("course", ""))
  s_year = urllib.parse.unquote(query_params.get("year", ""))
  s_track = urllib.parse.unquote(query_params.get("track", "غير متوفر"))
  s_loc = urllib.parse.unquote(query_params.get("loc", ""))
  lat = query_params.get("lat", "")
  lon = query_params.get("lon", "")
  dist = query_params.get("dist", "")

  if s_name and s_id:
    df = pd.read_excel(EXCEL_FILE)

    if str(s_id) in df["كود الطالب"].astype(str).values:
      st.warning(
          f"⚠️ الطالب ذو الكود ({s_id}) مسجل مسبقاً في كشف الحضور بالفعل!"
      )
    else:
      now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      new_row = {
          "اسم الطالب": s_name,
          "كود الطالب": str(s_id),
          "اسم المادة": s_course,
          "الفرقة": s_year,
          "التوجه": s_track if s_year == "الفرقة الرابعة" else "غير مخصص",
          "المكان": s_loc,
          "وقت الحضور": now_str,
          "خط العرض": lat,
          "خط الطول": lon,
          "المسافة (متر)": dist,
      }
      df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
      df.to_excel(EXCEL_FILE, index=False)
      st.success(
          f"✅ تم تسجيل حضور الطالب: **{s_name}** (الكود: {s_id}) للمادة **{s_course}**"
          f" بنجاح!"
      )
      st.query_params.clear()

form_html = (
    """
<div style="font-family: Tahoma, sans-serif; padding: 15px; direction: rtl; background-color: #f9f9f9; border-radius: 10px; border: 1px solid #ddd;">
    <div style="margin-bottom: 12px;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">اسم الطالب الثلاثي:</label>
        <input type="text" id="s_name" placeholder="أدخل اسمك الثلاثي هنا" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box;">
    </div>
    
    <div style="margin-bottom: 12px;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">كود الطالب (8 أرقام إنجليزية):</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="8" id="s_id" placeholder="أدخل 8 أرقام بالضبط" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box;">
    </div>

    <div style="margin-bottom: 12px;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">اسم المادة الدراسية:</label>
        <input type="text" id="s_course" placeholder="أدخل اسم المادة" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box;">
    </div>

    <div style="margin-bottom: 12px;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">الفرقة الدراسية:</label>
        <select id="s_year" onchange="toggleTrack()" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر الفرقة --</option>
            <option value="الفرقة الأولى">الفرقة الأولى</option>
            <option value="الفرقة الثانية">الفرقة الثانية</option>
            <option value="الفرقة الثالثة">الفرقة الثالثة</option>
            <option value="الفرقة الرابعة">الفرقة الرابعة</option>
        </select>
    </div>

    <div id="track_container" style="margin-bottom: 12px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">التوجه (التخصص):</label>
        <select id="s_track" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر التوجه --</option>
            <option value="توجه آلات">توجه آلات</option>
            <option value="توجه ري">توجه ري</option>
            <option value="توجه نظم">توجه نظم</option>
            <option value="توجه عام">توجه عام</option>
        </select>
    </div>

    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">مكان المحاضرة:</label>
        <select id="s_loc" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر المكان --</option>
            <option value="مدرج هندسة 1">مدرج هندسة 1</option>
            <option value="مدرج هندسة 2">مدرج هندسة 2</option>
            <option value="مدرج هندسة 3">مدرج هندسة 3</option>
            <option value="مدرج هندسة 4">مدرج هندسة 4</option>
            <option value="قاعة تدريس 1">قاعة تدريس 1</option>
            <option value="قاعة تدريس 2">قاعة تدريس 2</option>
            <option value="قاعة تدريس 3">قاعة تدريس 3</option>
            <option value="قاعة تدريس 4">قاعة تدريس 4</option>
            <option value="قاعة تدريس 5">قاعة تدريس 5</option>
        </select>
    </div>

    <button onclick="verifyLocation()" style="background-color: #ff4b4b; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 تحقق من الموقع الجغرافي</button>
    
    <p id="msg" style="margin-top: 15px; font-weight: bold; text-align: center; font-size: 15px;"></p>
    
    <!-- زر الإرسال يظهر فقط بعد اجتياز فحص الـ GPS بنجاح -->
    <div id="success_container" style="display: none; margin-top: 15px; text-align: center;">
        <p style="color: green; font-weight: bold; margin-bottom: 8px;">✅ تم التحقق من تواجدك داخل القاعة بنجاح!</p>
        <a id="submit_link" href="#" style="display: block; background-color: #28a745; color: white; padding: 14px 20px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🚀 اضغط هنا لتأكيد وتسجيل الحضور نهائياً</a>
    </div>
</div>

<script>
const CLASS_LAT = __LAT__;
const CLASS_LON = __LON__;
const ALLOWED_RADIUS = __RADIUS__;

function toggleTrack() {
    const year = document.getElementById("s_year").value;
    const trackContainer = document.getElementById("track_container");
    if (year === "الفرقة الرابعة") {
        trackContainer.style.display = "block";
    } else {
        trackContainer.style.display = "none";
        document.getElementById("s_track").value = "";
    }
}

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

function verifyLocation() {
    const name = document.getElementById("s_name").value.trim();
    const id = document.getElementById("s_id").value.trim();
    const course = document.getElementById("s_course").value.trim();
    const year = document.getElementById("s_year").value;
    const track = document.getElementById("s_track").value;
    const loc = document.getElementById("s_loc").value;
    const msg = document.getElementById("msg");
    const successContainer = document.getElementById("success_container");

    if (!name || !id || !course || !year || !loc) {
        msg.style.color = "red";
        msg.innerHTML = "❌ يرجى استيفاء جميع الحقول المطلوبة واختيار المكان والفرقة!";
        successContainer.style.display = "none";
        return;
    }

    if (year === "الفرقة الرابعة" && !track) {
        msg.style.color = "red";
        msg.innerHTML = "❌ يرجى اختيار التوجه الخاص بالفرقة الرابعة!";
        successContainer.style.display = "none";
        return;
    }

    if (id.length !== 8 || isNaN(id)) {
        msg.style.color = "red";
        msg.innerHTML = "❌ خطأ: يجب أن يكون كود الطالب مكوناً من 8 أرقام بالضبط!";
        successContainer.style.display = "none";
        return;
    }

    if (!navigator.geolocation) {
        msg.style.color = "red";
        msg.innerHTML = "❌ متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.";
        successContainer.style.display = "none";
        return;
    }

    msg.style.color = "blue";
    msg.innerHTML = "⏳ جاري تحديد موقعك بدقة، يرجى الانتظار...";
    successContainer.style.display = "none";

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

            if (distance <= ALLOWED_RADIUS) {
                msg.style.color = "green";
                msg.innerHTML = "🎉 مطابقة صحيحة! المسافة عن القاعة: " + Math.round(distance) + " متر.";
                
                // استخدام encodeURIComponent للتأكد من نقل الحروف العربية بالكامل ودون فقدان
                const currentUrl = window.parent.location.href.split('?')[0];
                const targetUrl = currentUrl + "?action=save" +
                                  "&name=" + encodeURIComponent(name) +
                                  "&id=" + encodeURIComponent(id) +
                                  "&course=" + encodeURIComponent(course) +
                                  "&year=" + encodeURIComponent(year) +
                                  "&track=" + encodeURIComponent(track) +
                                  "&loc=" + encodeURIComponent(loc) +
                                  "&lat=" + lat +
                                  "&lon=" + lon +
                                  "&dist=" + Math.round(distance);
                
                document.getElementById("submit_link").href = targetUrl;
                successContainer.style.display = "block";

            } else {
                msg.style.color = "red";
                msg.innerHTML = "❌ عذراً، أنت خارج النطاق المسموح! (المسافة: " + Math.round(distance) + " متر والمسموح 100 متر).";
                successContainer.style.display = "none";
            }
        },
        (error) => {
            msg.style.color = "red";
            msg.innerHTML = "❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.";
            successContainer.style.display = "none";
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

components.html(form_html, height=640)

# --- لوحة تحكم المحاضر ---
st.markdown("---")
st.subheader("👨‍🏫 لوحة تحكم المحاضر (كشف الحضور)")

if os.path.exists(EXCEL_FILE):
  df_view = pd.read_excel(EXCEL_FILE)
  st.metric(label="إجمالي الطلاب المسجلين حتى الآن", value=len(df_view))
  st.dataframe(df_view, use_container_width=True)

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
