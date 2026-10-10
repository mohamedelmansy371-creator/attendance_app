import math
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import json
import requests

st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

hide_header_style = """
    <style>
    [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    </style>
"""
st.markdown(hide_header_style, unsafe_allow_html=True)

if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

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

if st.button("‹", key="toggle_admin_arrow", help=""):
    st.session_state.show_admin = not st.session_state.show_admin

otp_enabled = True
current_otp = "7890"

if st.session_state.show_admin:
    with st.sidebar:
        st.title("🔐 لوحة تحكم المشرف")
        admin_password_input = st.text_input(
            "كلمة مرور المشرف", type="password", placeholder="أدخل كلمة المرور"
        )

        ADMIN_SECRET_PASS = st.secrets.get("ADMIN_PASSWORD", "5994")

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

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwbaqD14H__MwLXFlaIBMFsNWw_A7V3MMulgQtXsS_p-age3plUlHINvTzFNo2L11vP/exec"

query_params = st.query_params

raw_serial = query_params.get("device_serial", "unknown_device")
passed_serial = str(raw_serial).strip() if raw_serial else "unknown_device"

has_valid_serial = "true" if (passed_serial and passed_serial != "None" and passed_serial != "unknown_device") else "false"

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
    "مدرج إقتصاد 2": {"lat": 30.354200, "lon": 31.225200},
    "مدرج محاصيل 1": {"lat": 30.355000, "lon": 31.226000},
    "مدرج محاصيل 2": {"lat": 30.355200, "lon": 31.226200},
    "مدرج محاصيل 3": {"lat": 30.355400, "lon": 31.226400}
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
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">يوم الأسبوع الحالي والتوقيت:</label>
        <input type="text" id="s_day_time" readonly placeholder="جاري التقاط اليوم والوقت..." style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; background-color: #e9ecef; font-weight: bold; color: #0275d8; box-sizing: border-box;">
        <input type="hidden" id="s_day">
        <input type="hidden" id="s_hour">
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
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">اسم المادة الدراسية (المتاحة في توقيتك الحالي):</label>
        <select id="s_course" onchange="onCourseChange()" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر المادة الدراسية --</option>
        </select>
    </div>

    <div id="section_container" style="margin-bottom: 15px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">الشق الدراسي المتاح:</label>
        <select id="s_section" onchange="onSectionChange()" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر الشق الدراسي --</option>
        </select>
    </div>

    <div id="loc_container" style="margin-bottom: 18px; display: none;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">مكان المحاضرة المتاح:</label>
        <select id="s_loc" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: white;">
            <option value="">-- اختر المكان --</option>
        </select>
    </div>

    <div style="margin-bottom: 18px;">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #333; font-size: 16px;">وقت الحضور المسجل:</label>
        <input type="text" id="s_time" readonly placeholder="سيتم التقاط الوقت تلقائياً عند التسجيل" style="width: 100%; padding: 14px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px; background-color: #e9ecef; box-sizing: border-box;">
    </div>

    <div id="otp_box_container" style="margin-bottom: 20px; display: {SHOW_OTP_FIELD};">
        <label style="font-weight: bold; display: block; margin-bottom: 6px; color: #c0392b; font-size: 16px;">🔐 رمز التحقق (OTP) المعلن في القاعة:</label>
        <input type="text" inputmode="numeric" pattern="[0-9]*" id="s_otp" placeholder="أدخل رمز التحقق" style="width: 100%; padding: 14px; border: 2px dashed #e74c3c; border-radius: 8px; font-size: 16px; box-sizing: border-box; background-color: #fff5f5;">
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

const PASSED_DEVICE_SERIAL = "{PASSED_SERIAL}";

