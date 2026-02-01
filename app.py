from flask import Flask, render_template, request
from datetime import date
from PIL import Image
import pytesseract

# ================= CONFIG =================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)

# ================= HOME =================
@app.route("/")
def home():
    return render_template(
        "index.html",
        title="Easy Tamil Tools – Free Online Calculators & Letter Formats",
        description="Free Tamil tools like calculators, unit converters, OCR tools and ready-made Tamil & English letter formats."
    )

# ================= LEGAL PAGES =================
@app.route("/privacy")
def privacy():
    return render_template(
        "privacy.html",
        title="Privacy Policy - EasyTamilTools",
        description="Privacy policy of EasyTamilTools explaining data usage and cookies."
    )

@app.route("/terms")
def terms():
    return render_template(
        "terms.html",
        title="Terms & Conditions - EasyTamilTools",
        description="Terms and conditions for using EasyTamilTools website."
    )

@app.route("/disclaimer")
def disclaimer():
    return render_template(
        "disclaimer.html",
        title="Disclaimer - EasyTamilTools",
        description="Disclaimer about content accuracy and external tools."
    )

# ================= LETTERS =================
@app.route("/letters")
def letters():
    return render_template(
        "letters.html",
        title="Tamil Letter Formats – School, Office, Bank",
        description="Free Tamil letter formats including school leave, office leave, bank and Aadhaar letters."
    )

@app.route("/letters/school-leave")
def school_leave():
    return render_template(
        "school_leave_letter.html",
        title="School Leave Letter Format in Tamil",
        description="Free school leave letter format in Tamil."
    )

@app.route("/letters/sick-leave")
def sick_leave():
    return render_template(
        "sick_leave_letter.html",
        title="Sick Leave Letter Format",
        description="Medical sick leave letter format in Tamil and English."
    )

@app.route("/letters/office-leave")
def office_leave():
    return render_template(
        "office_leave_letter.html",
        title="Office Leave Letter Format",
        description="Professional office leave letter format."
    )

@app.route("/letters/bank-close")
def bank_close():
    return render_template(
        "bank_close_letter.html",
        title="Bank Account Closing Letter Format",
        description="Bank account closing letter format for Indian banks."
    )

@app.route("/letters/aadhaar-correction")
def aadhaar_correction():
    return render_template(
        "aadhaar_correction_letter.html",
        title="Aadhaar Correction Letter Format",
        description="Aadhaar correction letter format for name, DOB and address."
    )

# ================= CALCULATORS =================
@app.route("/calculators")
def calculators():
    return render_template(
        "calculators.html",
        title="Online Calculators - Age, BMI, EMI",
        description="Free online calculators like Age, BMI, EMI and Percentage."
    )

@app.route("/age-calculator", methods=["GET", "POST"])
def age_calculator():
    age = None
    if request.method == "POST":
        y, m, d = map(int, request.form["dob"].split("-"))
        birth = date(y, m, d)
        today = date.today()

        years = today.year - birth.year
        months = today.month - birth.month
        days = today.day - birth.day

        if days < 0:
            months -= 1
            days += 30
        if months < 0:
            years -= 1
            months += 12

        age = {"years": years, "months": months, "days": days}

    return render_template(
        "age_calculator.html",
        age=age,
        title="Age Calculator Online",
        description="Calculate your exact age online."
    )

@app.route("/percentage-calculator", methods=["GET", "POST"])
def percentage_calculator():
    result = None
    if request.method == "POST":
        result = round(
            (float(request.form["value"]) / float(request.form["total"])) * 100, 2
        )

    return render_template(
        "percentage_calculator.html",
        result=result,
        title="Percentage Calculator",
        description="Free percentage calculator online."
    )

@app.route("/bmi-calculator", methods=["GET", "POST"])
def bmi_calculator():
    bmi = None
    category = ""
    if request.method == "POST":
        weight = float(request.form["weight"])
        height = float(request.form["height"]) / 100
        bmi = round(weight / (height * height), 2)

        category = (
            "Underweight" if bmi < 18.5 else
            "Normal" if bmi < 25 else
            "Overweight" if bmi < 30 else
            "Obese"
        )

    return render_template(
        "bmi_calculator.html",
        bmi=bmi,
        category=category,
        title="BMI Calculator Online",
        description="Calculate your BMI instantly."
    )

@app.route("/emi-calculator", methods=["GET", "POST"])
def emi_calculator():
    emi = None
    if request.method == "POST":
        p = float(request.form["principal"])
        r = float(request.form["rate"]) / 12 / 100
        n = int(request.form["years"]) * 12
        emi = round(p * r * (1 + r) ** n / ((1 + r) ** n - 1), 2)

    return render_template(
        "emi_calculator.html",
        emi=emi,
        title="EMI Calculator",
        description="Loan EMI calculator online."
    )

