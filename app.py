from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_agency_key"  # Required for flash messages

# Central Data for Projects (Easier to update)
PROJECTS = [
    {
        "id": "factory",
        "title": "Factory B2B Export",
        "category": "Manufacturing",
        "desc": {
            "en": "Heavy machinery and tools export site. Focus on technical specs, certifications, and factory tour video.",
            "zh": "重型机械和手工具的出口型网站，突出技术参数、认证资质和工厂参观视频。"
        },        
        "url": "https://factory.skylaneai.com/",
        "icon": "fa-industry"
    },
    {
        "id": "tea",
        "title": "Premium Tea Brand",
        "category": "Consumer Goods",
        "desc": {
            "en": "Luxury storytelling site for a Hangzhou tea farm. Includes origin stories and premium packaging showcase.",
            "zh": "杭州茶园的高端品牌故事型网站，讲述产地故事并展示精美礼盒包装。"
        },
                        "url": "https://tea.skylaneai.com/",
        "icon": "fa-leaf"
    },
    {
        "id": "sourcing",
        "title": "Horizon Sourcing",
        "category": "Service Agency",
        "desc": {
            "en": "Professional service site for a trading partner, clearly outlining sourcing steps, QC, and logistics.",
            "zh": "专业的外贸服务型网站，清晰展示采购流程、质量控制以及物流安排。"
        },
        "url": "http://127.0.0.1:5003/",
        "icon": "fa-handshake"
    },
    {
        "id": "shop",
        "title": "SkyLane Shop",
        "category": "E-Commerce",
        "desc": {
            "en": "Full B2C experience with shopping basket, user accounts, and checkout forms.",
            "zh": "完整的 B2C 独立站体验，包含购物车、用户账号和结算流程。"
        },
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

def localize_projects(lang: str):
    localized = []
    for p in PROJECTS:
        p_copy = dict(p)
        desc = p_copy.get("desc")
        if isinstance(desc, dict):
            p_copy["desc"] = desc.get(lang, desc.get("en"))
        localized.append(p_copy)
    return localized


def get_lang(default="en"):
    lang = request.args.get("lang", default)
    return "zh" if lang.lower() in ("zh", "cn", "zh-cn") else "en"


@app.route("/")
def index_pc():
    lang = get_lang(default="zh")
    return render_template(
        "index_pc.html",
        projects=localize_projects(lang),  # <- use localized descriptions
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
        projects=localize_projects(lang),  # <- use localized descriptions
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