// جدول المحاضرات والسكاشن بناءً على التفاصيل المُرسلة تماماً (مع اعتماد مدرج هندسة 3)
const scheduleData = {
    "الفرقة الأولى": {
        "الأحد": [
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "نظري", locs: ["مدرج محاصيل 1"] },
            { startHour: 13, endHour: 15, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 13, endHour: 15, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 2"] },
            { startHour: 9, endHour: 11, course: "جرارات زراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "هندسة البيوت المحمية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هندسة مزارع الإنتاج الحيواني والداجني", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هندسة مزارع الإنتاج الحيواني والداجني", section: "عملي", locs: ["مدرج هندسة 3"] }
        ],
        "الإثنين": [
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "نظري", locs: ["مدرج محاصيل 2", "مدرج هندسة 4"] },
            { startHour: 9, endHour: 11, course: "ميكانيكا (ديناميكا – استاتيكا)", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 13, endHour: 15, course: "ميكانيكا (ديناميكا – استاتيكا)", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 9, endHour: 11, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1"] },
            { startHour: 13, endHour: 15, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 2"] },
            { startHour: 9, endHour: 11, course: "هندسة الري والصرف", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "هندسة البيوت المحمية", section: "عملي", locs: ["مدرج هندسة 1"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] }
        ],
        "الثلاثاء": [
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "نظري", locs: ["مدرج محاصيل 1"] },
            { startHour: 9, endHour: 11, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 3"] },
            { startHour: 9, endHour: 11, course: "رياضة هندسة", section: "نظري", locs: ["مدرج هندسة 1"] },
            { startHour: 13, endHour: 15, course: "رياضة هندسة", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 11, endHour: 13, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1"] },
            { startHour: 13, endHour: 15, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1"] },
            { startHour: 9, endHour: 11, course: "هندسة الري والصرف", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "مصطلحات علمية باللغة الإنجليزية", section: "نظري", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "مصطلحات علمية باللغة الإنجليزية", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 13, endHour: 15, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 4"] }
        ],
        "الأربعاء": [
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "نظري", locs: ["مدرج محاصيل 2", "مدرج هندسة 1"] },
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 13, endHour: 15, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 13, endHour: 15, course: "أساسيات هندسة النظم الزراعية والحيوية", section: "نظري", locs: ["مدرج هندسة 1"] },
            { startHour: 13, endHour: 15, course: "أساسيات هندسة النظم الزراعية والحيوية", section: "عملي", locs: ["مدرج هندسة 1"] },
            { startHour: 9, endHour: 11, course: "رسم هندسي (1)", section: "نظري", locs: ["مدرج هندسة 1"] },
            { startHour: 11, endHour: 13, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 2"] },
            { startHour: 11, endHour: 13, course: "جرارات زراعية", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 13, endHour: 15, course: "جرارات زراعية", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 15, endHour: 17, course: "هندسة البيوت المحمية", section: "عملي", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 13, endHour: 15, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] }
        ],
        "الخميس": [
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2", "مدرج إقتصاد 1"] },
            { startHour: 13, endHour: 15, course: "رياضة عام", section: "عملي", locs: ["مدرج إقتصاد 1"] },
            { startHour: 13, endHour: 15, course: "رياضة هندسة", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 9, endHour: 11, course: "رياضة هندسة", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 13, endHour: 15, course: "رياضة هندسة", section: "عملي", locs: ["مدرج هندسة 1"] },
            { startHour: 11, endHour: 13, course: "ميكانيكا (ديناميكا – استاتيكا)", section: "نظري", locs: ["مدرج هندسة 1"] },
            { startHour: 9, endHour: 11, course: "ميكانيكا (ديناميكا – استاتيكا)", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 13, endHour: 15, course: "ميكانيكا (ديناميكا – استاتيكا)", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 9, endHour: 11, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 1"] },
            { startHour: 13, endHour: 15, course: "رسم هندسي (1)", section: "عملي", locs: ["قاعة تدريس 2"] },
            { startHour: 11, endHour: 13, course: "جرارات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] }
        ],
        "السبت": [
            { startHour: 9, endHour: 11, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 11, endHour: 13, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2"] },
            { startHour: 13, endHour: 15, course: "رياضة عام", section: "عملي", locs: ["مدرج هندسة 2", "مدرج هندسة 3", "مدرج هندسة 4"] }
        ]
    },
    "الفرقة الثانية": {
        "السبت": [
            { startHour: 9, endHour: 11, course: "رياضة تطبيقية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "هيدروليكا وميكانيكا موائع", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هيدروليكا وميكانيكا موائع", section: "عملي", locs: ["مدرج هندسة 1"] },
            { startHour: 13, endHour: 15, course: "نظرية آلات", section: "عملي", locs: ["قاعة تدريس 3"] }
        ],
        "الأحد": [
            { startHour: 9, endHour: 11, course: "رياضة تطبيقية", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 9, endHour: 11, course: "نظرية آلات", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 13, endHour: 15, course: "نظرية آلات", section: "عملي", locs: ["مدرج هندسة 4"] }
        ],
        "الثلاثاء": [
            { startHour: 13, endHour: 15, course: "رياضة تطبيقية", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 9, endHour: 11, course: "هيدروليكا وميكانيكا موائع", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 13, endHour: 15, course: "هيدروليكا وميكانيكا موائع", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "نظرية آلات", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "نظرية آلات", section: "عملي", locs: ["مدرج هندسة 3"] },
            { startHour: 9, endHour: 11, course: "انتقال حراري", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 11, endHour: 13, course: "مقدمة في الحاسب الآلي", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "مقدمة في الحاسب الآلي", section: "عملي", locs: ["مدرج هندسة 3"] }
        ],
        "الأربعاء": [
            { startHour: 9, endHour: 11, course: "انتقال حراري", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "انتقال حراري", section: "عملي", locs: ["مدرج هندسة 4"] }
        ],
        "الخميس": [
            { startHour: 11, endHour: 13, course: "رياضة تطبيقية", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 13, endHour: 15, course: "رياضة تطبيقية", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "هيدروليكا وميكانيكا موائع", section: "عملي", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "انتقال حراري", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 13, endHour: 15, course: "انتقال حراري", section: "عملي", locs: ["مدرج هندسة 3"] }
        ]
    },
    "الفرقة الثالثة": {
        "الأحد": [
            { startHour: 9, endHour: 11, course: "جرارات زراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "هندسة البيوت المحمية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هندسة مزارع الإنتاج الحيواني والداجني", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هندسة مزارع الإنتاج الحيواني والداجني", section: "عملي", locs: ["مدرج هندسة 3"] }
        ],
        "الإثنين": [
            { startHour: 9, endHour: 11, course: "هندسة الري والصرف", section: "نظري", locs: ["مدرج هندسة 3"] },
            { startHour: 13, endHour: 15, course: "هندسة البيوت المحمية", section: "عملي", locs: ["مدرج هندسة 1"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] }
        ],
        "الثلاثاء": [
            { startHour: 9, endHour: 11, course: "هندسة الري والصرف", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "مصطلحات علمية باللغة الإنجليزية", section: "نظري", locs: ["مدرج هندسة 4"] },
            { startHour: 11, endHour: 13, course: "مصطلحات علمية باللغة الإنجليزية", section: "عملي", locs: ["مدرج هندسة 4"] },
            { startHour: 13, endHour: 15, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 4"] }
        ],
        "الأربعاء": [
            { startHour: 11, endHour: 13, course: "جرارات زراعية", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 13, endHour: 15, course: "جرارات زراعية", section: "عملي", locs: ["قاعة تدريس 4"] },
            { startHour: 15, endHour: 17, course: "هندسة البيوت المحمية", section: "عملي", locs: ["مدرج هندسة 3"] },
            { startHour: 11, endHour: 13, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] },
            { startHour: 13, endHour: 15, course: "تخطيط وتصميم المنشآت الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] }
        ],
        "الخميس": [
            { startHour: 11, endHour: 13, course: "جرارات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] }
        ]
    },
    "الفرقة الرابعة": {
        "توجه آلات": {
            "السبت": [
                { startHour: 9, endHour: 11, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "نظرية اهتزازات وتوازن", section: "عملي", locs: ["قاعة تدريس 4"] },
                { startHour: 11, endHour: 13, course: "ميكانيكا تربة", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "معدات التسميد والمكافحة", section: "عملي", locs: ["قاعة تدريس 4"] }
            ],
            "الأحد": [
                { startHour: 11, endHour: 13, course: "تصميم نظم الري", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "نظري", locs: ["مدرج هندسة 4"] }
            ],
            "الإثنين": [
                { startHour: 11, endHour: 13, course: "التحكم البيئي في المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "ميكانيكا تربة", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 9, endHour: 11, course: "معدات التسميد والمكافحة", section: "نظري", locs: ["مدرج هندسة 4"] }
            ],
            "الثلاثاء": [
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "عملي", locs: ["مدرج هندسة 4"] }
            ],
            "الأربعاء": [
                { startHour: 13, endHour: 15, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 11, endHour: 13, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "نظرية اهتزازات وتوازن", section: "نظري", locs: ["قاعة تدريس 3"] },
                { startHour: 13, endHour: 15, course: "معدات التسميد والمكافحة", section: "عملي", locs: ["قاعة تدريس 2", "قاعة تدريس 5"] }
            ]
        },
        "توجه ري": {
            "السبت": [
                { startHour: 9, endHour: 11, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "ميكانيكا تربة", section: "نظري", locs: ["مدرج هندسة 4"] }
            ],
            "الأحد": [
                { startHour: 11, endHour: 13, course: "تصميم نظم الري", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "نظري", locs: ["مدرج هندسة 4"] }
            ],
            "الإثنين": [
                { startHour: 11, endHour: 13, course: "التحكم البيئي في المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "ميكانيكا تربة", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 9, endHour: 11, course: "هيدروليكا الآبار والمضخات", section: "عملي", locs: ["قاعة تدريس 3"] }
            ],
            "الثلاثاء": [
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["قاعة تدريس 2", "قاعة تدريس 5"] },
                { startHour: 13, endHour: 15, course: "هيدروليكا الآبار والمضخات", section: "نظري", locs: ["قاعة تدريس 4", "قاعة تدريس 5"] },
                { startHour: 11, endHour: 13, course: "هيدروليكا الآبار والمضخات", section: "عملي", locs: ["قاعة تدريس 3", "قاعة تدريس 4", "قاعة تدريس 5"] },
                { startHour: 13, endHour: 15, course: "هيدروليكا الآبار والمضخات", section: "عملي", locs: ["قاعة تدريس 4", "قاعة تدريس 5"] }
            ],
            "الأربعاء": [
                { startHour: 13, endHour: 15, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 11, endHour: 13, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 5"] }
            ]
        },
        "توجه نظم": {
            "السبت": [
                { startHour: 9, endHour: 11, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "الخواص الطبيعية والهندسية للمنتجات الزراعية", section: "نظري", locs: ["قاعة تدريس 3"] },
                { startHour: 11, endHour: 13, course: "الخواص الطبيعية والهندسية للمنتجات الزراعية", section: "عملي", locs: ["قاعة تدريس 3"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 5"] }
            ],
            "الأحد": [
                { startHour: 11, endHour: 13, course: "تصميم نظم الري", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "عملي", locs: ["مدرج هندسة 3"] }
            ],
            "الإثنين": [
                { startHour: 11, endHour: 13, course: "التحكم البيئي في المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "إدارة وتشغيل المزارع المائية", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 9, endHour: 11, course: "الخواص الطبيعية والهندسية للمنتجات الزراعية", section: "عملي", locs: ["قاعة تدريس 2", "قاعة تدريس 5"] }
            ],
            "الثلاثاء": [
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "عملي", locs: ["مدرج هندسة 4"] }
            ],
            "الأربعاء": [
                { startHour: 13, endHour: 15, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 11, endHour: 13, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "إدارة وتشغيل المزارع المائية", section: "عملي", locs: ["قاعة تدريس 4"] }
            ]
        },
        "توجه عام": {
            "السبت": [
                { startHour: 9, endHour: 11, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "معدات التسميد والمكافحة", section: "عملي", locs: ["قاعة تدريس 4"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 5"] }
            ],
            "الأحد": [
                { startHour: 11, endHour: 13, course: "تصميم نظم الري", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 1"] },
                { startHour: 9, endHour: 11, course: "تصميم آلات زراعية", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "هندسة تصنيع السماد العضوي المكمور", section: "عملي", locs: ["مدرج هندسة 3"] }
            ],
            "الإثنين": [
                { startHour: 11, endHour: 13, course: "التحكم البيئي في المنشآت الزراعية", section: "نظري", locs: ["مدرج هندسة 3"] },
                { startHour: 13, endHour: 15, course: "تصميم نظم الري", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "معدات التسميد والمكافحة", section: "نظري", locs: ["مدرج هندسة 4"] }
            ],
            "الثلاثاء": [
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 11, endHour: 13, course: "أساليب البحث العلمي", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["قاعة تدريس 2", "قاعة تدريس 5"] }
            ],
            "الأربعاء": [
                { startHour: 13, endHour: 15, course: "التحكم البيئي في المنشآت الزراعية", section: "عملي", locs: ["مدرج هندسة 3"] },
                { startHour: 11, endHour: 13, course: "تصميم آلات زراعية", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "معدات التسميد والمكافحة", section: "عملي", locs: ["قاعة تدريس 2", "قاعة تدريس 5"] },
                { startHour: 9, endHour: 11, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "نظري", locs: ["مدرج هندسة 4"] },
                { startHour: 9, endHour: 11, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["مدرج هندسة 4"] },
                { startHour: 13, endHour: 15, course: "تخطيط وتصميم نظم الصرف الحقلي", section: "عملي", locs: ["قاعة تدريس 1", "قاعة تدريس 5"] }
            ]
        }
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
    const dayName = daysMap[todayIndex];

    document.getElementById("s_day").value = dayName;
    document.getElementById("s_hour").value = currentHour;
    
    const timeStr = (currentHour <= 12 ? currentHour : currentHour - 12) + ":00 " + (currentHour < 12 ? "صباحاً" : "مساءً");
    document.getElementById("s_day_time").value = dayName + " - الساعة: " + timeStr;
});

function getActiveScheduleItems() {
    const year = document.getElementById("s_year").value;
    const track = document.getElementById("s_track").value;
    const day = document.getElementById("s_day").value;
    const currentHour = parseInt(document.getElementById("s_hour").value) || new Date().getHours();

    if (!year || !day) return [];

    let items = [];
    if (year === "الفرقة الرابعة") {
        if (!track) return [];
        if (scheduleData[year] && scheduleData[year][track] && scheduleData[year][track][day]) {
            items = scheduleData[year][track][day];
        }
    } else {
        if (scheduleData[year] && scheduleData[year][day]) {
            items = scheduleData[year][day];
        }
    }

    return items.filter(item => currentHour >= item.startHour && currentHour < item.endHour);
}

function onYearChange() {
    const year = document.getElementById("s_year").value;
    const trackContainer = document.getElementById("track_container");
    
    document.getElementById("s_track").value = "";
    resetDependentDropdowns();

    if (year === "الفرقة الرابعة") {
        trackContainer.style.display = "block";
    } else {
        trackContainer.style.display = "none";
        populateCourses();
    }
}

function onTrackChange() {
    resetDependentDropdowns();
    populateCourses();
}

function resetDependentDropdowns() {
    document.getElementById("s_course").innerHTML = '<option value="">-- اختر المادة الدراسية --</option>';
    document.getElementById("course_container").style.display = "none";

    document.getElementById("s_section").innerHTML = '<option value="">-- اختر الشق الدراسي --</option>';
    document.getElementById("section_container").style.display = "none";

    document.getElementById("s_loc").innerHTML = '<option value="">-- اختر المكان --</option>';
    document.getElementById("loc_container").style.display = "none";
}

function populateCourses() {
    const courseContainer = document.getElementById("course_container");
    const activeItems = getActiveScheduleItems();

    let select = document.getElementById("s_course");
    select.innerHTML = '<option value="">-- اختر المادة الدراسية --</option>';

    if (activeItems.length > 0) {
        courseContainer.style.display = "block";
        let uniqueCourses = [...new Set(activeItems.map(i => i.course))];
        uniqueCourses.forEach(course => {
            let opt = document.createElement("option");
            opt.value = course;
            opt.textContent = course;
            select.appendChild(opt);
        });
    } else {
        courseContainer.style.display = "none";
        showMessage("ℹ️ عذراً، ليس لديك أي محاضرات أو سكاشن متاحة في هذا التوقيت اليوم.", "#856404", "#fff3cd");
    }
}

function onCourseChange() {
    const course = document.getElementById("s_course").value;
    const sectionContainer = document.getElementById("section_container");
    const activeItems = getActiveScheduleItems();

    let select = document.getElementById("s_section");
    select.innerHTML = '<option value="">-- اختر الشق الدراسي --</option>';
    document.getElementById("s_loc").innerHTML = '<option value="">-- اختر المكان --</option>';
    document.getElementById("loc_container").style.display = "none";

    if (course) {
        sectionContainer.style.display = "block";
        let matchingSections = activeItems.filter(i => i.course === course);
        let uniqueSections = [...new Set(matchingSections.map(i => i.section))];
        
        uniqueSections.forEach(sec => {
            let opt = document.createElement("option");
            opt.value = sec;
            opt.textContent = sec;
            select.appendChild(opt);
        });
    } else {
        sectionContainer.style.display = "none";
    }
}

function onSectionChange() {
    const course = document.getElementById("s_course").value;
    const section = document.getElementById("s_section").value;
    const locContainer = document.getElementById("loc_container");
    const activeItems = getActiveScheduleItems();

    let select = document.getElementById("s_loc");
    select.innerHTML = '<option value="">-- اختر المكان --</option>';

    if (section) {
        locContainer.style.display = "block";
        let matchingItem = activeItems.find(i => i.course === course && i.section === section);
        if (matchingItem && matchingItem.locs) {
            matchingItem.locs.forEach(loc => {
                let opt = document.createElement("option");
                opt.value = loc;
                opt.textContent = loc;
                select.appendChild(opt);
            });
        }
    } else {
        locContainer.style.display = "none";
    }
}

function getAdvancedHardwareFingerprint() {
    try {
        let androidIdStr = (PASSED_DEVICE_SERIAL && PASSED_DEVICE_SERIAL.trim() !== "" && PASSED_DEVICE_SERIAL !== "None") 
                            ? PASSED_DEVICE_SERIAL.trim() 
                            : "unknown_device";
        
        let screenWidth = window.screen.width || 0;
        let screenHeight = window.screen.height || 0;
        let pixelRatio = window.devicePixelRatio || 1;
        let userAgent = navigator.userAgent || "unknown_agent";
        
        let osInfo = "Other";
        if (/android/i.test(userAgent)) {
            osInfo = "Android";
        } else if (/iphone|ipad|ipod/i.test(userAgent)) {
            osInfo = "iOS";
        }

        let dynamicSpecs = osInfo + "_" + screenWidth + "x" + screenHeight + "_px" + pixelRatio;
        return dynamicSpecs + " | AndroidID: " + androidIdStr;
    } catch (e) {
        let androidIdStr = (PASSED_DEVICE_SERIAL && PASSED_DEVICE_SERIAL.trim() !== "") ? PASSED_DEVICE_SERIAL.trim() : "unknown_device";
        return "Device_Fallback | AndroidID: " + androidIdStr;
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
            showMessage("🚨 تنبيه أمني: تم رصد محاولة تسجيل غير قانونية، تم رفض التسجيل!", "#d9534f", "#f2dede");
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
                    showMessage("❌ " + (result.message || "عذراً، حدث خطأ أثناء التسجيل، قد تكون سجلت حضورك ولكن حدث خطأ بسبب ضعف الانترنت لديك، فحاول مجددا واذا ظهرت لك رسالة تفيد بأنك سجلت المادة مسبقا اليوم فاعلم انه تم تسجيل حضورك فلا تقلق."), "#d9534f", "#f2dede");
                }
            })
            .catch((error) => {
                showMessage("❌ حدث خطأ أثناء الاتصال بالخادم، قد تكون سجلت حضورك ولكن حدث خطأ بسبب ضعف الانترنت لديك، فحاول مجددا واذا ظهرت لك رسالة تفيد بأنك سجلت المادة مسبقا اليوم فاعلم انه تم تسجيل حضورك فلا تقلق.", "#d9534f", "#f2dede");
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
    .replace("{PASSED_SERIAL}", str(passed_serial))
)

components.html(form_html, height=1500)
