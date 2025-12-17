
import os
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify

from openai import OpenAI

app = Flask(__name__)
app.secret_key = "your_secret_agency_key"  # Required for flash and sessions

# === OpenAI client ===
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Toggle AI chat per site (you can later turn this off for some clients)
ENABLE_AI_CHAT = True
ENABLE_SMART_RFQ = True

# --- Central Data for Projects (bilingual desc) ---
PROJECTS = [
    {
        "id": "factory",
        "title": "Factory B2B Export",
        "category": "Manufacturing",
        "desc": {
            "en": "Heavy machinery and tools export site. Focus on technical specs, certifications, and factory tour video.",
            "zh": "重型机械和手工具出口型网站，重点展示技术参数、认证资质和工厂参观内容。"
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
            "zh": "杭州茶园的高端品牌故事网站，结合产地故事与精致礼盒包装展示。"
        },
        "url": "https://tea.skylaneai.com/",
        "icon": "fa-leaf"
    },
    {
        "id": "sourcing",
        "title": "Horizon Sourcing",
        "category": "Service Agency",
        "desc": {
            "en": "Futuristic sourcing control center for importers: live-like process visuals, QC timelines, and logistics tracking screens.",
            "zh": "面向海外买家的未来感采购控制中枢网站，以短视频和可视化流程展示选品、质检与物流全流程。"
        },
        "url": "https://sourcing.skylaneai.com/",
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
        "url": "https://shop-demo.skylaneai.com/",  # when deployed
        "icon": "fa-cart-shopping"
    }
]

PACKAGES = [
    {
        "id": "pkg_factory",
        "project_id": "factory",  # links to PROJECTS[id="factory"]
        "name": {
            "en": "Factory Export Starter Site",
            "zh": "工厂出口官网 · 入门版"
        },
        "price": {
            "en": "¥3,900",
            "zh": "¥3,900"
        },
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: Factory B2B export demo",
                "Up to 5 pages (Home, About, Products, QC, Contact)",
                "Bilingual EN / CN content",
                "Inquiry form that sends RFQs to your email"
            ],
            "zh": [
                "基于：工厂 B2B 出口演示网站",
                "最多 5 个页面（首页 / 公司介绍 / 产品列表 / 质量控制 / 联系我们）",
                "中英双语内容",
                "在线询盘表单（自动发送到您的邮箱）"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Smart RFQ – expand buyer notes into a full RFQ",
                "Optional: AI Export Assistant chat widget"
            ],
            "zh": [
                "可选：AI 智能 RFQ – 把买家备注扩展为完整询盘",
                "可选：AI 出口助手聊天窗口"
            ]
        }
    },
    {
        "id": "pkg_sourcing",
        "project_id": "sourcing",
        "name": {
            "en": "Sourcing & Service Website",
            "zh": "一站式采购服务官网"
        },
        "price": {
            "en": "¥6,800",
            "zh": "¥6,800"
        },
        "recommended": True,
        "bullets": {
            "en": [
                "Based on: Horizon Sourcing demo",
                "Service pages for sourcing, QC, logistics and workflow",
                "Case studies / project timeline sections",
                "Contact / RFQ form with multi-step fields"
            ],
            "zh": [
                "基于：Horizon Sourcing 演示站",
                "完整服务页面：采购 / 质检 / 物流及流程说明",
                "案例展示与项目时间线模块",
                "多步骤询盘表单，收集更完整项目信息"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Smart RFQ for complex projects",
                "Optional: AI Export Assistant for 24/7 pre-sales questions",
                "Optional: AI Market Navigator (basic market suggestions)"
            ],
            "zh": [
                "可选：AI 智能 RFQ（适合复杂项目）",
                "可选：AI 出口助手（7x24 小时预售问答）",
                "可选：AI 市场导航（基础市场建议）"
            ]
        }
    },
    {
        "id": "pkg_tea",
        "project_id": "tea",
        "name": {
            "en": "Brand Storytelling Site (Tea)",
            "zh": "品牌故事官网（以茶叶为例）"
        },
        "price": {
            "en": "¥4,800",
            "zh": "¥4,800"
        },
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: Premium Tea Brand demo",
                "Story-driven layout with photos and short videos",
                "Sections for origin story, process, packaging and gallery",
                "Lead capture form for distributors and importers"
            ],
            "zh": [
                "基于：高端茶叶品牌演示站",
                "以图片与短视频为主的品牌故事布局",
                "原产地故事 / 制作过程 / 包装展示 / 图库模块",
                "用于收集代理商与进口商信息的表单"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Export Assistant for brand Q&A",
                "Optional: AI Product Advisor for tea selection help"
            ],
            "zh": [
                "可选：AI 出口助手，回答品牌相关问题",
                "可选：AI 产品顾问，帮买家选择茶叶款式"
            ]
        }
    },
    {
        "id": "pkg_shop",
        "project_id": "shop",
        "name": {
            "en": "Export E-Commerce Shop",
            "zh": "出口型独立商城"
        },
        "price": {
            "en": "¥12,000+",
            "zh": "¥12,000+"
        },
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: SkyLane Shop demo (basket + login + checkout)",
                "Product catalog, shopping cart and demo checkout flow",
                "User account area with sample orders",
                "Ready for Stripe / PayPal / bank transfer integration"
            ],
            "zh": [
                "基于：SkyLane 商城演示站（含购物车 / 登录 / 结算）",
                "产品目录、购物车及演示结算流程",
                "带示例订单的用户中心页面",
                "可扩展接入 Stripe / PayPal / 银行转账等支付方式"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Product Advisor to recommend products",
                "Optional: AI Export Assistant for order and shipping questions"
            ],
            "zh": [
                "可选：AI 产品顾问，为买家推荐合适产品",
                "可选：AI 出口助手，回答订单与物流问题"
            ]
        }
    },
]

