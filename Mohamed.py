import math
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import json
import requests

st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

# كود CSS لإخفاء عناصر Streamlit العلوية وأيضاً إخفاء زر الـ Sidebar الافتراضي تماماً لنستبدله بسهمنا الخاص
hide_header_style = """
    <style>
    [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    /* إخفاء زر القائمة الجانبية الافتراضي لنتحكم به نحن */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
"""
st.markdown(hide_header_style, unsafe_allow_html=True)

# إدارة حالة إظهار/إخفاء لوحة تحكم المشرف عبر الـ Session State
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

# سهم صغير جداً في أقصى يسار الشاشة (مخفي تماماً ولا يظهر عليه أي كلام، مجرد سهم دقيق)
st.markdown("""
    <style>
    .admin-toggle-btn {
        position: fixed;
        top: 10px;
        left: 5px;
        z-index: 999999;
        background: transparent;
        border: none;
        color: #888;
        font-size: 14px;
        cursor: pointer;
        padding: 2px 5px;
    }
    .admin-toggle-btn:hover {
        color: #000;
    }
    </style>
""", unsafe_allow_html=True)

# زر سهم دقيق وصغير جداً في أقصى اليسار
if st.button("‹", key="toggle_admin_arrow", help=""):
    st.session_state.show_admin = not st.session_state.show_admin

# إذا قام المشرف بالضغط على السهم، تظهر لوحة التحكم في الشريط الجانبي (Sidebar)
otp_enabled = True
current_otp = "7890"

if st.session_state.show_admin:
    with st.sidebar:
        st.title("🔐 لوحة تحكم المشرف")
        admin_password_input = st.text_input(
            "كلمة مرور المشرف", type="password", placeholder="أدخل كلمة المرور"
        )

        ADMIN_SECRET_PASS = "5994"

        if admin_password_input == ADMIN_SECRET_PASS:
            st.success("تم تسجيل الدخول بنجاح كمشرف ✅")
            st.markdown("---")
            st.subheader("إدارة رمز التحقق (OTP)")
            use_otp = st.checkbox("تفعيل نظام رمز التحقق (OTP)", value=True)
            if use_otp:
                otp_enabled = True
                current_otp = st.text_input(
                    "الرمز الحالي للمحاضرة",
                    value="7890",
                    help="اكتب الرمز الذي ستعطيه للطلاب في المدرج",
                )
            else:
                otp_enabled = False
                current_otp = ""
        else:
            if admin_password_input != "":
                st.error("كلمة المرور غير صحيحة")
            otp_enabled = True
            current_otp = "7890"

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby1Ex3JjMWYrflTX73bPpmKpKZCCNZ6_l95aQOi8uyHnd0FQQ1pZAqYye0eDEqpvLRf/exec"

query_params = st.query_params
device_serial = query_params.get("device_serial", None)

has_valid_serial = "true" if (device_serial and str(device_serial).strip() != "") else "false"

st.title("نظام تسجيل الحضور الذكي")

APP_OPEN_HOUR = 0          
APP_CLOSE_HOUR = 23   

LOCATIONS_COORDS = {
    "مدرج هندسة 1": {"lat": 30.719101, "lon": 31.244522},
    "مدرج هندسة 2": {"lat": 30.353500, "lon": 31.224400},
    "مدرج هندسة 3": {"lat": 30.353500, "lon": 31.224600},
    "مدرج هندسة 4": {"lat": 30.353700, "lon": 31.224800},
    "قاعة تدريس 1": {"lat": 30.352800, "lon": 31.223900},
    "قاعة تدريس 2": {"lat": 30.352950, "lon": 31.224050},
    "قاعة تدريس 3": {"lat": 30.353100, "lon": 31.224200},
    "قاعة تدريس 4": {"lat": 30.353250, "lon": 31.224350},
    "قاعة تدريس 5": {"lat": 30.353400, "lon": 31.224500},
    "مدرج إقتصاد 1": {"lat": 30.354000, "lon": 31.225000},
    "مدرج إقتصاد 2": {"lat": 30.354200, "lon": 31.225200}
}

ALLOWED_RADIUS_METERS = 500
SHOW_OTP_FIELD = "block" if otp_enabled else "none"
SERVER_OTP = str(current_otp).strip()
locations_json = json.dumps(LOCATIONS_COORDS, ensure_ascii=False)

open_hour_12 = APP_OPEN_HOUR if APP_OPEN_HOUR <= 12 else APP_OPEN_HOUR - 12
open_period = "صباحاً" if APP_OPEN_HOUR < 12 else "مساءً"

close_hour_12 = APP_CLOSE_HOUR if APP_CLOSE_HOUR <= 12 else APP_CLOSE_HOUR - 12
close_period = "صباحاً" if APP_CLOSE_HOUR < 12 else "مساءً"

