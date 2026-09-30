import math
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

# --- لوحة التحكم الجانبية للمشرف (أنت) ---
st.sidebar.title("🔐 لوحة تحكم المشرف")
admin_password_input = st.sidebar.text_input(
    "كلمة مرور المشرف", type="password", placeholder="أدخل كلمة المرور"
)

ADMIN_SECRET_PASS = "5994"

otp_enabled = False
current_otp = ""

if admin_password_input == ADMIN_SECRET_PASS:
    st.sidebar.success("تم تسجيل الدخول بنجاح كمشرف ✅")
    st.sidebar.markdown("---")
    st.sidebar.subheader("إدارة رمز التحقق (OTP)")

    use_otp = st.sidebar.checkbox("تفعيل نظام رمز التحقق (OTP)", value=True)

    if use_otp:
        otp_enabled = True
        current_otp = st.sidebar.text_input(
            "الرمز الحالي للمحاضرة",
            value="7890",
            help="اكتب الرمز الذي ستعطيه للطلاب في المدرج",
        )
    else:
        otp_enabled = False
        current_otp = ""
else:
    if admin_password_input != "":
        st.sidebar.error("كلمة المرور غير صحيحة")
    otp_enabled = True
    current_otp = "7890"

st.title("نظام تسجيل الحضور الذكي")
st.write(
    "يرجى إدخال البيانات المطلوبة بدقة، ثم الضغط على زر التحقق من الموقع وتسجيل الحضور."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.353160
CLASS_LON = 31.224244
ALLOWED_RADIUS_METERS = 500

# رابط الـ Web App الخاص بك
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyOwQi0NR-XzZ1jQSYmezWL-KmWA1gu1d36T5GSZOMSBGx5dlAJ42mDIxaFwojDnYWx/exec"

SHOW_OTP_FIELD = "block" if otp_enabled else "none"
SERVER_OTP = str(current_otp).strip()

form_html = """
<div id="browser_warning_container" style="display: none; font-family: Tahoma, sans-serif; padding: 30px; direction: rtl; background-color: #f8d7da; border-radius: 12px; border: 2px solid #f5c6cb; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px;">
    <h2 style="color: #721c24; margin-bottom: 15px;">⚠️ تنبيه هـام جداً - المتصفح غير مسموح</h2>
    <p style="font-size: 18px; color: #721c24; line-height: 1.6; font-weight: bold;">
        عذراً، لا يمكن تسجيل الحضور إلا من خلال <b>متصفح جوجل كروم (Google Chrome) الأساسي</b> فقط.
    </p>
    <p style="font-size: 16px; color: #555; line-height: 1.5; margin-bottom: 20px;">
        يبدو أنك تفتح الرابط من متصفح غير مدعوم أو من داخل تطبيق خارجي (مثل فيسبوك، واتساب، إلخ). يرجى نسخ الرابط فتحه مباشرة في تطبيق <b>جوجل كروم</b> بهاتفك.
    </p>
    <button onclick="copyLinkAndOpen()" style="background-color: #17a2b8; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">📋 نسخ الرابط لفتحه في كروم</button>
</div>

<div id="main_app_container" style="display: none; font-family: Tahoma, sans-serif; padding: 25px; direction: rtl; background-color: #f9f9f9; border-radius: 12px; border: 1px solid #ddd; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">اسم الطالب الثلاثي:</label>
        <input type="text" id="s_name" placeholder="أدخل اسمك الثلاثي هنا" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box;">
    </div>
    
    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">الرقم القومي (14 رقم بالإنجليزية):</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" maxlength="14" id="s_id" placeholder="أدخل 14 رقم بالضبط" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box;">
    </div>

    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">يوم الأسبوع:</label>
        <input type="text" id="s_day" readonly placeholder="جاري التقاط اليوم تلقائياً..." style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; background-color: #e9ecef; font-weight: bold; color: #0275d8; box-sizing: border-box;">
    </div>

    <div style="margin-bottom: 15px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">الفرقة الدراسية:</label>
        <select id="s_year" onchange="onYearChange()" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر الفرقة --</option>
            <option value="الفرقة الأولى">الفرقة الأولى</option>
            <option value="الفرقة الثانية">الفرقة الثانية</option>
            <option value="الفرقة الثالثة">الفرقة الثالثة</option>
            <option value="الفرقة الرابعة">الفرقة الرابعة</option>
        </select>
    </div>

    <div id="track_container" style="margin-bottom: 15px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">التوجه (التخصص):</label>
        <select id="s_track" onchange="onTrackChange()" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر التوجه --</option>
            <option value="توجه آلات">توجه آلات</option>
            <option value="توجه ري">توجه ري</option>
            <option value="توجه نظم">توجه نظم</option>
            <option value="توجه عام">توجه عام</option>
        </select>
    </div>

    <div id="course_container" style="margin-bottom: 15px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">اسم المادة الدراسية:</label>
        <select id="s_course" onchange="toggleSection()" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر المادة الدراسية --</option>
        </select>
    </div>

    <div id="section_container" style="margin-bottom: 15px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">الشق الدراسي:</label>
        <select id="s_section" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر الشق الدراسي --</option>
            <option value="نظري">نظري</option>
            <option value="عملي">عملي</option>
        </select>
    </div>

    <div style="margin-bottom: 18px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">مكان المحاضرة:</label>
        <select id="s_loc" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
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

    <div style="margin-bottom: 18px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">وقت الحضور المسجل:</label>
        <input type="text" id="s_time" readonly placeholder="سيتم التقاط الوقت تلقائياً عند التسجيل" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; background-color: #e9ecef; box-sizing: border-box;">
    </div>

    <div id="otp_box_container" style="margin-bottom: 20px; display: __SHOW_OTP__;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #c0392b; font-size: 16px;">🔐 رمز التحقق (OTP) المعلن في القاعة:</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" id="s_otp" placeholder="أدخل الرمز التحقق" style="width: 100%; padding: 14px; border: 2px dashed #e74c3c; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: #fff5f5;">
    </div>

    <button onclick="verifyAndSubmit()" style="background-color: #28a745; color: white; padding: 16px 20px; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; width: 100%; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">📍 تحقق من الموقع وتسجيل الحضور</button>
    
    <div id="msg_container" style="margin-top: 25px; padding: 20px; border-radius: 10px; text-align: center; display: none; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <p id="msg" style="margin: 0; font-weight: bold; font-size: 17px; line-height: 1.6;"></p>
    </div>
</div>

<script>
const CLASS_LAT = __LAT__;
const CLASS_LON = __LON__;
const ALLOWED_RADIUS = __RADIUS__;
const SCRIPT_URL = "__URL__";
const OTP_ENABLED = __OTP_ENABLED__;
const CORRECT_OTP = "__CORRECT_OTP__";

const coursesData = {
    "الفرقة الأولى": [
        "رياضة عام",
        "أساسيات هندسة النظم الزراعية والحيوية",
        "رياضة هندسة",
        "ميكانيكا (ديناميكا – استاتيكا)",
        "رسم هندسي (1)"
    ],
    "الفرقة الثانية": [
        "رياضة تطبيقية",
        "هيدروليكا وميكانيكا موائع",
        "نظرية آلات",
        "مقدمة في الحاسب الآلي",
        "انتقال حراري"
    ],
    "الفرقة الثالثة": [
        "جرارات زراعية",
        "تخطيط وتصميم المنشآت الزراعية",
        "هندسة الري والصرف",
        "هندسة البيوت المحمية",
        "هندسة مزارع الإنتاج الحيواني والداجني",
        "مصطلحات علمية باللغة الإنجليزية"
    ],
    "الفرقة الرابعة": {
        "توجه آلات": [
            "التحكم البيئي في المنشآت الزراعية",
            "تصميم نظم الري",
            "تصميم آلات زراعية",
            "أساليب البحث العلمي",
            "نظرية اهتزازات وتوازن",
            "ميكانيكا تربة",
            "معدات التسميد والمكافحة"
        ],
        "توجه ري": [
            "التحكم البيئي في المنشآت الزراعية",
            "تصميم نظم الري",
            "تصميم آلات زراعية",
            "أساليب البحث العلمي",
            "هيدروليكا الآبار والمضخات",
            "ميكانيكا تربة",
            "تخطيط وتصميم نظم الصرف الحقلي"
        ],
        "توجه نظم": [
            "التحكم البيئي في المنشآت الزراعية",
            "تصميم نظم الري",
            "تصميم آلات زراعية",
            "أساليب البحث العلمي",
            "إدارة وتشغيل المزارع المائية",
            "الخواص الطبيعية والهندسية للمنتجات الزراعية",
            "هندسة تصنيع السماد العضوي المكمور"
        ],
        "توجه عام": [
            "التحكم البيئي في المنشآت الزراعية",
            "تصميم نظم الري",
            "تصميم آلات زراعية",
            "أساليب البحث العلمي",
            "معدات التسميد والمكافحة",
            "تخطيط وتصميم نظم الصرف الحقلي",
            "هندسة تصنيع السماد العضوي المكمور"
        ]
    }
};

document.addEventListener("DOMContentLoaded", function() {
    const ua = navigator.userAgent;
    
    // شروط صارمة لفحص كروم واستبعاد أي متصفح خارجي أو مدمج
    const isChromeBrowser = /Chrome|CriOS/.test(ua);
    const isExcludedBrowser = /Edg|OPR|SamsungBrowser|UCBrowser|Firefox|MiuiBrowser|Whale|Yandex|FBAN|FBAV|Instagram|WhatsApp|Twitter/i.test(ua);
    const isActualChrome = isChromeBrowser && !isExcludedBrowser;

    const warningBox = document.getElementById("browser_warning_container");
    const mainApp = document.getElementById("main_app_container");

    if (!isActualChrome) {
        if (warningBox) warningBox.style.display = "block";
        if (mainApp) mainApp.style.display = "none";
    } else {
        if (warningBox) warningBox.style.display = "none";
        if (mainApp) mainApp.style.display = "block";
        
        const daysMap = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"];
        const todayIndex = new Date().getDay();
        const dayInput = document.getElementById("s_day");
        if(dayInput) dayInput.value = daysMap[todayIndex];
    }
});

function copyLinkAndOpen() {
    const currentUrl = window.location.href;
    navigator.clipboard.writeText(currentUrl).then(() => {
        alert("تم نسخ رابط التطبيق بنجاح! يرجى فتح متصفح جوجل كروم ولصق الرابط هناك.");
    }).catch(err => {
        prompt("نسخ الرابط يدوياً:", currentUrl);
    });
}

function onYearChange() {
    const year = document.getElementById("s_year").value;
    const trackContainer = document.getElementById("track_container");
    const courseContainer = document.getElementById("course_container");
    const sectionContainer = document.getElementById("section_container");
    
    document.getElementById("s_track").value = "";
    document.getElementById("s_course").innerHTML = '<option value="">-- اختر المادة الدراسية --</option>';
    document.getElementById("s_section").value = "";
    sectionContainer.style.display = "none";

    if (year === "الفرقة الرابعة") {
        trackContainer.style.display = "block";
        courseContainer.style.display = "none";
    } else if (year) {
        trackContainer.style.display = "none";
        courseContainer.style.display = "block";
        
        let select = document.getElementById("s_course");
        coursesData[year].forEach(course => {
            let opt = document.createElement("option");
            opt.value = course;
            opt.textContent = course;
            select.appendChild(opt);
        });
    } else {
        trackContainer.style.display = "none";
        courseContainer.style.display = "none";
    }
}

function onTrackChange() {
    const track = document.getElementById("s_track").value;
    const courseContainer = document.getElementById("course_container");
    const sectionContainer = document.getElementById("section_container");
    
    let select = document.getElementById("s_course");
    select.innerHTML = '<option value="">-- اختر المادة الدراسية --</option>';
    document.getElementById("s_section").value = "";
    sectionContainer.style.display = "none";

    if (track) {
        courseContainer.style.display = "block";
        let courses = coursesData["الفرقة الرابعة"][track];
        courses.forEach(course => {
            let opt = document.createElement("option");
            opt.value = course;
            opt.textContent = course;
            select.appendChild(opt);
        });
    } else {
        courseContainer.style.display = "none";
    }
}

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

function getAdvancedHardwareFingerprint() {
    try {
        let canvas = document.createElement('canvas');
        let ctx = canvas.getContext('2d');
        ctx.textBaseline = "top";
        ctx.font = "14px Arial";
        ctx.fillStyle = "#f60";
        ctx.fillRect(125, 1, 62, 20);
        ctx.fillStyle = "#069";
        ctx.fillText("BenhaUnivSys2026", 2, 15);
        let canvasData = canvas.toDataURL();

        let glVendor = "";
        let glRenderer = "";
        try {
            let canvasGL = document.createElement('canvas');
            let gl = canvasGL.getContext('webgl') || canvasGL.getContext('experimental-webgl');
            if (gl) {
                let debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    glVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    glRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
            }
        } catch(e) {}

        let components = [
            navigator.hardwareConcurrency || '4',
            navigator.deviceMemory || '4',
            screen.width + 'x' + screen.height,
            screen.colorDepth || '24',
            Intl.DateTimeFormat().resolvedOptions().timeZone || '',
            glVendor,
            glRenderer,
            canvasData.substring(canvasData.length - 40)
        ].join('###');

        let hash = 0;
        for (let i = 0; i < components.length; i++) {
            let char = components.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return 'hw_fp_' + Math.abs(hash).toString(36) + '_' + screen.width + 'x' + screen.height;
    } catch (e) {
        return 'hw_fallback_' + screen.width + 'x' + screen.height;
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

function showMessage(text, color, bgColor) {
    const container = document.getElementById("msg_container");
    const msg = document.getElementById("msg");
    container.style.display = "block";
    container.style.backgroundColor = bgColor;
    container.style.border = "2px solid " + color;
    msg.style.color = color;
    msg.innerHTML = text;
}

function cleanDigits(inputStr) {
    if (!inputStr) return "";
    let cleaned = inputStr.toString().replace(/[\\u200B-\\u200D\\uFEFF]/g, '').trim();
    let arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let persianNumbers = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    for (let i = 0; i < 10; i++) {
        cleaned = cleaned.replace(new RegExp(arabicNumbers[i], 'g'), i).replace(new RegExp(persianNumbers[i], 'g'), i);
    }
    let matches = cleaned.match(/[0-9]/g);
    return matches ? matches.join('') : '';
}

function verifyAndSubmit() {
    const name = document.getElementById("s_name").value.trim();
    const id = document.getElementById("s_id").value.trim();
    const day = document.getElementById("s_day").value;
    const year = document.getElementById("s_year").value;
    const track = document.getElementById("s_track").value;
    const course = document.getElementById("s_course").value;
    const section = document.getElementById("s_section").value;
    const loc = document.getElementById("s_loc").value;
    
    let studentOtp = "";
    if (OTP_ENABLED) {
        studentOtp = cleanDigits(document.getElementById("s_otp").value);
    }

    if (!name || !id || !day || !year || !course || !section || !loc || (OTP_ENABLED && !studentOtp)) {
        showMessage("❌ يرجى استيفاء جميع الحقول المطلوبة بدقة!", "#d9534f", "#f2dede");
        return;
    }

    if (year === "الفرقة الرابعة" && !track) {
        showMessage("❌ يرجى اختيار التوجه الخاص بالفرقة الرابعة!", "#d9534f", "#f2dede");
        return;
    }

    if (id.length !== 14 || isNaN(id)) {
        showMessage("❌ خطأ: يجب أن يكون الرقم القومي مكوناً من 14 رقماً بالضبط!", "#d9534f", "#f2dede");
        return;
    }

    let serverOtpCleaned = cleanDigits(CORRECT_OTP);
    if (OTP_ENABLED && (studentOtp !== serverOtpCleaned)) {
        showMessage("❌ عذراً، رمز التحقق (OTP) الذي أدخلته غير صحيح!", "#d9534f", "#f2dede");
        return;
    }

    const nowCheck = new Date();
    const currentDateStr = nowCheck.getFullYear() + '-' + 
        String(nowCheck.getMonth() + 1).padStart(2, '0') + '-' + 
        String(nowCheck.getDate()).padStart(2, '0');

    if (!navigator.geolocation) {
        showMessage("❌ متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.", "#d9534f", "#f2dede");
        return;
    }

    showMessage("⏳ جاري تحديد موقعك الجغرافي والتحقق من النطاق...", "#0275d8", "#d9edf7");

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

            if (distance <= ALLOWED_RADIUS) {
                showMessage("⏳ تم التحقق من الموقع (داخل النطاق بنجاح)، جاري إرسال وتسجيل الحضور...", "#0275d8", "#d9edf7");

                const now = new Date();
                const formattedTime = now.getFullYear() + '-' + 
                    String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                    String(now.getDate()).padStart(2, '0') + ' ' + 
                    String(now.getHours()).padStart(2, '0') + ':' + 
                    String(now.getMinutes()).padStart(2, '0') + ':' + 
                    String(now.getSeconds()).padStart(2, '0');

                document.getElementById("s_time").value = formattedTime;

                const data = {
                    name: name,
                    id: id,
                    day: day,
                    year: year,
                    track: (year === "الفرقة الرابعة") ? track : "غير مخصص",
                    course: course,
                    section: section,
                    loc: loc,
                    lat: lat,
                    lon: lon,
                    dist: Math.round(distance),
                    time: formattedTime,
                    deviceId: getAdvancedHardwareFingerprint()
                };

                fetch(SCRIPT_URL, {
                    method: "POST",
                    headers: { "Content-Type": "text/plain" },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(result => {
                    if (result.status === "success") {
                        showMessage("✅ تم تسجيل حضورك بنجاح في مادة (" + course + " - " + section + ") ليوم " + day + " وتاريخ " + currentDateStr + "!", "#28a745", "#d4edda");
                    } else {
                        showMessage("❌ " + (result.message || "عذراً، حدث خطأ أثناء التسجيل."), "#d9534f", "#f2dede");
                    }
                })
                .catch((error) => {
                    showMessage("❌ حدث خطأ أثناء الاتصال بالخادم، يرجى المحاولة مرة أخرى.", "#d9534f", "#f2dede");
                });

            } else {
                showMessage("❌ عذراً، أنت خارج النطاق المسموح للقاعة (المسافة الحالية: " + Math.round(distance) + " متر)!", "#d9534f", "#f2dede");
            }
        },
        (error) => {
            showMessage("❌ فشل تحديد الموقع. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.", "#d9534f", "#f2dede");
        },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
    );
}
</script>
""" \
.replace("__LAT__", str(CLASS_LAT)) \
.replace("__LON__", str(CLASS_LON)) \
.replace("__RADIUS__", str(ALLOWED_RADIUS_METERS)) \
.replace("__URL__", GOOGLE_SCRIPT_URL) \
.replace("__SHOW_OTP__", SHOW_OTP_FIELD) \
.replace("__OTP_ENABLED__", "true" if otp_enabled else "false") \
.replace("__CORRECT_OTP__", SERVER_OTP)

components.html(form_html, height=1500)