DASHBOARD_SITES = [
    {
        "id": "factory",
        "name_en": "Factory B2B Export",
        "name_zh": "工厂 B2B 出口官网",
        "url": "https://factory.skylaneai.com/",
        "type": "B2B",
        "status": "online",
        "leads_30d": 18,
        "ai_rfq": True,
        "ai_chat": True,
    },
    {
        "id": "tea",
        "name_en": "Premium Tea Brand",
        "name_zh": "高端茶叶品牌官网",
        "url": "https://tea.skylaneai.com/",
        "type": "Brand",
        "status": "online",
        "leads_30d": 11,
        "ai_rfq": False,
        "ai_chat": True,
    },
    {
        "id": "sourcing",
        "name_en": "Horizon Sourcing",
        "name_zh": "Horizon 采购服务网站",
        "url": "https://sourcing.skylaneai.com/",
        "type": "Service",
        "status": "building",
        "leads_30d": 7,
        "ai_rfq": True,
        "ai_chat": False,
    },
    {
        "id": "shop",
        "name_en": "SkyLane Shop (B2C)",
        "name_zh": "SkyLane B2C 商城",
        "url": "https://shop-demo.skylaneai.com/",
        "type": "E-Commerce",
        "status": "online",
        "leads_30d": 9,
        "ai_rfq": False,
        "ai_chat": True,
    },
]

DASHBOARD_RECENT_LEADS = [
    {
        "site_id": "factory",
        "date": "2025-12-01",
        "company": "Ningbo Tools Co.",
        "country": "DE",
        "project_en": "Socket & wrench set for German distributor",
        "project_zh": "面向德国经销商的套筒扳手组套项目",
        "budget": "USD 15,000",
    },
    {
        "site_id": "tea",
        "date": "2025-12-03",
        "company": "Hangzhou Leaf Story",
        "country": "US",
        "project_en": "Premium gift tea boxes for online store",
        "project_zh": "高端礼盒茶叶，用于跨境电商平台",
        "budget": "USD 8,000",
    },
    {
        "site_id": "shop",
        "date": "2025-12-05",
        "company": "Demo online buyer",
        "country": "UK",
        "project_en": "Sample B2C export shop test order",
        "project_zh": "B2C 出口商城测试订单",
        "budget": "USD 3,500",
    },
]


