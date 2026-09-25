from datetime import datetime
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")

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

# استخدام نموذج Streamlit الأصلي لضمان الحفظ الدقيق للغة العربية والبيانات
with st.form("attendance_form"):
  st.write("يرجى إدخال البيانات بدقة:")

  s_name = st.text_input("اسم الطالب الثلاثي")
  s_id = st.text_input(
      "كود الطالب (8 أرقام إنجليزية)", max_chars=8, placeholder="مثال: 12345678"
  )
  s_course = st.text_input("اسم المادة الدراسية")

  s_year = st.selectbox(
      "الفرقة الدراسية",
      [
          "-- اختر الفرقة --",
          "الفرقة الأولى",
          "الفرقة الثانية",
          "الفرقة الثالثة",
          "الفرقة الرابعة",
      ],
  )

  s_track = "غير مخصص"
  if s_year == "الفرقة الرابعة":
    s_track = st.selectbox(
        "التوجه (التخصص)",
        ["-- اختر التوجه --", "توجه آلات", "توجه ري", "توجه نظم", "توجه عام"],
    )

  s_loc = st.selectbox(
      "مكان المحاضرة",
      [
          "-- اختر المكان --",
          "مدرج هندسة 1",
          "مدرج هندسة 2",
          "مدرج هندسة 3",
          "مدرج هندسة 4",
          "قاعة تدريس 1",
          "قاعة تدريس 2",
          "قاعة تدريس 3",
          "قاعة تدريس 4",
          "قاعة تدريس 5",
      ],
  )

  submitted = st.form_submit_button(
      "📍 تحقق من الموقع وسجل الحضور", use_container_width=True
  )

if submitted:
  # التحقق من صحة الحقول
  if (
      not s_name.strip()
      or not s_id.strip()
      or not s_course.strip()
      or s_year.startswith("--")
      or s_loc.startswith("--")
  ):
    st.error("❌ يرجى استيفاء جميع الحقول واختيار الفرقة والمكان بشكل صحيح!")
  elif s_year == "الفرقة الرابعة" and s_track.startswith("--"):
    st.error("❌ يرجى اختيار التوجه الخاص بالفرقة الرابعة!")
  elif len(s_id.strip()) != 8 or not s_id.strip().isdigit():
    st.error("❌ خطأ: يجب أن يكون كود الطالب مكوناً من 8 أرقام إنجليزية بالضبط!")
  else:
    # كود الجافاسكريبت المخصص لجلب إحداثيات المتصفح والتحقق منها ومقارنتها بسيرفر بايثون
    location_html = """
        <div id="loc_status" style="font-family: Tahoma; font-weight: bold; color: blue; text-align: center; padding: 10px;">
            ⏳ جاري تحديد موقعك الجغرافي عبر الهاتف، يرجى الانتظار والسماح بالصلاحية...
        </div>
        <script>
        const CLASS_LAT = """ + str(CLASS_LAT) + """;
        const CLASS_LON = """ + str(CLASS_LON) + """;
        const ALLOWED_RADIUS = """ + str(ALLOWED_RADIUS_METERS) + """;

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

        if (!navigator.geolocation) {
            document.getElementById("loc_status").innerHTML = "❌ متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.";
        } else {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

                    if (distance <= ALLOWED_RADIUS) {
                        document.getElementById("loc_status").style.color = "green";
                        document.getElementById("loc_status").innerHTML = "✅ تم التحقق من تواجدك داخل النطاق! (المسافة: " + Math.round(distance) + " متر). جاري الحفظ...";
                        
                        // إعادة توجيه الصفحة مع تمرير الإحداثيات والمسافة لتأكيد الحفظ في بايثون
                        const baseUrl = window.location.href.split('?')[0];
                        const finalUrl = baseUrl + "?verified=true" +
                                         "&lat=" + lat +
                                         "&lon=" + lon +
                                         "&dist=" + Math.round(distance);
                        setTimeout(() => { window.location.href = finalUrl; }, 1000);
                    } else {
                        document.getElementById("loc_status").style.color = "red";
                        document.getElementById("loc_status").innerHTML = "❌ عذراً، أنت خارج النطاق المسموح! المسافة الحالية: " + Math.round(distance) + " متر (المسموح 100 متر فقط).";
                    }
                },
                (error) => {
                    document.getElementById("loc_status").style.color = "red";
                    document.getElementById("loc_status").innerHTML = "❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.";
                },
                { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
            );
        }
        </script>
        """
    # حفظ بيانات النموذج المؤقتة في الـ Session State لضمان عدم ضياعها
    st.session_state["temp_name"] = s_name.strip()
    st.session_state["temp_id"] = s_id.strip()
    st.session_state["temp_course"] = s_course.strip()
    st.session_state["temp_year"] = s_year
    st.session_state["temp_track"] = s_track
    st.session_state["temp_loc"] = s_loc

    components.html(location_html, height=100)

# معالجة وحفظ البيانات نهائياً بعد نجاح مطابقة الـ GPS وتحديث الصفحة
query_params = st.query_params
if "verified" in query_params and "temp_name" in st.session_state:
  lat = query_params.get("lat", "0")
  lon = query_params.get("lon", "0")
  dist = query_params.get("dist", "0")

  s_name = st.session_state["temp_name"]
  s_id = st.session_state["temp_id"]
  s_course = st.session_state["temp_course"]
  s_year = st.session_state["temp_year"]
  s_track = st.session_state["temp_track"]
  s_loc = st.session_state["temp_loc"]

  df = pd.read_excel(EXCEL_FILE)

  if str(s_id) in df["كود الطالب"].astype(str).values:
    st.warning(f"⚠️ الطالب ذو الكود ({s_id}) مسجل مسبقاً في كشف الحضور بالفعل!")
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
        f"🎉 تم تسجيل حضور الطالب: **{s_name}** (الكود: {s_id}) للمادة"
        f" **{s_course}** بنجاح تام في شيت الإكسيل!"
    )
    # تنظيف المتغيرات المؤقتة
    for key in list(st.session_state.keys()):
      if key.startswith("temp_"):
        del st.session_state[key]
    st.query_params.clear()

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
