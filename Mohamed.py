import math
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى إدخال البيانات المطلوبة بدقة، ثم الضغط على زر التحقق من الموقع وتسجيل"
    " الحضور."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.718881
CLASS_LON = 31.244633
ALLOWED_RADIUS_METERS = 100

# رابط الـ Web App الجديد الخاص بك
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyWzDVaeoEo1-moJC7UycBA1qpSTInUUPpPpD5euhqOqFPtpaRbaFmA13_ZQlBTGdK67w/exec"

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

    <button onclick="verifyAndSubmit()" style="background-color: #28a745; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">📍 تحقق من الموقع وتسجيل الحضور</button>
    
    <p id="msg" style="margin-top: 15px; font-weight: bold; text-align: center; font-size: 15px;"></p>
</div>

<script>
const CLASS_LAT = __LAT__;
const CLASS_LON = __LON__;
const ALLOWED_RADIUS = __RADIUS__;
const SCRIPT_URL = "__URL__";

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

function verifyAndSubmit() {
    const name = document.getElementById("s_name").value.trim();
    const id = document.getElementById("s_id").value.trim();
    const course = document.getElementById("s_course").value;
    const section = document.getElementById("s_section").value;
    const year = document.getElementById("s_year").value;
    const track = document.getElementById("s_track").value;
    const loc = document.getElementById("s_loc").value;
    const msg = document.getElementById("msg");

    if (!name || !id || !course || !section || !year || !loc) {
        msg.style.color = "red";
        msg.innerHTML = "❌ يرجى استيفاء جميع الحقول المطلوبة واختيار المادة والشق الدراسي والفرقة والمكان!";
        return;
    }

    if (year === "الفرقة الرابعة" && !track) {
        msg.style.color = "red";
        msg.innerHTML = "❌ يرجى اختيار التوجه الخاص بالفرقة الرابعة!";
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
    msg.innerHTML = "⏳ جاري تحديد موقعك الجغرافي والتحقق من النطاق...";

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

            if (distance <= ALLOWED_RADIUS) {
                msg.style.color = "blue";
                msg.innerHTML = "⏳ تم التحقق من الموقع، جاري إرسال وتسجيل الحضور...";

                const data = {
                    name: name,
                    id: id,
                    course: course,
                    section: section,
                    year: year,
                    track: (year === "الفرقة الرابعة") ? track : "غير مخصص",
                    loc: loc,
                    lat: lat,
                    lon: lon,
                    dist: Math.round(distance)
                };

                # إرسال البيانات باستخدام Fetch API مباشرة إلى Google Sheets Web App
                fetch(SCRIPT_URL, {
                    method: "POST",
                    mode: "no-cors", # لتجنب مشاكل الـ CORS في قوقل سكريبت
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                }).then(() => {
                    msg.style.color = "green";
                    msg.innerHTML = "✅ تم تسجيل حضورك بنجاح وحفظه في جدول البيانات!";
                }).catch((error) => {
                    msg.style.color = "red";
                    msg.innerHTML = "❌ حدث خطأ أثناء الاتصال بالخادم، يرجى المحاولة مرة أخرى.";
                });

            } else {
                msg.style.color = "red";
                msg.innerHTML = "❌ عذراً، أنت خارج النطاق المسموح للقاعة (المسافة: " + Math.round(distance) + " متر)!";
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
    .replace("__URL__", GOOGLE_SCRIPT_URL)
)

components.html(form_html, height=650)
