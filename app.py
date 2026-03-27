from flask import Flask, render_template, request, Response, redirect, url_for, send_file, abort, session, jsonify, send_from_directory
from datetime import date, datetime, timedelta
from PIL import Image
import os
import uuid
import logging
import json
import requests
import smtplib
from email.message import EmailMessage
from num2words import num2words
import qrcode
from werkzeug.utils import secure_filename
from pdf2docx import Converter
from dateutil.relativedelta import relativedelta
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from slugify import slugify
from markupsafe import escape
import firebase_admin
from firebase_admin import credentials, firestore, messaging
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
load_dotenv()



# ===============cloudnary intregrated codes=============
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url


def load_gold_data():
    try:
        with open("gold_data.json") as f:
            return json.load(f)
    except:
        return {
            "gold": 0,
            "silver": 0,
            "last_updated": None
        }

def save_gold_data(data):
    with open("gold_data.json", "w") as f:
        json.dump(data, f)

# Configuration       
cloudinary.config(
    cloud_name=os.environ.get("CLOUD_NAME"),
    api_key=os.environ.get("API_KEY"),
    api_secret=os.environ.get("API_SECRET"),
    secure=True
)

# ================= SEARCH DATA =================
# All tools, calculators, PDF tools, and blog posts
SEARCH_ITEMS = [
    # Tools
    {"name": "PDF Compress", "url": "/compress-pdf", "type": "tool"},
    {"name": "PDF Merge", "url": "/pdf-merge", "type": "tool"},
    {"name": "PDF Split", "url": "/pdf-split", "type": "tool"},
    {"name": "Tamil PDF to Word", "url": "/tamil-pdf-to-word", "type": "tool"},
    {"name": "Text Counter", "url": "/text-counter", "type": "tool"},
    {"name": "Case Converter", "url": "/case-converter", "type": "tool"},
    {"name": "Unit Converter", "url": "/unit-converter", "type": "tool"},
    {"name": "Number to Words", "url": "/number-to-words", "type": "tool"},
    {"name": "QR Code Generator", "url": "/qr-code-generator", "type": "tool"},
    {"name": "Image Compressor", "url": "/image-compressor", "type": "tool"},
    {"name": "Age Calculator", "url": "/age-calculator", "type": "calculator"},
    {"name": "EMI Calculator", "url": "/emi-calculator", "type": "calculator"},
    {"name": "Percentage Calculator", "url": "/percentage-calculator", "type": "calculator"},
    {"name": "Date Difference Calculator", "url": "/date-difference-calculator", "type": "calculator"},
    {"name": "Image Converter", "url": "/image-converter", "type": "tool"},
    {"name": "Compress PDF", "url": "/compress-pdf", "type": "tool"},
    {"name": "English to Tamil Typing", "url": "/english-to-tamil-typing", "type": "tool"},
    
    # Letters
    {"name": "School Leave Letter", "url": "/letters/school-leave", "type": "letter"},
    {"name": "Office Leave Letter", "url": "/letters/office-leave", "type": "letter"},
    {"name": "Bank Close Letter", "url": "/letters/bank-close", "type": "letter"},
    
    # Blog Posts (example)
    {"name": "OTT Movie Updates", "url": "/blog/ott/inth-avaram-ott-movies", "type": "blog"},
    # Add more blog posts here
]


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "temporarysecret123"


MANUAL_GOLD_DATA = load_gold_data()

# ================= HEALTH CHECK =================
@app.route("/health")
def health():
    return "Server is live! ✅"


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        password = request.form.get("password")

        # 🔐 Change this password
        if password == os.environ.get("ADMIN_PASSWORD"):
            session["admin_logged_in"] = True
            return redirect("/admin")
        else:
            return "Wrong Password"
        

    return render_template("admin_login.html")
# ===========firebase connected ===========
firebase_json = os.environ.get("FIREBASE_KEY")

try:
    if firebase_json:
        firebase_dict = json.loads(firebase_json)
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)
        print("🔥 Firebase Connected (Render Mode)")
    else:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)
        print("🔥 Firebase Connected (Local Mode)")

    db = firestore.client()

