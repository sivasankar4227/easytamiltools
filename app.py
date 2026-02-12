from flask import Flask, render_template, request, Response, send_from_directory
from datetime import date
from PIL import Image
import os
from num2words import num2words
import qrcode
from werkzeug.utils import secure_filename
import logging



app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "uploads"



ALLOWED_EXTENSIONS = {"png","jpg","jpeg","webp"}
os.makedirs("uploads", exist_ok=True)

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR
)

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS


# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= SITEMAP =================
from flask import url_for
from datetime import datetime

@app.route("/sitemap.xml")
def sitemap():
    pages = []

    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            if not rule.rule.startswith("/static"):
                pages.append(url_for(rule.endpoint, _external=True))

    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

    for page in pages:
        sitemap_xml += f"""
    <url>
        <loc>{page}</loc>
        <lastmod>{datetime.now().date()}</lastmod>
        <priority>0.8</priority>
    </url>"""

    sitemap_xml += "\n</urlset>"

    return Response(sitemap_xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")

# ================= LETTERS =================
@app.route("/letters")
def letters():
    return render_template("letters.html")

@app.route("/letters/school-leave")
def school_leave():
    return render_template("school_leave_letter.html")

# @app.route("/letters/sick-leave")
# def sick_leave():
#     return render_template("sick_leave_letter.html")


@app.route("/letters/office-leave")
def office_leave():
    return render_template("office_leave_letter.html")


@app.route("/letters/bank-close")
def bank_close():
    return render_template("bank_close_letter.html")


# @app.route("/letters/aadhaar-correction")
# def aadhaar_correction():
#     return render_template("aadhaar_correction_letter.html")


# ================= CALCULATORS =================
@app.route("/calculators")
def calculators():
    return render_template("calculators.html")

@app.route("/age-calculator", methods=["GET","POST"])
def age_calculator():
    age=None
    if request.method=="POST":
        y,m,d=map(int,request.form["dob"].split("-"))
        birth=date(y,m,d)
        today=date.today()
        years=today.year-birth.year
        months=today.month-birth.month
        days=today.day-birth.day
        if days<0:
            months-=1
            days+=30
        if months<0:
            years-=1
            months+=12
        age={"years":years,"months":months,"days":days}
    return render_template("age_calculator.html",age=age)

@app.route("/emi-calculator", methods=["GET","POST"])
def emi_calculator():

    emi=None
    interest=None
    total=None
    principal=None

    if request.method=="POST":
        principal=float(request.form["principal"])
        rate=float(request.form["rate"])/12/100
        years=int(request.form["years"])
        months=years*12

        emi=round(principal*rate*(1+rate)**months/((1+rate)**months-1),2)
        total=round(emi*months,2)
        interest=round(total-principal,2)

    return render_template(
        "emi_calculator.html",
        emi=emi,
        interest=interest,
        total=total,
        principal=principal
    )

# ================= BMI CALCULATOR =================
@app.route("/bmi-calculator", methods=["GET","POST"])
def bmi_calculator():
    bmi = None
    category = ""

    if request.method == "POST":
        weight = float(request.form["weight"])
        height = float(request.form["height"]) / 100  # cm to meter
        bmi = round(weight / (height * height), 2)

        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"

    return render_template("bmi_calculator.html", bmi=bmi, category=category)


# ================= PERCENTAGE CALCULATOR =================
@app.route("/percentage-calculator", methods=["GET","POST"])
def percentage_calculator():
    result = None

    if request.method == "POST":
        value = float(request.form["value"])
        total = float(request.form["total"])

        if total == 0:
            result = "error"
        else:
            result = round((value / total) * 100, 2)

    return render_template("percentage_calculator.html", result=result)


# ================= TOOLS =================
@app.route("/tools")
def tools():
    return render_template("tools.html")

# ================= text-counter =================

@app.route("/text-counter", methods=["GET","POST"])
def text_counter():

    text = ""
    word_count = 0
    char_count = 0
    char_no_space = 0
    line_count = 0

    if request.method == "POST":
        text = request.form.get("text","")

        word_count = len(text.split())
        char_count = len(text)
        char_no_space = len(text.replace(" ", ""))
        line_count = len(text.splitlines())

    return render_template(
        "text_counter.html",
        text=text,
        word_count=word_count,
        char_count=char_count,
        char_no_space=char_no_space,
        line_count=line_count
    )

# ================= date-difference =================

@app.route("/date-difference", methods=["GET","POST"])
def date_difference():

    diff = None
    date1 = ""
    date2 = ""

    if request.method == "POST":
        date1 = request.form.get("date1")
        date2 = request.form.get("date2")

        if date1 and date2:
            d1 = date.fromisoformat(date1)
            d2 = date.fromisoformat(date2)
            diff = abs((d2 - d1).days)

    return render_template(
        "date_difference.html",
        diff=diff,
        date1=date1,
        date2=date2
    )

# ================= case-converter =================

@app.route("/case-converter", methods=["GET","POST"])
def case_converter():

    text = ""
    result = ""
    action = "upper"

    if request.method == "POST":
        text = request.form.get("text","")
        action = request.form.get("action")

        if action == "upper":
            result = text.upper()
        elif action == "lower":
            result = text.lower()
        else:
            result = text.title()

    return render_template(
        "case_converter.html",
        text=text,
        result=result,
        action=action
    )
# ================= number-to-words =================
@app.route("/number-to-words", methods=["GET","POST"])
def number_to_words():

    result = None
    number = ""
    lang = "en"

    if request.method == "POST":
        number = request.form["number"]
        lang = request.form["lang"]

        try:
            result = num2words(int(number), lang=lang).title()
        except:
            result = "coming soon"

    return render_template(
        "number_to_words.html",
        result=result,
        number=number,
        lang=lang
    )
# ================= unit-converter =================

@app.route("/unit-converter", methods=["GET","POST"])
def unit_converter():

    result = None
    value = ""
    unit = ""

    if request.method == "POST":
        value = float(request.form["value"])
        unit = request.form["unit"]

        if unit == "cm_to_m":
            result = value / 100

        elif unit == "m_to_cm":
            result = value * 100

        elif unit == "m_to_ft":
            result = value * 3.28084

        elif unit == "ft_to_m":
            result = value / 3.28084

        elif unit == "km_to_mile":
            result = value * 0.621371

        elif unit == "mile_to_km":
            result = value / 0.621371

        elif unit == "inch_to_cm":
            result = value * 2.54

        elif unit == "cm_to_inch":
            result = value / 2.54

        elif unit == "kg_to_g":
            result = value * 1000

        elif unit == "g_to_kg":
            result = value / 1000

        elif unit == "pound_to_kg":
            result = value * 0.453592

        elif unit == "kg_to_pound":
            result = value * 2.20462

        elif unit == "c_to_f":
            result = (value * 9/5) + 32

        elif unit == "f_to_c":
            result = (value - 32) * 5/9

        result = round(result, 4)

    return render_template(
        "unit_converter.html",
        result=result,
        value=value,
        unit=unit
    )


# ================= QR CODE GENERATOR =================

@app.route("/qr-code-generator", methods=["GET","POST"])
def qr_code_generator():

    qr_image = None
    data = ""

    if request.method == "POST":
        data = request.form.get("data")

        if data:
            img = qrcode.make(data)

            save_path = "static/qr_code.png"
            img.save(save_path)

            qr_image = save_path

    return render_template(
        "qr_code_generator.html",
        qr_image=qr_image,
        data=data,
        title="QR Code Generator - Easy Tamil Tools",
        description="Free Online QR Code Generator. Create QR codes for text, URL, phone number and download instantly.",
        keywords="qr code generator online, free qr generator, tamil qr tool"
    )


# ================= LEGAL PAGES =================

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        print(name, email, message)   # Later save to DB or email
    return render_template(
        "contact.html",
        title="Contact Us - Easy Tamil Tools",
        description="Contact Easy Tamil Tools for queries, suggestions and support.",
        keywords="contact easy tamil tools"
    )


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        feedback_text = request.form.get("feedback")
        print(name, email, feedback_text)
    return render_template(
        "feedback.html",
        title="Feedback - Easy Tamil Tools",
        description="Send your feedback and suggestions to Easy Tamil Tools.",
        keywords="feedback easy tamil tools"
    )
# about us codes
@app.route("/about")
def about():
    return render_template("about.html",
                           title="About Us - Easy Tamil Tools",
                           description="Learn more about Easy Tamil Tools and our mission to provide free Tamil online utilities.",
                           keywords="about easy tamil tools, tamil tools website, free tamil utilities")

# search option codes 
# ================= SEARCH =================
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    results = []

    # List of searchable pages in your app
    pages = [
        # Letters
        {"name": "Letters", "url": "/letters"},
        {"name": "School Leave Letter", "url": "/letters/school-leave"},
        {"name": "Office Leave Letter", "url": "/letters/office-leave"},
        {"name": "Bank Close Letter", "url": "/letters/bank-close"},

        # Calculators
        {"name": "Age Calculator", "url": "/age-calculator"},
        {"name": "EMI Calculator", "url": "/emi-calculator"},
        {"name": "BMI Calculator", "url": "/bmi-calculator"},
        {"name": "Percentage Calculator", "url": "/percentage-calculator"},
        {"name": "Unit Converter", "url": "/unit-converter"},
        {"name": "Date Difference Calculator", "url": "/date-difference"},
        {"name": "Case Converter", "url": "/case-converter"},
        {"name": "Number to Words", "url": "/number-to-words"},

        # Tools
        {"name": "Text Counter", "url": "/text-counter"},
        {"name": "QR Code Generator", "url": "/qr-code-generator"},

        # Legal & Info
        {"name": "Privacy Policy", "url": "/privacy"},
        {"name": "Terms & Conditions", "url": "/terms"},
        {"name": "Disclaimer", "url": "/disclaimer"},
        {"name": "About Us", "url": "/about"},
        {"name": "Contact", "url": "/contact"},
        {"name": "Feedback", "url": "/feedback"},
    ]

    # Simple search: check if query is in page name (case-insensitive)
    if query:
        results = [page for page in pages if query.lower() in page["name"].lower()]

    return render_template("search_results.html", query=query, results=results)




# ================= RUN =================
if __name__ == "__main__":
    print("Starting EasyTamilTools Server...")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