def build_dashboard_summary(lang: str) -> dict:
    """Prepare data for Export Command Center view."""
    total_sites = len(DASHBOARD_SITES)
    total_leads_30d = sum(s.get("leads_30d", 0) for s in DASHBOARD_SITES)
    ai_enabled_sites = sum(
        1 for s in DASHBOARD_SITES if s.get("ai_rfq") or s.get("ai_chat")
    )

    # Localize site names + AI labels
    sites_localized = []
    for site in DASHBOARD_SITES:
        s = dict(site)
        s["display_name"] = site["name_zh"] if lang == "zh" else site["name_en"]

        ai_labels = []
        if site.get("ai_rfq"):
            ai_labels.append("AI Smart RFQ" if lang == "en" else "AI 智能 RFQ")
        if site.get("ai_chat"):
            ai_labels.append("AI Chat" if lang == "en" else "AI 在线咨询")
        s["ai_label_str"] = ", ".join(ai_labels) if ai_labels else (
            "None" if lang == "en" else "暂无"
        )

        sites_localized.append(s)

    # Localize recent leads
    recent_leads = []
    for lead in DASHBOARD_RECENT_LEADS:
        l = dict(lead)
        site = next((s for s in sites_localized if s["id"] == lead["site_id"]), None)
        if site:
            l["site_name"] = site["display_name"]
        l["project"] = lead["project_zh"] if lang == "zh" else lead["project_en"]
        recent_leads.append(l)

    return {
        "total_sites": total_sites,
        "total_leads_30d": total_leads_30d,
        "ai_enabled_sites": ai_enabled_sites,
        "sites": sites_localized,
        "recent_leads": recent_leads,
    }


def get_lang(default="en"):
    lang = request.args.get("lang", default)
    return "zh" if lang and lang.lower() in ("zh", "cn", "zh-cn") else "en"


def localize_projects(lang: str):
    """Flatten bilingual desc into plain string for templates."""
    localized = []
    for p in PROJECTS:
        p_copy = dict(p)
        desc = p_copy.get("desc")
        if isinstance(desc, dict):
            p_copy["desc"] = desc.get(lang, desc.get("en"))
        localized.append(p_copy)
    return localized

def localize_packages(lang: str):
    """Return packages ready for display with localized text and demo links."""
    project_map = {p["id"]: p for p in PROJECTS}
    localized = []
    for pkg in PACKAGES:
        p = dict(pkg)

        # Name & price
        name_data = p.get("name")
        if isinstance(name_data, dict):
            p["display_name"] = name_data.get(lang, name_data.get("en")) or ""
        else:
            p["display_name"] = name_data or ""

        price_data = p.get("price")
        if isinstance(price_data, dict):
            p["display_price"] = price_data.get(lang, price_data.get("en")) or ""
        else:
            p["display_price"] = price_data or ""

        # Bullets & AI options
        bullets_data = p.get("bullets", {})
        ai_data = p.get("ai_options", {})
        if isinstance(bullets_data, dict):
            p["display_bullets"] = bullets_data.get(lang, bullets_data.get("en", []))
        else:
            p["display_bullets"] = bullets_data or []

        if isinstance(ai_data, dict):
            p["display_ai_options"] = ai_data.get(lang, ai_data.get("en", []))
        else:
            p["display_ai_options"] = ai_data or []

        # Link to demo project
        proj = project_map.get(p.get("project_id"))
        if proj:
            p["demo_title"] = proj.get("title")
            p["demo_url"] = proj.get("url")
            p["demo_icon"] = proj.get("icon")
        else:
            p["demo_title"] = None
            p["demo_url"] = None
            p["demo_icon"] = None

        localized.append(p)
    return localized