form_html = """
<div id="app_block_container" style="display: none; font-family: Tahoma, sans-serif; padding: 35px; direction: rtl; background-color: #f8d7da; border-radius: 12px; border: 2px solid #f5c6cb; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px;">
    <h2 style="color: #721c24; margin-bottom: 15px;">🚫 تنبيه أمني - ممنوع الدخول المباشر</h2>
    <p style="font-size: 18px; color: #721c24; line-height: 1.6; font-weight: bold;">
        عذراً، لا يمكن تسجيل الحضور من خلال متصفح الإنترنت بشكل مباشر.
    </p>
    <p style="font-size: 16px; color: #555; line-height: 1.6; margin-bottom: 20px;">
        يجب عليك فتح التطبيق الرسمي الخاص بالحضور من على هاتفك المحمول.
    </p>
</div>

<div id="time_warning_container" style="display: none; font-family: Tahoma, sans-serif; padding: 30px; direction: rtl; background-color: #fff3cd; border-radius: 12px; border: 2px solid #ffeeba; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); margin-top: 20px;">
    <h2 style="color: #856404; margin-bottom: 15px;">⏳ التطبيق مغلق حالياً</h2>
    <p style="font-size: 18px; color: #856404; line-height: 1.6; font-weight: bold;">
        عذراً، أوقات تسجيل الحضور الرسمية هي من الساعة <b>{OPEN_H}:00 {OPEN_P}</b> وحتى الساعة <b>{CLOSE_H}:00 {CLOSE_P}</b>.
    </p>
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
            <option value="مدرج إقتصاد 1">مدرج إقتصاد 1</option>
            <option value="مدرج إقتصاد 2">مدرج إقتصاد 2</option>
        </select>
    </div>

    <div style="margin-bottom: 18px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">وقت الحضور المسجل:</label>
        <input type="text" id="s_time" readonly placeholder="سيتم التقاط الوقت تلقائياً عند التسجيل" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; background-color: #e9ecef; box-sizing: border-box;">
    </div>

    <div id="otp_box_container" style="margin-bottom: 20px; display: {SHOW_OTP_FIELD};">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #c0392b; font-size: 16px;">🔐 رمز التحقق (OTP) المعلن في القاعة:</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" id="s_otp" placeholder="أدخل الرمز التحقق" style="width: 100%; padding: 14px; border: 2px dashed #e74c3c; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: #fff5f5;">
    </div>

    <button onclick="verifyAndSubmit()" style="background-color: #28a745; color: white; padding: 16px 20px; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; width: 100%; box-shadow: 0 6px 12px rgba(0,0,0,0.15);">📍 تحقق من الموقع وتسجيل الحضور</button>
    
    <div id="msg_container" style="margin-top: 25px; padding: 20px; border-radius: 10px; text-align: center; display: none; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        <p id="msg" style="margin: 0; font-weight: bold; font-size: 17px; line-height: 1.6;"></p>
    </div>
</div>

<script>
const LOCATIONS_COORDS = {LOCATIONS_JSON};
const ALLOWED_RADIUS = {ALLOWED_RADIUS_METERS};
const SCRIPT_URL = "{GOOGLE_SCRIPT_URL}";
const OTP_ENABLED = {OTP_ENABLED_JS};
const CORRECT_OTP = "{SERVER_OTP}";
const APP_OPEN_HOUR = {APP_OPEN_HOUR};
const APP_CLOSE_HOUR = {APP_CLOSE_HOUR};
const HAS_VALID_SERIAL = {HAS_VALID_SERIAL_JS};

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
    const blockContainer = document.getElementById("app_block_container");
    const timeWarningBox = document.getElementById("time_warning_container");
    const mainApp = document.getElementById("main_app_container");

    if (!HAS_VALID_SERIAL) {
        if (blockContainer) blockContainer.style.display = "block";
        if (timeWarningBox) timeWarningBox.style.display = "none";
        if (mainApp) mainApp.style.display = "none";
        return;
    }

    const now = new Date();
    const currentHour = now.getHours();

    if (currentHour < APP_OPEN_HOUR || currentHour >= APP_CLOSE_HOUR) {
        if (blockContainer) blockContainer.style.display = "none";
        if (timeWarningBox) timeWarningBox.style.display = "block";
        if (mainApp) mainApp.style.display = "none";
        return;
    }

    if (blockContainer) blockContainer.style.display = "none";
    if (timeWarningBox) timeWarningBox.style.display = "none";
    if (mainApp) mainApp.style.display = "block";
    
    const daysMap = ["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"];
    const todayIndex = now.getDay();
    const dayInput = document.getElementById("s_day");
    if(dayInput) dayInput.value = daysMap[todayIndex];
});

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
        const urlParams = new URLSearchParams(window.location.search);
        let androidId = urlParams.get("device_serial");
        let androidIdStr = (androidId && androidId.trim() !== "") ? androidId.trim() : "0ea6954ce0b7abf8";
        
        return "hw_v2_qolzcn_384x857 | AndroidID: " + androidIdStr;
    } catch (e) {
        return "hw_v2_qolzcn_384x857 | AndroidID: 0ea6954ce0b7abf8";
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
    let cleaned = inputStr.toString().replace(/[\u200B-\u200D\uFEFF]/g, '').trim();
    let arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let persianNumbers = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    for (let i = 0; i < 10; i++) {
        cleaned = cleaned.replace(new RegExp(arabicNumbers[i], 'g'), i).replace(new RegExp(persianNumbers[i], 'g'), i);
    }
    let matches = cleaned.match(/[0-9]/g);
    return matches ? matches.join('') : '';
}

function getSinglePosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject("متصفح هاتفك لا يدعم تحديد الموقع الجغرافي.");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            (position) => resolve(position),
            (error) => reject(error),
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
        );
    });
}

async function verifyAndSubmit() {
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

    if (!LOCATIONS_COORDS[loc]) {
        showMessage("❌ يرجى اختيار مكان محاضرة صحيح من القائمة!", "#d9534f", "#f2dede");
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

    showMessage("⏳ جاري تحديد موقعك الجغرافي...", "#0275d8", "#d9edf7");

    try {
        let samples = [];

        for (let i = 0; i < 3; i++) {
            try {
                let pos = await getSinglePosition();
                samples.push({
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude,
                    alt: pos.coords.altitude,
                    acc: pos.coords.accuracy
                });
                if (i < 2) {
                    await new Promise(r => setTimeout(r, 3000));
                }
            } catch (e) {}
        }

        if (samples.length < 2) {
            throw new Error("يرجى التأكد من تفعيل موقعك الجغرافي");
        }

        let lowAccuracyFound = false;
        samples.forEach(s => {
            if (s.acc !== null && s.acc !== undefined && s.acc < 5) {
                lowAccuracyFound = true;
            }
        });

        if (lowAccuracyFound) {
            showMessage("🚨 تنبيه أمني: تم رصد دقة غير منطقية لإشارة الـ GPS، تم رفض التسجيل!", "#d9534f", "#f2dede");
            return;
        }

        let isFakeStatic = true;
        for (let i = 1; i < samples.length; i++) {
            if (samples[i].lat !== samples[0].lat || samples[i].lon !== samples[0].lon) {
                isFakeStatic = false;
                break;
            }
        }

        if (isFakeStatic) {
            showMessage("🚨 تنبيه أمني: تم رصد محاولة تسجيل غير قانونية، تم حظر محاولة التسجيل!", "#d9534f", "#f2dede");
            return;
        }

        let bestSample = samples.reduce((prev, curr) => (curr.acc < prev.acc) ? curr : prev);
        const lat = bestSample.lat;
        const lon = bestSample.lon;
        
        const targetLocCoords = LOCATIONS_COORDS[loc];
        const distance = calculateDistance(targetLocCoords.lat, targetLocCoords.lon, lat, lon);

        if (distance <= ALLOWED_RADIUS) {
            showMessage("⏳ تم اجتياز الفحوصات الأمنية بدقة، جاري تسجيل حضورك...", "#0275d8", "#d9edf7");

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
                    showMessage("✅ تم تسجيل حضورك بنجاح في مادة (" + course + " - " + section + ") في (" + loc + ") ليوم " + day + "!", "#28a745", "#d4edda");
                } else {
                    showMessage("❌ " + (result.message || "عذراً، حدث خطأ أثناء التسجيل."), "#d9534f", "#f2dede");
                }
            })
            .catch((error) => {
                showMessage("❌ حدث خطأ أثناء الاتصال بالخادم، يرجى المحاولة مرة أخرى.", "#d9534f", "#f2dede");
            });

        } else {
            showMessage("❌ عذراً، أنت خارج النطاق المسموح لـ (" + loc + ") (المسافة الحالية: " + Math.round(distance) + " متر)!", "#d9534f", "#f2dede");
        }

    } catch (error) {
        showMessage("❌ فشل تحديد الموقع بدقة. تأكد من تفعيل الـ GPS والسماح للمتصفح بالوصول لموقعك.", "#d9534f", "#f2dede");
    }
}
</script>
"""

form_html = (
    form_html.replace("{OPEN_H}", str(open_hour_12))
    .replace("{OPEN_P}", str(open_period))
    .replace("{CLOSE_H}", str(close_hour_12))
    .replace("{CLOSE_P}", str(close_period))
    .replace("{SHOW_OTP_FIELD}", str(SHOW_OTP_FIELD))
    .replace("{LOCATIONS_JSON}", str(locations_json))
    .replace("{ALLOWED_RADIUS_METERS}", str(ALLOWED_RADIUS_METERS))
    .replace("{GOOGLE_SCRIPT_URL}", str(GOOGLE_SCRIPT_URL))
    .replace("{OTP_ENABLED_JS}", "true" if otp_enabled else "false")
    .replace("{SERVER_OTP}", str(SERVER_OTP))
    .replace("{APP_OPEN_HOUR}", str(APP_OPEN_HOUR))
    .replace("{APP_CLOSE_HOUR}", str(APP_CLOSE_HOUR))
    .replace("{HAS_VALID_SERIAL_JS}", has_valid_serial)
)

components.html(form_html, height=1500)
