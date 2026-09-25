import math
import os
from datetime import datetime
import urllib.parse
import pandas as pd
import requests  # مكتبة إرسال البيانات للرابط
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("نظام تسجيل الحضور الذكي لبرنامج الهندسة الزراعية")
st.write(
    "يرجى إدخال البيانات المطلوبة، ثم الضغط على زر التحقق من الموقع."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.718881
CLASS_LON = 31.244633
ALLOWED_RADIUS_METERS = 100

# رابط الـ Web App الخاص بملف Google Sheets الذي أنشأته
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxvYZXJaC6rgpchmf2jN8TgzzrbukHmc-BiTGVtGBa2XzcJvwVo5oJGcN5LiEgX9j3v2A/exec"

# معالجة حفظ البيانات عند استقبالها عبر الـ query_params وإرسالها لـ Google Sheets
query_params = st.query_params
if "action" in query_params and query_params["action"] == "save":
  s_name = urllib.parse.unquote(query_params.get("name", ""))
  s_id = query_params.get("id", "")
  s_course = urllib.parse.unquote(query_params.get("course", ""))
  s_section = urllib.parse.unquote(query_params.get("section", ""))
  s_year = urllib.parse.unquote(query_params.get("year", ""))
  s_track = urllib.parse.unquote(query_params.get("track", "غير متوفر"))
  s_loc = urllib.parse.unquote(query_params.get("loc", ""))
  lat = query_params.get("lat", "")
  lon = query_params.get("lon", "")
  dist = query_params.get("dist", "")

  if s_name and s_id:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # تجهيز البيانات للإرسال بصيغة JSON
    payload = {
        "name": s_name,
        "id": str(s_id),
        "course": s_course,
        "section": s_section,
        "year": s_year,
        "track": s_track if s_year == "الفرقة الرابعة" else "غير مخصص",
        "loc": s_loc,
        "time": now_str,
        "lat": lat,
        "lon": lon,
        "dist": dist,
    }

    try:
      # إرسال البيانات مباشرة إلى ملف Google Sheets عبر رابط الـ Web App
      response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
      if response.status_code == 200:
        st.success(
            f"✅ تم تسجيل حضور الطالب: **{s_name}** (الكود: {s_id}) للمادة **{s_course}**"
            f" ({s_section}) وحفظه في جدول جوجل شيت بنجاح!"
        )
      else:
        st.error("⚠️ حدث خطأ أثناء الاتصال بملف السيرفر، يرجى المحاولة مرة أخرى.")
    except Exception as e:
      st.error(f"❌ خطأ في الشبكة: {e}")

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
        <select id="s_course" onchange="toggleSection()" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر المادة الدراسية --</option>
            <option value="أساسيات هندسة النظم الزراعية والحيوية">أساسيات هندسة النظم الزراعية والحيوية</option>
            <option value="رياضة هندسة">رياضة هندسة</option>
            <option value="رياضة عام">رياضة عام</option>
            <option value="ميكانيكا (ديناميكا - استاتيكا)">ميكانيكا (ديناميكا - استاتيكا)</option>
            <option value="رسم هندسي (1)">رسم هندسي (1)</option>
            <option value="رياضة تطبيقية">رياضة تطبيقية</option>
            <option value="هيدروليكا وميكانيكا موائع">هيدروليكا وميكانيكا موائع</option>
            <option value="نظرية آلات">نظرية آلات</option>
            <option value="مقدمة في الحاسب الآلي">مقدمة في الحاسب الآلي</option>
            <option value="انتقال حراري">انتقال حراري</option>
            <option value="جرارات زراعية">جرارات زراعية</option>
            <option value="تخطيط وتصميم المنشآت الزراعية">تخطيط وتصميم المنشآت الزراعية</option>
            <option value="هندسة الري والصرف">هندسة الري والصرف</option>
            <option value="هندسة البيوت المحمية">هندسة البيوت المحمية</option>
            <option value="هندسة مزارع الإنتاج الحيواني والداجني">هندسة مزارع الإنتاج الحيواني والداجني</option>
            <option value="التحكم البيئي في المنشآت الزراعية">التحكم البيئي في المنشآت الزراعية</option>
            <option value="تصميم نظم الري">تصميم نظم الري</option>
            <option value="تصميم آلات زراعية">تصميم آلات زراعية</option>
            <option value="إدارة وتشغيل المزارع المائية">إدارة وتشغيل المزارع المائية</option>
            <option value="ميكانيكا تربة">ميكانيكا تربة</option>
            <option value="هيدروليكا الآبار والمضخات">هيدروليكا الآبار والمضخات</option>
            <option value="تخطيط وتصميم نظم الصرف الحقلي">تخطيط وتصميم نظم الصرف الحقلي</option>
            <option value="نظرية اهتزازات وتوازن">نظرية اهتزازات وتوازن</option>
            <option value="معدات التسميد والمكافحة">معدات التسميد والمكافحة</option>
            <option value="الخواص الطبيعية والهندسية للمنتجات الزراعية">الخواص الطبيعية والهندسية للمنتجات الزراعية</option>
            <option value="هندسة تصنيع السماد العضوي المكمور">هندسة تصنيع السماد العضوي المكمور</option>
        </select>
    </div>

    <div id="section_container" style="margin-bottom: 12px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 4px; color: #333;">الشق الدراسي:</label>
        <select id="s_section" style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 15px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر الشق الدراسي --</option>
            <option value="نظري">نظري</option>
            <option value="عملي">عملي</option>
        </select>
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
    
    <div id="success_container" style="display: none; margin-top: 15px; text-align: center;">
        <p style="color: green; font-weight: bold; margin-bottom: 8px;">✅ تم التأكد من موقعك الجغرافي</p>
        <a id="submit_link" href="#" style="display: block; background-color: #28a745; color: white; padding: 14px 20px; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🚀 اضغط هنا لتأكيد وتسجيل الحضور نهائياً</a>
    </div>
</div>

<script>
const CLASS_LAT = __LAT__;
const CLASS_LON = __LON__;
const ALLOWED_RADIUS = __RADIUS__;

function toggleSection() {
    const course = document.getElementById("s_course").value;
    const sectionContainer = document.getElementById("section_container");
    if (course !== "") {
        sectionContainer.style.display = "block";
    } else {
        sectionContainer.style.display = "none";
        document.getElementById("s_section").value = "";
    }
}

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
    const course = document.getElementById("s_course").value;
    const section = document.getElementById("s_section").value;
    const year = document.getElementById("s_year").value;
    const track = document.getElementById("s_track").value;
    const loc = document.getElementById("s_loc").value;
    const msg = document.getElementById("msg");
    const successContainer = document.getElementById("success_container");

    if (!name || !id || !course || !section || !year || !loc) {
        msg.style.color = "red";
        msg.innerHTML = "❌ يرجى استيفاء جميع الحقول المطلوبة واختيار المادة والشق الدراسي والفرقة والمكان!";
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
                msg.innerHTML = "✅ تم التأكد من موقعك الجغرافي";
                
                const currentUrl = window.parent.location.href.split('?')[0];
                const targetUrl = currentUrl + "?action=save" +
                                  "&name=" + encodeURIComponent(name) +
                                  "&id=" + encodeURIComponent(id) +
                                  "&course=" + encodeURIComponent(course) +
                                  "&section=" + encodeURIComponent(section) +
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
                msg.innerHTML = "❌ عذراً، أنت خارج النطاق المسموح للقاعة!";
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

components.html(form_html, height=720)