except Exception as e:
    print("🔥 Firebase Initialization Error:", e)
    db = None   # just set db None
# ================= PUSH NOTIFICATION =================
def send_push_notification(title, body, url):

    try:
        tokens_ref = db.collection("fcm_tokens").stream()

        for t in tokens_ref:

            token = t.id

            message = messaging.Message(

                notification=messaging.Notification(
                    title=title,
                    body=body
                ),

                webpush=messaging.WebpushConfig(
                    fcm_options=messaging.WebpushFCMOptions(
                        link=url
                    )
                ),

                token=token
            )

            response = messaging.send(message)
            print("Notification sent:", response)

    # except Exception as e:
    #     print("Push Error:", e)
    except Exception as e:
        print("🔥 Firebase Initialization Error:", e)
        db = None

@app.route("/save-token", methods=["POST"])
def save_token():

    data = request.get_json()
    token = data.get("token")

    if token:
        db.collection("fcm_tokens").document(token).set({
            "created_at": firestore.SERVER_TIMESTAMP
        })

        return jsonify({"status": "saved"})

    return jsonify({"error": "No token"}), 400

#====firebase messing sysytem &subscription route codes=====
@app.route('/firebase-messaging-sw.js')
def firebase_sw():
    return send_from_directory('.', 'firebase-messaging-sw.js')
# ================= CONFIG =================
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(app.root_path, "static", "output")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

logging.basicConfig(filename="error.log", level=logging.ERROR)

# ========cloudinary connect panni image store aaga==========
def upload_image_to_cloudinary(file):

    result = cloudinary.uploader.upload(
        file,
        folder="blog_images"
    )

    return result["secure_url"]

# ================= ADD REVIEW =================
@app.route("/add-review", methods=["POST"])
def add_review():

    name = request.form.get("name")
    review = request.form.get("review")
    rating = request.form.get("rating")

    if name and review and rating:
        db.collection("reviews").add({
            "name": name,
            "review": review,
            "rating": int(rating),
            "timestamp": firestore.SERVER_TIMESTAMP
        })

    return redirect("/")

@app.route("/sitemap.xml")
def sitemap():
    pages = []

    # ================= STATIC USER-FACING PAGES =================
    user_pages = [
        "/", "/privacy", "/terms", "/disclaimer", "/about", "/contact",
        "/feedback", "/advertise", "/letters", "/tools", "/calculators", "/search"
    ]

    for route in user_pages:
        try:
            url = url_for(route.strip("/").replace("/", "_") or "home", _external=True)
        except:
            # fallback for routes like "/search" that may not have endpoint name exactly
            url = url_for("home", _external=True) if route == "/" else request.url_root[:-1] + route
        pages.append({
            "loc": url,
            "priority": "0.8" if route not in ["/", "/search"] else "1.0",
            "changefreq": "daily" if route == "/" else "monthly"
        })

    # ================= BLOG DYNAMIC POSTS (Firebase) =================
    posts_ref = db.collection("posts").stream()
    categories = set()

    for doc in posts_ref:
        data = doc.to_dict()
        category = data.get("category", "general")
        slug = doc.id
        categories.add(category)

        # Individual blog post
        pages.append({
            "loc": url_for("blog_post", category=category, post=slug, _external=True),
            "priority": "0.7",
            "changefreq": "weekly"
        })

    # Add category pages
    for category in categories:
        pages.append({
            "loc": url_for("blog_category", category=category, _external=True),
            "priority": "0.8",
            "changefreq": "weekly"
        })

    # ================= BUILD XML =================
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""

    for page in pages:
        xml += f"""
  <url>
    <loc>{page['loc']}</loc>
    <lastmod>{datetime.now().date()}</lastmod>
    <changefreq>{page['changefreq']}</changefreq>
    <priority>{page['priority']}</priority>
  </url>"""

    xml += "\n</urlset>"

    return Response(xml, mimetype="application/xml")

# =============ROBOTS TEXT==========
@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")
# favicon route codes =====
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico'
    )
