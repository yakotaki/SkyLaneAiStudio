from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_agency_key"  # Required for flash messages

# Central Data for Projects (Easier to update)
PROJECTS = [
    {
        "id": "factory",
        "title": "Factory B2B Export",
        "category": "Manufacturing",
        "desc": "Heavy machinery and tools export site. Focus on technical specs, certifications, and factory tour video.",
        "url": "https://factory.skylaneai.com/",
        "icon": "fa-industry"
    },
    {
        "id": "tea",
        "title": "Premium Tea Brand",
        "category": "Consumer Goods",
        "desc": "Luxury storytelling site for a Hangzhou tea farm. Includes origin stories and premium packaging showcase.",
        "url": "http://127.0.0.1:5002/",
        "icon": "fa-leaf"
    },
    {
        "id": "sourcing",
        "title": "Horizon Sourcing",
        "category": "Service Agency",
        "desc": "Professional service site for a trading partner. clearly outlining sourcing steps, QC, and logistics.",
        "url": "http://127.0.0.1:5003/",
        "icon": "fa-handshake"
    },
    {
        "id": "shop",
        "title": "SkyLane Shop",
        "category": "E-Commerce",
        "desc": "Full B2C experience with shopping basket, user accounts, and checkout forms.",
        "url": "http://127.0.0.1:5004/",
        "icon": "fa-cart-shopping"
    }
]

PACKAGES = [
    {
        "name": "Starter Export",
        "price": "¥3,900",
        "features": ["5 Page Website", "Mobile Responsive", "Contact Form", "Basic SEO", "1 Month Support"],
        "recommended": False
    },
    {
        "name": "Professional B2B",
        "price": "¥6,800",
        "features": ["10+ Pages", "Product Catalog (50 items)", "Bilingual (CN/EN)", "Whatsapp Integration", "3 Months Support"],
        "recommended": True
    },
    {
        "name": "E-Commerce",
        "price": "¥12,000+",
        "features": ["Online Shop System", "Shopping Cart", "User Accounts", "Payment Gateway Info", "6 Months Support"],
        "recommended": False
    }
]


def get_lang(default="en"):
    lang = request.args.get("lang", default)
    return "zh" if lang.lower() in ("zh", "cn", "zh-cn") else "en"


@app.route("/")
def index_pc():
    lang = get_lang(default="en")
    return render_template(
        "index_pc.html",
        projects=PROJECTS,
        packages=PACKAGES,
        lang=lang,
        is_wechat=False,
    )


@app.route("/wechat")
def index_wechat():
    # For WeChat H5, default to Chinese UI
    lang = get_lang(default="zh")
    return render_template(
        "index_wechat.html",
        projects=PROJECTS,
        lang=lang,
        is_wechat=True,
    )


@app.route("/contact", methods=["POST"])
def contact_submit():
    name = request.form.get("name")
    lang = request.form.get("lang", "en")

    if lang == "zh":
        flash(f"谢谢 {name}！您的需求已经发送，我会在24小时内回复。", "success")
    else:
        flash(f"Thanks {name}! Your inquiry has been sent. I will reply within 24 hours.", "success")

    return redirect(url_for("index_pc", lang=lang))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
