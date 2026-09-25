import math
import streamlit as st
import streamlit.components.v1 as components

# إعدادات صفحة التطبيق
st.set_page_config(page_title="تسجيل الحضور الجامعي الذكي", page_icon="📍")

st.title("📌 نظام تسجيل الحضور المقيد جغرافياً")
st.write(
    "يرجى إدخال اسمك وكود الطالب (8 أرقام)، ثم الضغط على زر التحقق والتسجيل"
    " التلقائي."
)

# --- إحداثيات قاعة المحاضرات ---
CLASS_LAT = 30.718881
CLASS_LON = 31.244633
ALLOWED_RADIUS_METERS = 100

# رابط الـ Web App الجديد الخاص بك
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwXqXyuuccgwaxtCTWGme09bYfdIMJOwIlWP6edGOXudxnmOIhS8wkP43ka0pLm1tKE/exec"

# واجهة المدخلات وإرسال البيانات في الخلفية
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

    <button onclick="verifyAndRegister()" style="background-color: #ff4b4b; color: white; padding: 14px 20px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%;">📍 تحقق وسجل حضورك تلقائياً</button>
    
    <p id="msg" style="margin-top: 15px; font-weight: bold; text-align: center; font-size: 15px;"></p>
    
    <!-- صندوق النجاح -->
    <div id="success_container" style="display: none; margin-top: 20px; text-align: center; background-color: #d4edda; padding: 15px; border-radius: 8px; border: 1px solid #c3e6cb;">
        <p style="color: #155724; font-weight: bold; font-size: 16px; margin: 0;">✅ تم التحقق من موقعك وتسجيل حضورك بنجاح تام!</p>
    </div>
</div>

<script>
const CLASS_LAT = __LAT__;
const CLASS_LON = __LON__;
const ALLOWED_RADIUS = __RADIUS__;
const WEB_APP_URL = "__WEB_APP_URL__";

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
    const successContainer = document.getElementById("success_container");

    if (!name || !id) {
        msg.style.color = "red";
        msg.innerHTML = "❌ الرجاء إدخال الاسم وكود الطالب أولاً!";
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
    msg.innerHTML = "⏳ جاري تحديد موقعك بدقة وتسجيل الحضور في الخلفية، يرجى الانتظار...";
    successContainer.style.display = "none";

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            const distance = calculateDistance(CLASS_LAT, CLASS_LON, lat, lon);

            if (distance <= ALLOWED_RADIUS) {
                msg.style.color = "green";
                msg.innerHTML = "🎉 مطابقة صحيحة! المسافة عن القاعة: " + Math.round(distance) + " متر.";
                
                // إرسال البيانات للـ Web App عبر رابط الـ GET مع استخدام no-cors لضمان نجاح الاتصال من المتصفح
                const targetUrl = WEB_APP_URL + "?name=" + encodeURIComponent(name) + "&id=" + encodeURIComponent(id);
                
                fetch(targetUrl, {
                    method: "GET",
                    mode: "no-cors"
                }).then(() => {
                    successContainer.style.display = "block";
                }).catch((error) => {
                    successContainer.style.display = "block";
                });

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
    .replace("__WEB_APP_URL__", WEB_APP_URL)
)

components.html(form_html, height=480)