# ===============ADMIN PAGE ROUTE==================
from datetime import datetime
from flask import request, redirect, render_template, session
import os
from werkzeug.utils import secure_filename

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    if request.method == "POST":

        title = request.form.get("title")
        slug = request.form.get("slug") or slugify(title)
        # Unique slug fix
        original_slug = slug
        counter = 1

        while db.collection("posts").document(slug).get().exists:
            slug = f"{original_slug}-{counter}"
            counter += 1
        category = request.form.get("category")
        content = request.form.get("content")
        tags = request.form.get("tags")
        meta_title = request.form.get("meta_title")
        meta_description = request.form.get("meta_description")
        status = request.form.get("status")  # draft or publish
        image = request.files.get("image")

        image_filename = None

        # 🔥 Featured Image Upload
        image_url = None

        if image and image.filename != "":
            image_url = upload_image_to_cloudinary(image)

        # 🔥 Save to Firestore
        db.collection("posts").document(slug).set({
            "title": title,
            "slug": slug,
            "category": category,
            "tags": tags,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "content": content,
            "excerpt": content[:150],
            "image": image_url,
            "status": status,
            "views": 0,
            "created_at": firestore.SERVER_TIMESTAMP
        })

        # 🔔 If Published → Send Push
        if status == "publish":
            post_url = f"https://easytamiltools.in/blog/{category}/{slug}"

            send_push_notification(
            title,
            "New update வந்துவிட்டது 🔥",
            post_url
    )

    # ⚡ Auto Ping to Google & Bing
    try:
        requests.get("https://www.google.com/ping?sitemap=https://easytamiltools.in/sitemap.xml")
        requests.get("https://www.bing.com/ping?sitemap=https://easytamiltools.in/sitemap.xml")
        print("✅ Sitemap ping success")
    except Exception as e:
        print("❌ Ping error:", e)
            
        return redirect(f"/blog/{category}/{slug}")

    return render_template("admin.html")

# ===========upload inline images codes in admin.html============
@app.route("/upload-inline-image", methods=["POST"])
def upload_inline_image():

    image = request.files.get("file")

    if image:
        image_url = upload_image_to_cloudinary(image)
        return {"location": image_url}

    return {"error": "Upload failed"}, 400
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

# ===CALCULATORS HOME ====
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
# -------------------------------
# emi-calculator
# -------------------------------
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

# -------------------------------
# percentage-calculator
# -------------------------------


@app.route("/percentage-calculator", methods=["GET","POST"])
def percentage_calculator():
    result=None
    if request.method=="POST":
        value=float(request.form["value"])
        total=float(request.form["total"])
        result=round((value/total)*100,2) if total!=0 else "error"
    return render_template("percentage_calculator.html",result=result)
# -------------------------------
# date-difference-calculator
# -------------------------------

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

# ===== TOOLS HOME ROUTES====
@app.route("/tools")
def tools():
    return render_template("tools.html")

@app.route("/json-formatter")
def json_formatter():
    return render_template("json_formatter.html")

@app.route('/converted/<filename>')
def download_file(filename):
    return send_from_directory(CONVERT_FOLDER, filename, as_attachment=True)

@app.route("/english-to-tamil-typing")
def english_to_tamil_typing():
    return render_template("english_to_tamil_typing.html")

# =============image converter code=============

UPLOAD_FOLDER = "uploads"
CONVERT_FOLDER = "converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png","jpg","jpeg","webp","avif"}

app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

@app.route("/image-converter")
def image_converter():
    return render_template("image_converter.html")


@app.route("/convert-image", methods=["POST"])
def convert_image():
    files = request.files.getlist("images")
    output_format = request.form.get("format")

    format_map = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "avif": "AVIF"
    }

    save_format = format_map.get(output_format.lower())

    if not save_format:
        return jsonify({"error": "Invalid format"}), 400

    converted_files = []

    for file in files:
        filename = secure_filename(file.filename)

        if "." not in filename:
            continue

        unique = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, unique + "_" + filename)
        file.save(input_path)

        img = Image.open(input_path)

        output_filename = unique + "." + output_format
        output_path = os.path.join(CONVERT_FOLDER, output_filename)

        # RGB fix for JPG
        if save_format == "JPEG":
            img = img.convert("RGB")

        img.save(output_path, save_format)

        converted_files.append(output_filename)

    return jsonify({"files": converted_files})
