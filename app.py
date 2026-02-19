from flask import Flask, render_template, request, Response, redirect, url_for ,send_file
from datetime import date, datetime
from PIL import Image
import os
from num2words import num2words
import qrcode
import logging
from werkzeug.utils import secure_filename
from pdf2docx import Converter
import uuid
import smtplib
from email.message import EmailMessage
from datetime import datetime
from dateutil.relativedelta import relativedelta



app = Flask(__name__)

# ================= CONFIG =================
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "output"
os.makedirs("uploads", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(filename="error.log", level=logging.ERROR)

REVIEWS_FILE = "reviews.txt"

# ================= HOME =================
@app.route("/")
def home():
    reviews = []

    if os.path.exists(REVIEWS_FILE):
        with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    reviews.append({
                        "name": parts[0],
                        "review": parts[1],
                        "rating": parts[2]
                    })

    return render_template("index.html", reviews=reviews)

# ================= ADD REVIEW =================
@app.route("/add-review", methods=["POST"])
def add_review():
    name = request.form.get("name")
    review = request.form.get("review")
    rating = request.form.get("rating")

    if name and review and rating:
        with open(REVIEWS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{name}|{review}|{rating}\n")

    return redirect("/")

# ================= SITEMAP =================
@app.route("/sitemap.xml")
def sitemap():
    pages = []

    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            if not rule.rule.startswith("/static"):
                pages.append(url_for(rule.endpoint, _external=True))

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

    for page in pages:
        xml += f"""
<url>
<loc>{page}</loc>
<lastmod>{datetime.now().date()}</lastmod>
<priority>0.8</priority>
</url>"""

    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")

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

@app.route("/letters/office-leave")
def office_leave():
    return render_template("office_leave_letter.html")

@app.route("/letters/bank-close")
def bank_close():
    return render_template("bank_close_letter.html")

# ================= CALCULATORS =================

# ================= CALCULATORS HOME =================
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

    return render_template("emi_calculator.html",
        emi=emi,interest=interest,total=total,principal=principal)



@app.route("/percentage-calculator", methods=["GET","POST"])
def percentage_calculator():
    result=None
    if request.method=="POST":
        value=float(request.form["value"])
        total=float(request.form["total"])
        result=round((value/total)*100,2) if total!=0 else "error"
    return render_template("percentage_calculator.html",result=result)

@app.route('/date-difference-calculator', methods=['GET', 'POST'])
def date_difference_calculator():
    result = None
    error = None

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")

            if d2 < d1:
                d1, d2 = d2, d1

            difference = relativedelta(d2, d1)
            total_days = (d2 - d1).days

            result = {
                "years": difference.years,
                "months": difference.months,
                "days": difference.days,
                "total_days": total_days
            }

        except:
            error = "Invalid Date Entered"

    return render_template("date_difference_calculator.html", result=result, error=error)


# ================= TOOLS =================
# ================= TOOLS HOME =================
@app.route("/tools")
def tools():
    return render_template("tools.html")

# -------------------------------
# TAMIL PDF TO WORD CONVERTER
# -------------------------------

@app.route("/tamil-pdf-to-word", methods=["GET","POST"])
def tamil_pdf_to_word():

    if request.method == "POST":

        file = request.files.get("pdf_file")

        if file:

            filename = secure_filename(file.filename)
            unique = str(uuid.uuid4())

            pdf_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                unique + ".pdf"
            )

            docx_path = os.path.join(
                app.config["OUTPUT_FOLDER"],
                unique + ".docx"
            )

            file.save(pdf_path)

            try:
                cv = Converter(pdf_path)
                cv.convert(docx_path)
                cv.close()

                return send_file(docx_path, as_attachment=True)

            except Exception as e:
                return f"Conversion Failed: {e}"

    return render_template("tamil_pdf_to_word.html")
# -------------------------------
# text-counter
# -------------------------------

@app.route("/text-counter", methods=["GET","POST"])
def text_counter():
    text=""
    word_count=char_count=char_no_space=line_count=0

    if request.method=="POST":
        text=request.form.get("text","")
        word_count=len(text.split())
        char_count=len(text)
        char_no_space=len(text.replace(" ",""))
        line_count=len(text.splitlines())

    return render_template("text_counter.html",
        text=text,word_count=word_count,
        char_count=char_count,
        char_no_space=char_no_space,
        line_count=line_count)

# -------------------------------
# CASE CONVERTER
# -------------------------------
@app.route("/case-converter", methods=["GET","POST"])
def case_converter():
    text=""
    result=""
    action="upper"

    if request.method=="POST":
        text=request.form.get("text","")
        action=request.form.get("action")

        if action=="upper":
            result=text.upper()
        elif action=="lower":
            result=text.lower()
        elif action=="title":
            result=text.title()

    return render_template(
        "case_converter.html",
        text=text,
        result=result,
        action=action
    )


# -------------------------------
# UNIT CONVERTER
# -------------------------------
@app.route("/unit-converter", methods=["GET","POST"])
def unit_converter():
    value=None
    unit=""
    result=None

    if request.method=="POST":
        value=float(request.form.get("value"))
        unit=request.form.get("unit")

        if unit=="cm_to_m":
            result=value/100
        elif unit=="m_to_cm":
            result=value*100
        elif unit=="m_to_ft":
            result=value*3.28084
        elif unit=="ft_to_m":
            result=value/3.28084
        elif unit=="km_to_mile":
            result=value*0.621371
        elif unit=="mile_to_km":
            result=value/0.621371
        elif unit=="inch_to_cm":
            result=value*2.54
        elif unit=="cm_to_inch":
            result=value/2.54
        elif unit=="kg_to_g":
            result=value*1000
        elif unit=="g_to_kg":
            result=value/1000
        elif unit=="pound_to_kg":
            result=value*0.453592
        elif unit=="kg_to_pound":
            result=value*2.20462
        elif unit=="c_to_f":
            result=(value*9/5)+32
        elif unit=="f_to_c":
            result=(value-32)*5/9

        result=round(result,4)

    return render_template(
        "unit_converter.html",
        value=value,
        unit=unit,
        result=result
    )


# -------------------------------
# NUMBER TO WORDS
# -------------------------------
from num2words import num2words

@app.route("/number-to-words", methods=["GET","POST"])
def number_to_words():
    number=None
    result=""
    lang="en"

    if request.method=="POST":
        number=request.form.get("number")
        lang=request.form.get("lang")

        if number:
            if lang=="ta":
                result=num2words(int(number), lang="ta")
            else:
                result=num2words(int(number), lang="en")

    return render_template(
        "number_to_words.html",
        number=number,
        result=result,
        lang=lang
    )

# -------------------------------
# qr-code-generator
# -------------------------------

@app.route("/qr-code-generator", methods=["GET","POST"])
def qr_code_generator():
    qr_image=None
    data=""

    if request.method=="POST":
        data=request.form.get("data")
        if data:
            img=qrcode.make(data)
            path="static/qr_code.png"
            img.save(path)
            qr_image=path

    return render_template("qr_code_generator.html",
        qr_image=qr_image,data=data)

# -------------------------------
# IMAGE COMPRESSOR
# -------------------------------


@app.route("/image-compressor", methods=["GET","POST"])
def image_compressor():

    compressed_image=None

    if request.method=="POST":

        file=request.files.get("image")

        if file:

            filename=secure_filename(file.filename)
            input_path=os.path.join("static/uploads", filename)
            output_path=os.path.join("static/compressed", filename)

            file.save(input_path)

            img=Image.open(input_path)
            img.save(output_path, optimize=True, quality=60)

            compressed_image=output_path

    return render_template(
        "image_compressor.html",
        compressed_image=compressed_image
    )

# ================= LEGAL =================
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        feedback_text = request.form.get("feedback")
        print(name, email, feedback_text)
    return render_template("feedback.html")



@app.route("/advertise", methods=["GET","POST"])
def advertise():
    if request.method=="POST":
        name=request.form.get("name")
        email=request.form.get("email")
        company=request.form.get("company")
        message=request.form.get("message")

        msg=EmailMessage()
        msg["Subject"]="New Sponsor Enquiry - EasyTamilTools"
        msg["From"]="yourgmail@gmail.com"
        msg["To"]="yourgmail@gmail.com"

        msg.set_content(f"""
New Advertising Enquiry

Name: {name}
Email: {email}
Company/Website: {company}

Message:
{message}
""")

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login("easytamiltools@gmail.com","rmqu yjgx tvnu eoty")
            server.send_message(msg)

        return render_template("advertise.html", success=True)

    return render_template("advertise.html")



# ================= RUN =================
if __name__ == "__main__":
    print("Starting EasyTamilTools Server...")
    app.run(debug=True)