# ================= TOOLS =================
@app.route("/tools")
def tools():
    return render_template(
        "tools.html",
        title="Online Tools - EasyTamilTools",
        description="Free online utilities like OCR, text counter and converters."
    )

@app.route("/image-to-text", methods=["GET", "POST"])
def image_to_text():
    text = ""
    if request.method == "POST" and "image" in request.files:
        img = Image.open(request.files["image"])
        text = pytesseract.image_to_string(img, lang="tam+eng")

    return render_template(
        "image_to_text.html",
        text=text,
        title="Image to Text Converter",
        description="Convert images to Tamil and English text."
    )

@app.route("/text-counter", methods=["GET", "POST"])
def text_counter():
    text = ""
    count = 0
    if request.method == "POST":
        text = request.form["text"]
        count = len(text.split())

    return render_template(
        "text_counter.html",
        text=text,
        count=count,
        title="Text Counter Tool",
        description="Count words and characters online."
    )

@app.route("/date-difference", methods=["GET", "POST"])
def date_difference():
    diff = None
    if request.method == "POST":
        d1 = date.fromisoformat(request.form["date1"])
        d2 = date.fromisoformat(request.form["date2"])
        diff = abs((d2 - d1).days)

    return render_template(
        "date_difference.html",
        diff=diff,
        title="Date Difference Calculator",
        description="Calculate difference between two dates."
    )

@app.route("/case-converter", methods=["GET", "POST"])
def case_converter():
    result = ""
    if request.method == "POST":
        text = request.form["text"]
        action = request.form["action"]
        result = (
            text.upper() if action == "upper"
            else text.lower() if action == "lower"
            else text.title()
        )

    return render_template(
        "case_converter.html",
        result=result,
        title="Case Converter",
        description="Convert text case online."
    )

@app.route("/number-to-words", methods=["GET", "POST"])
def number_to_words():
    result = ""
    if request.method == "POST":
        num = request.form.get("number")
        if num and num.isdigit() and int(num) < 100000:
            result = convert_number_to_words(int(num))
        else:
            result = "Invalid number"

    return render_template(
        "number_to_words.html",
        result=result,
        title="Number to Words Converter",
        description="Convert numbers into words."
    )

@app.route("/unit-converter", methods=["GET", "POST"])
def unit_converter():
    result = None
    if request.method == "POST":
        value = float(request.form["value"])
        unit = request.form["unit"]
        result = (
            value / 100 if unit == "cm_to_m" else
            value * 100 if unit == "m_to_cm" else
            value * 1000 if unit == "kg_to_g" else
            value / 1000
        )

    return render_template(
        "unit_converter.html",
        result=result,
        title="Unit Converter",
        description="Convert units easily online."
    )

# ================= SEARCH =================
@app.route("/search")
def search():
    query = request.args.get("q", "").lower()

    tools = [
        {"name": "Age Calculator", "url": "/age-calculator"},
        {"name": "BMI Calculator", "url": "/bmi-calculator"},
        {"name": "EMI Calculator", "url": "/emi-calculator"},
        {"name": "Text Counter", "url": "/text-counter"},
        {"name": "Date Difference", "url": "/date-difference"},
        {"name": "Case Converter", "url": "/case-converter"},
        {"name": "Number to Words", "url": "/number-to-words"},
        {"name": "Unit Converter", "url": "/unit-converter"},
        {"name": "Image to Text", "url": "/image-to-text"},
    ]

    letters = [
        {"name": "School Leave Letter", "url": "/letters/school-leave"},
        {"name": "Sick Leave Letter", "url": "/letters/sick-leave"},
        {"name": "Office Leave Letter", "url": "/letters/office-leave"},
        {"name": "Bank Account Closing Letter", "url": "/letters/bank-close"},
        {"name": "Aadhaar Correction Letter", "url": "/letters/aadhaar-correction"},
    ]

    if not query:
        results = tools + letters
    else:
        results = [i for i in tools + letters if query in i["name"].lower()]

    return render_template(
        "search_results.html",
        query=query,
        results=results,
        title=f"Search results for {query}"
    )

# ================= NUMBER TO WORDS LOGIC =================
def convert_number_to_words(n):
    ones = ["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine",
            "Ten","Eleven","Twelve","Thirteen","Fourteen","Fifteen",
            "Sixteen","Seventeen","Eighteen","Nineteen"]
    tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]

    if n == 0:
        return "Zero"
    if n < 20:
        return ones[n]
    if n < 100:
        return tens[n//10] + (" " + ones[n%10] if n%10 else "")
    if n < 1000:
        return ones[n//100] + " Hundred"
    if n < 100000:
        return convert_number_to_words(n//1000) + " Thousand"

    return "Number too large"

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