@app.route("/compress-pdf")
def compress_pdf():
    return render_template("compress_pdf.html")
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
# --------------------
# pdf_merge codes
# ----------------------

@app.route("/pdf-merge", methods=["GET","POST"])
def pdf_merge():

    if request.method == "POST":

        files = request.files.getlist("pdf_files")
        output_name = request.form.get("output_name")

        if not files or not output_name:
            return render_template("pdf_merge.html", error="Please select files.")

        merger = PdfMerger()

        upload_folder = "temp_uploads"
        os.makedirs(upload_folder, exist_ok=True)

        temp_paths = []

        try:
            for file in files:
                if file.filename.endswith(".pdf"):
                    filename = secure_filename(file.filename)
                    path = os.path.join(upload_folder, filename)
                    file.save(path)
                    merger.append(path)
                    temp_paths.append(path)

            output_path = os.path.join(upload_folder, output_name + ".pdf")
            merger.write(output_path)
            merger.close()

            for path in temp_paths:
                os.remove(path)

            return send_file(output_path, as_attachment=True)

        except Exception as e:
            return render_template("pdf_merge.html", error="Error merging PDF files.")

    return render_template("pdf_merge.html")

# --------------------
# pdf_split  codes
# ----------------------

@app.route("/pdf-split", methods=["GET","POST"])
def pdf_split_tool():

    if request.method == "POST":

        file = request.files.get("pdf_file")
        page_range = request.form.get("page_range")
        output_name = request.form.get("output_name")

        if not file or not page_range:
            return render_template("pdf_split.html", error="Please upload file and enter page range.")

        upload_folder = "temp_uploads"
        os.makedirs(upload_folder, exist_ok=True)

        try:
            filename = secure_filename(file.filename)
            input_path = os.path.join(upload_folder, filename)
            file.save(input_path)

            reader = PdfReader(input_path)
            writer = PdfWriter()

            total_pages = len(reader.pages)

            if "-" in page_range:
                start, end = page_range.split("-")
                start = int(start) - 1
                end = int(end)

                for i in range(start, end):
                    if i < total_pages:
                        writer.add_page(reader.pages[i])
            else:
                page = int(page_range) - 1
                if page < total_pages:
                    writer.add_page(reader.pages[page])

            output_path = os.path.join(upload_folder, output_name)
            with open(output_path, "wb") as f:
                writer.write(f)

            os.remove(input_path)

            return send_file(output_path, as_attachment=True)

        except Exception as e:
            return render_template("pdf_split.html", error="Error splitting PDF.")

    return render_template("pdf_split.html")