def build_smart_rfq_prompt(data: dict, lang: str) -> str:
    """
    Build the user prompt for the RFQ expander.
    data keys (all optional): company, buyer_name, email, country, product, quantity,
                              incoterm, target_port, quality_level, certifications,
                              packaging, notes
    lang: "en" or "zh"
    """
    if lang == "zh":
        base_instructions = """
你是一名外贸手工具/一般工业品的资深业务员，擅长把客户的原始需求整理成结构化的询盘/报价单（RFQ）。
请根据下面信息，生成：

1) 一份【英文】RFQ，结构清晰、适合发送给中国工厂或外贸公司的业务员；
2) 一份【中文】版本，方便转发给工厂或内部团队。

要求：
- 用条目或小标题分段（如：Buyer info, Product spec, Quality, Packaging, Incoterms, QC, Others 等）；
- 不要发邮件问候语（如 Dear Sir），直接从“Buyer info”开始；
- 可以合理补充缺失但常见的信息（并标注为“to be confirmed”）。
输出格式使用 JSON，对象中包含两个字段：rfq_en 和 rfq_zh，其值为字符串。
"""
    else:
        base_instructions = """
You are an experienced export sales manager for tools/general industrial products.
Your job is to turn a buyer's rough message into a clean, structured RFQ (request for quotation).

Please produce:

1) A clear ENGLISH RFQ suitable to send to Chinese factories or trading companies.
2) A CHINESE version of the same RFQ for internal use or for factories.

Requirements:
- Use clear sections (e.g., Buyer info, Product spec, Quality, Packaging, Incoterms, QC, Others).
- No email greetings (no “Dear Sir/Madam”); start directly with the RFQ sections.
- You may reasonably fill in common missing details, marking them as “to be confirmed”.
Return the result as JSON with two string fields: rfq_en and rfq_zh.
"""

    # Build a compact description from provided fields
    parts = []

    def add_line(label: str, value_key: str):
        value = data.get(value_key)
        if value:
            parts.append(f"{label}: {value}")

    if lang == "zh":
        add_line("公司名称", "company")
        add_line("联系人", "buyer_name")
        add_line("邮箱", "email")
        add_line("采购国家/地区", "country")
        add_line("产品方向", "product")
        add_line("大致数量或金额", "quantity")
        add_line("希望的贸易条款 (Incoterm)", "incoterm")
        add_line("目的港/城市", "target_port")
        add_line("目标质量档次", "quality_level")
        add_line("认证或要求标准", "certifications")
        add_line("包装要求", "packaging")
        add_line("补充说明", "notes")
    else:
        add_line("Company", "company")
        add_line("Contact person", "buyer_name")
        add_line("Email", "email")
        add_line("Buyer country/region", "country")
        add_line("Product focus", "product")
        add_line("Approx. quantity/budget", "quantity")
        add_line("Preferred Incoterm", "incoterm")
        add_line("Target port/city", "target_port")
        add_line("Quality level", "quality_level")
        add_line("Required certifications/standards", "certifications")
        add_line("Packaging requirements", "packaging")
        add_line("Extra notes", "notes")

    user_text = "\n".join(parts) if parts else "(no structured info provided)"

    if lang == "zh":
        return base_instructions + "\n\n客户提供的信息如下（可能不完整）：\n" + user_text
    else:
        return base_instructions + "\n\nBuyer provided the following raw info (may be incomplete):\n" + user_text


# --- Simple knowledge base for AI chat (you can expand per client) ---
AI_KB = {
    "agency_en": """
SkyLane AI Studio is a small web studio focused on bilingual export websites for Chinese factories and trading companies.
We build:
- Factory profile sites (tools, hardware, manufacturing)
- Service / sourcing agency sites
- Simple e-commerce / B2C sites
Strengths: English content writing, Chinese/English bilingual layouts, SEO-friendly structure, WeChat H5 friendly pages.
Typical questions: MOQ info, how many pages, pricing packages, what content is needed from the factory, how long to finish a site.
    """,
    "agency_zh": """
SkyLane AI Studio（天航智网工作室）专注为中国工厂和外贸公司打造出口型双语网站。
我们主要制作：
- 工厂形象与产品网站（工具、五金、制造业等）
- 采购 / 外贸服务型网站
- 简单独立站类 B2C 网站
特点：中英文双语结构、英文文案优化、初级 SEO 布局、支持微信 H5 访问。
常见问题：需要哪些资料？起步价和不同套餐？制作周期？网站能否展示证书、质检流程、出运信息等。
    """
}


def build_ai_system_prompt(lang: str) -> str:
    """Create the system prompt for the AI chat assistant."""
    if lang == "zh":
        kb = AI_KB["agency_zh"]
        return f"""
你是 SkyLane AI Studio（天航智网工作室）的智能网站顾问助手。
请用简体中文回答用户问题，并结合以下背景信息简介：

{kb}

要求：
- 回答简洁清晰，适合工厂老板或外贸业务员阅读；
- 主动引导他们提供产品类别、目标市场、预算等信息；
- 不要谈论你是一个 AI 模型，只表现为网站顾问。
"""
    else:
        kb = AI_KB["agency_en"]
        return f"""
You are the smart website consultant for SkyLane AI Studio.
Always answer in clear, simple English unless the user explicitly uses Chinese.

Background:
{kb}

Guidelines:
- Be concise and practical (think like a sourcing / export website consultant).
- Encourage the user to share product category, target market, and budget.
- Do not say you are an AI model; act as a human consultant from SkyLane AI Studio.
"""


@app.route("/")
def index_pc():
    lang = get_lang(default="en")
    return render_template(
        "index_pc.html",
        projects=localize_projects(lang),
        packages=localize_packages(lang),
        lang=lang,
        is_wechat=False,
        enable_ai_chat=ENABLE_AI_CHAT,
        enable_smart_rfq=ENABLE_SMART_RFQ,
    )