# ================= SEARCH OPTION =================
@app.route("/search")
def search():
    query = request.args.get("q", "").strip().lower()

    if not query:
        return render_template(
            "search_results.html",
            query=query,
            results=[],
            message="Please enter something to search."
        )

    results = []

    # ================= STATIC SEARCH (TOOLS, CALCULATORS, LETTERS) =================
    for item in SEARCH_ITEMS:
        searchable_text = (
            item.get("name", "") + " " +
            item.get("type", "")
        ).lower()

        if query in searchable_text:
            results.append(item)

    # ================= BLOG POSTS SEARCH (FIREBASE) =================
    try:
        if db:
            posts_ref = db.collection("posts").stream()
        else:
            posts_ref = []

        for doc in posts_ref:
            data = doc.to_dict()

            title = data.get("title", "").lower()
            category = data.get("category", "")
            slug = doc.id

            if query in title:
                results.append({
                    "name": data.get("title"),
                    "url": f"/blog/{category}/{slug}",
                    "type": "blog"
                })

    except Exception as e:
        print("Search Blog Error:", e)

    # ================= REMOVE DUPLICATES =================
    unique_results = []
    seen_urls = set()

    for item in results:
        if item["url"] not in seen_urls:
            unique_results.append(item)
            seen_urls.add(item["url"])

    # ================= MESSAGE =================
    message = None
    if not unique_results:
        message = f"Item not found for '{query}'"

    return render_template(
        "search_results.html",
        query=query,
        results=unique_results,
        message=message
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

# ============advertise===========

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
            server.login("easytamiltools@gmail.com", os.environ.get("EMAIL_PASS"))
            server.send_message(msg)

        return render_template("advertise.html", success=True)

    return render_template("advertise.html")

# ================= BLOG SYSTEM ROUTES =================

@app.route("/blog")
def blog_list():
    posts_ref = db.collection("posts").stream()
    categories = set()

    for doc in posts_ref:
        cat = doc.to_dict().get("category")
        if cat:
            categories.add(cat)

    return render_template("blog/home.html", categories=categories)

@app.route("/blog/<category>")
def blog_category(category):
    breadcrumb = [
    {"name": "Home", "url": "https://easytamiltools.in/"},
    {"name": category.upper(), "url": f"https://easytamiltools.in/blog/{category}"}
]
    # 🔥 latest first (DESCENDING)
    posts_ref = db.collection("posts") \
        .where("category", "==", category) \
        .order_by("created_at", direction=firestore.Query.DESCENDING) \
        .stream()


    posts = []

    for doc in posts_ref:
        data = doc.to_dict()
        posts.append({
        "title": data.get("title"),
        "slug": doc.id,   # 🔥 THIS IS THE FIX
        "description": data.get("content")[:150] + "...",
        "views": data.get("views", 0),
        "image": data.get("image", None),
        "category": category   # optional but safe
    })
    # If no posts found
    if not posts:
        return render_template(
            "category.html",
            category=category,
            posts=[]
        )

    return render_template(
    "blog/category.html",
    category=category,
    posts=posts,
    breadcrumb=breadcrumb
    
)

@app.route("/blog/<category>/<post>")
def blog_post(category, post):

    # 🔥 Firebase fetch
    post_ref = db.collection("posts").document(post)
    doc = post_ref.get()

    if not doc.exists:
        abort(404)

    data = doc.to_dict()

    # 🔥 CATEGORY VALIDATION (SEO FIX)
    if data.get("category") != category:
        abort(404)

    # ✅ BREADCRUMB (AFTER data)
    breadcrumb = [
        {"name": "Home", "url": "https://easytamiltools.in/"},
        {"name": category.upper(), "url": f"https://easytamiltools.in/blog/{category}"},
        {"name": data.get("title"), "url": request.url}
    ]

    # 🔥 Update View Count
    post_ref.update({"views": firestore.Increment(1)})
    views = data.get("views", 0) + 1

    # 🔥 Safe defaults
    data.setdefault("image", None)
    data.setdefault("views", 0)

    # 🔥 Reviews
    reviews_ref = db.collection("reviews").where("post", "==", post).stream()
    total, count = 0, 0

    for r in reviews_ref:
        total += r.to_dict().get("rating", 0)
        count += 1

    avg_rating = round(total / count, 1) if count > 0 else 0

    # ================= RELATED POSTS =================
    related_query = db.collection("posts").limit(4).stream()
    related_posts = []

    for r in related_query:
        if r.id != post:
            data_r = r.to_dict()
            data_r["slug"] = r.id
            related_posts.append(data_r)

    # 🔥 FETCH COMMENTS
    comments_ref = post_ref.collection("comments") \
        .where("approved", "==", True) \
        .order_by("created_at", direction=firestore.Query.ASCENDING)

    comments_stream = comments_ref.stream()

    comments = []
    for c in comments_stream:
        data_c = c.to_dict()
        data_c["id"] = c.id
        comments.append(data_c)

    # 🔥 Separate comments & replies
    main_comments = [c for c in comments if not c.get("parent_id")]
    replies = [c for c in comments if c.get("parent_id")]

    for main in main_comments:
        main["replies"] = [
            r for r in replies if r.get("parent_id") == main["id"]
        ]

    # 🔥 FINAL RENDER
    return render_template(
        "blog/post.html",
        content=data.get("content"),
        title=data.get("title"),
        image=data.get("image"),
        slug=post,
        post=data,
        category=category,
        views=views,
        avg_rating=avg_rating,
        review_count=count,
        comments=main_comments,
        related_posts=related_posts,
        breadcrumb=breadcrumb
    )
@app.route("/")
def home():

    breadcrumb = [
    {"name": "Home", "url": "https://easytamiltools.in/"}
    ]
    # 🔥 GOLD + SILVER RATE FETCH
    city = request.args.get("city", "chennai")

    gold_price = MANUAL_GOLD_DATA["gold"]
    silver_price = MANUAL_GOLD_DATA["silver"]

    gold_price = get_location_rate(city, gold_price)

    # 🔥 LATEST POSTS FETCH
    latest_query = db.collection("posts") \
        .order_by("created_at", direction=firestore.Query.DESCENDING) \
        .limit(8) \
        .stream()

    latest_posts = []
    categories = set()

    for doc in latest_query:
        data = doc.to_dict()

        data["slug"] = doc.id
        data["category"] = data.get("category", "general")

        latest_posts.append(data)

        if data.get("category"):
            categories.add(data["category"])

    # 🧪 DEBUG (optional - remove later)
    print("Gold Price:", gold_price)
    print("Silver Price:", silver_price)

    # 🔥 SEND DATA TO HTML
    return render_template(
        "index.html",
        categories=categories,
        latest_posts=latest_posts,
        gold_price=gold_price,
        silver_price=silver_price,
        gold_data=MANUAL_GOLD_DATA,
        breadcrumb=breadcrumb
    )
# ===============comment sec add codes==========
@app.route("/add-comment/<category>/<post>", methods=["POST"])
def add_comment(category, post):

    name = escape(request.form.get("name"))
    message = escape(request.form.get("message"))
    parent_id = request.form.get("parent_id") or None

    comment_data = {
        "name": name,
        "message": message,
        "parent_id": parent_id,
        "created_at": firestore.SERVER_TIMESTAMP,
        "approved": True
    }

    db.collection("posts") \
      .document(post) \
      .collection("comments") \
      .add(comment_data)

    return redirect(url_for("blog_post", category=category, post=post))


# =========web-push-notification======
# @app.route("/save-token", methods=["POST"])
# def save_token():
#     data = request.get_json()
#     token = data.get("token")
#     if token:
#         db.collection("fcm_tokens").document(token).set({
#             "token": token,
#             "subscribed_at": firestore.SERVER_TIMESTAMP
#         })
#         return jsonify({"success": True})
#     return jsonify({"success": False}), 400

# def send_push_notification(title, body, url=None):
#     tokens_ref = db.collection("fcm_tokens").stream()
#     tokens = [t.id for t in tokens_ref]

#     headers = {
#         "Authorization": f"key={os.environ.get('FCM_SERVER_KEY')}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "registration_ids": tokens,
#         "notification": {
#             "title": title,
#             "body": body,
#             "click_action": url or "https://yourdomain.com",
#             "icon": "https://yourdomain.com/static/logo.png"
#         }
#     }

#     r = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, json=payload)
#     print("FCM Response:", r.text)

# @app.route("/save-token", methods=["POST"])
# def save_token():

#     data = request.json
#     token = data.get("token")

#     if token:
#         db.collection("fcm_tokens").document(token).set({
#             "created_at": firestore.SERVER_TIMESTAMP
#         })

#     return {"status": "success"}

#=====gold and silver arate manual update=====
@app.route("/update-gold", methods=["POST"])
def update_gold():

    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    global MANUAL_GOLD_DATA

    gold = request.form.get("gold")
    silver = request.form.get("silver")

    MANUAL_GOLD_DATA = {
        "gold": float(gold),
        "silver": float(silver),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    save_gold_data(MANUAL_GOLD_DATA)  # 🔥 முக்கியம்

    return redirect("/")

def save_gold_data(data):
    with open("gold_data.json", "w") as f:
        json.dump(data, f)

    
def get_location_rate(city, base_price):

    # 🔥 Simple demo logic (நீ later DB/API connect பண்ணலாம்)

    city_rates = {
        "chennai": base_price,
        "nagercoil": base_price + 20,  # example difference
    }

    return city_rates.get(city, base_price)
# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)  # production