@app.route("/wechat")
def index_wechat():
    # Default to Chinese for WeChat
    lang = get_lang(default="zh")
    return render_template(
        "index_wechat.html",
        projects=localize_projects(lang),
        packages=localize_packages(lang),
        lang=lang,
        is_wechat=True,
        enable_ai_chat=ENABLE_AI_CHAT,
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

@app.route("/dashboard")
def dashboard():
    """
    Export Command Center – internal style dashboard you can show to clients.
    Later you can clone this per client and plug in real analytics.
    """
    lang = get_lang(default="en")
    summary = build_dashboard_summary(lang)

    return render_template(
        "dashboard.html",
        lang=lang,
        is_wechat=False,          # PC-style layout
        enable_ai_chat=ENABLE_AI_CHAT,
        enable_smart_rfq=ENABLE_SMART_RFQ,
        summary=summary,
    )


@app.route("/api/smart-rfq", methods=["POST"])
def api_smart_rfq():
    """
    Smart RFQ expander.

    Expects JSON:
    {
      "company": "...",
      "buyer_name": "...",
      "email": "...",
      "country": "...",
      "product": "...",
      "quantity": "...",
      "incoterm": "...",
      "target_port": "...",
      "quality_level": "...",
      "certifications": "...",
      "packaging": "...",
      "notes": "...",
      "lang": "en" or "zh"
    }

    Returns JSON:
    {
      "rfq_en": "...",
      "rfq_zh": "..."
    }
    """
    if not ENABLE_SMART_RFQ:
        return jsonify({"error": "Smart RFQ is disabled"}), 403

    if os.environ.get("OPENAI_API_KEY") is None:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server"}), 500

    data = request.get_json(silent=True) or {}
    lang = data.get("lang", "en")
    lang = "zh" if lang and lang.lower() in ("zh", "cn", "zh-cn") else "en"

    # Build messages
    user_prompt = build_smart_rfq_prompt(data, lang)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an RFQ assistant. Follow the instructions carefully. "
                "Always output STRICT JSON with keys 'rfq_en' and 'rfq_zh'. "
                "No markdown, no backticks, no explanations, just JSON."
            )
        },
        {"role": "user", "content": user_prompt},
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # adjust model as needed
            messages=messages,
            max_tokens=800,
            temperature=0.4,
        )
        raw = completion.choices[0].message.content

        # Try to parse JSON result
        try:
            parsed = json.loads(raw)
            rfq_en = parsed.get("rfq_en", "").strip()
            rfq_zh = parsed.get("rfq_zh", "").strip()
        except Exception:
            # Fallback: treat entire output as English RFQ; produce a simple CN placeholder
            rfq_en = raw.strip()
            rfq_zh = (
                "（AI 输出未按 JSON 格式返回，这里为英文 RFQ 原文，请人工翻译或重新生成。）\n\n"
                + rfq_en
            )

        return jsonify({
            "rfq_en": rfq_en,
            "rfq_zh": rfq_zh
        })

    except Exception as e:
        return jsonify({"error": "Smart RFQ generation failed", "detail": str(e)}), 500


# === AI CHAT API ENDPOINT ===
@app.route("/api/ai-chat", methods=["POST"])
def api_ai_chat():
    """
    Expects JSON:
    {
      "messages": [
        {"role": "user", "content": "Hi, I need a factory website..."},
        {"role": "assistant", "content": "..."}  # optional history
      ],
      "lang": "en" or "zh"
    }
    Returns: {"reply": "..."} or error message.
    """
    if not ENABLE_AI_CHAT:
        return jsonify({"error": "AI chat is disabled"}), 403

    if os.environ.get("OPENAI_API_KEY") is None:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server"}), 500

    data = request.get_json(silent=True) or {}
    user_messages = data.get("messages", [])
    lang = data.get("lang", "en")
    lang = "zh" if lang in ("zh", "cn", "zh-cn") else "en"

    if not user_messages:
        return jsonify({"error": "No messages provided"}), 400

    system_prompt = build_ai_system_prompt(lang)

    # Build full message list for the model
    messages = [{"role": "system", "content": system_prompt}]
    for m in user_messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if not content:
            continue
        messages.append({"role": role, "content": content})

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",   # you can change model name if needed
            messages=messages,
            max_tokens=400,
            temperature=0.4,
        )
        reply = completion.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        # For production you may want to log the exception properly
        return jsonify({"error": "AI chat request failed", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
