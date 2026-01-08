import os
import json
from datetime import datetime
from urllib.parse import urlencode

from flask import Flask, render_template, request, flash, redirect, url_for, jsonify, session, g, Response
from werkzeug.middleware.proxy_fix import ProxyFix

from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_agency_key")  # Required for flash + sessions
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# -------------------------
# Language (default: Chinese)
# -------------------------
SUPPORTED_LANGS = {"zh", "en"}
DEFAULT_LANG = "zh"


def get_lang(default: str = DEFAULT_LANG) -> str:
    """
    Language selection order:
      1) ?lang= (en|zh)  -> persisted to session
      2) session['lang']
      3) default (zh)
    """
    raw = (request.args.get("lang") or session.get("lang") or default or DEFAULT_LANG).strip().lower()
    lang = "zh" if raw in ("zh", "cn", "zh-cn", "zh-hans") else "en"
    session["lang"] = lang
    g.lang = lang
    return lang


@app.context_processor
def inject_lang_helpers():
    def switch_lang_url(target_lang: str) -> str:
        tl = (target_lang or "").strip().lower()
        tl = "zh" if tl in ("zh", "cn", "zh-cn", "zh-hans") else "en"

        args = request.args.to_dict(flat=True)
        args["lang"] = tl
        qs = urlencode(args)
        return request.path + ("?" + qs if qs else "")

    _lang = getattr(g, "lang", session.get("lang", DEFAULT_LANG))
    return {
        "switch_lang_url": switch_lang_url,
        "lang": _lang,
        "support_policy": get_support_policy(_lang),
        "addons": localize_addons(_lang),
        "language_tiers": localize_language_tiers(_lang),
        "banking_service_note": BANKING_SERVICE_NOTE.get(_lang, BANKING_SERVICE_NOTE["en"]),
    }
# === OpenAI client ===
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Toggle AI chat per site (you can later turn this off for some clients)
ENABLE_AI_CHAT = True
ENABLE_SMART_RFQ = True

# --- Central Data for Projects (bilingual desc) ---
PROJECTS = [
    {
        "id": "factory",
        "title": "工厂B2B出口 - Factory B2B Export ",
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
        "title": "高端茶叶品牌 - Premium Tea Brand",
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
        "title": "地平线采购 - Horizon Sourcing",
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
        "title": "商店 - SkyLane Shop",
        "category": "E-Commerce",
        "desc": {
            "en": "Full B2C experience with shopping basket, user accounts, and checkout forms.",
            "zh": "完整的 B2C 独立站体验，包含购物车、用户账号和结算流程。"
        },
        "url": "https://shop.skylaneai.com/",
        "icon": "fa-cart-shopping"
    }
]


# -------------------------
# Cost Estimator: Language tiers (applies to all base website packages)
# Base package prices include CN + EN. Tier modifiers apply when more languages are required.
# -------------------------
LANGUAGE_TIERS = [
    {"id": "starter", "name": {"en": "Starter", "zh": "Starter"}, "max_lang": 3, "add_price": 0},
    {"id": "business", "name": {"en": "Business", "zh": "Business"}, "max_lang": 5, "add_price": 1500},
    {"id": "pro", "name": {"en": "Pro", "zh": "Pro"}, "max_lang": 10, "add_price": 3000},
]

BANKING_SERVICE_NOTE = {
    "en": "Banking / payment-related services are handled individually and quoted separately.",
    "zh": "银行/收款相关服务为单独评估与单独报价。"
}

# -------------------------
# Packages (realistic pricing)
# -------------------------
PACKAGES = [
    {
        "id": "pkg_factory",
        "project_id": "factory",
        "name": {"en": "Factory Export Starter Site", "zh": "工厂出口官网 · 标准版"},
        "price": {"en": "880元", "zh": "880元"},
        "delivery": {"en": "7–10 business days", "zh": "7–10 个工作日"},
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: Factory B2B export demo",
                "Up to 5 pages (Home, About, Products, QC, Contact)",
                "Bilingual EN / CN structure",
                "RFQ / inquiry form (to your email)"
            ],
            "zh": [
                "基于：工厂 B2B 出口演示网站",
                "最多 5 个页面（首页 / 公司介绍 / 产品列表 / 质量控制 / 联系我们）",
                "中英多语结构",
                "在线询盘表单（自动发送到您的邮箱）"
            ]
        },
        "excluded": {
            "en": [
                "Domain/hosting fees (billed by providers)",
                "Paid plugins/tools (CRM*, paid chat tools, etc.)",
                "Large-scale product data entry (can be quoted separately)"
            ],
            "zh": [
                "域名/主机费用（由供应商收取）",
                "第三方付费工具（CRM*、付费客服等）",
                "大批量产品录入（可单独报价）"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Smart RFQ** – expand buyer notes into a full RFQ**",
                "Optional: AI Export Assistant chat widget"
            ],
            "zh": [
                "可选：AI 智能 RFQ** – 把买家备注扩展为完整询盘",
                "可选：AI 出口助手聊天窗口"
            ]
        }
    },
    {
        "id": "pkg_sourcing",
        "project_id": "sourcing",
        "name": {"en": "Sourcing & Service Website", "zh": "一站式采购服务官网"},
        "price": {"en": "1280元", "zh": "1280元"},
        "delivery": {"en": "10–14 business days", "zh": "10–14 个工作日"},
        "recommended": True,
        "bullets": {
            "en": [
                "Based on: Horizon Sourcing demo",
                "Service pages: sourcing, QC, logistics and workflow",
                "Case studies / project timeline sections",
                "Multi-step RFQ** form for better lead quality"
            ],
            "zh": [
                "基于：Horizon Sourcing 演示站",
                "完整服务页面：采购 / 质检 / 物流及流程说明",
                "案例展示与项目时间线模块",
                "多步骤询盘表单，收集更完整项目信息"
            ]
        },
        "excluded": {
            "en": [
                "Domain/hosting fees (billed by providers)",
                "Paid analytics/CRM* subscriptions",
                "Custom ERP*** integrations (quoted separately)"
            ],
            "zh": [
                "域名/主机费用（由供应商收取）",
                "付费统计/CRM*订阅",
                "定制 ERP***/系统对接（需单独报价）"
            ]
        },
        "ai_options": {
            "en": [
                "Optional: AI Smart RFQ** for complex projects",
                "Optional: AI Export Assistant for 24/7 pre-sales questions",
                "Optional: AI Market Navigator (basic market suggestions)"
            ],
            "zh": [
                "可选：AI 智能 RFQ**（适合复杂项目）",
                "可选：AI 出口助手（7x24 小时预售问答）",
                "可选：AI 市场导航（基础市场建议）"
            ]
        }
    },
    {
        "id": "pkg_tea",
        "project_id": "tea",
        "name": {"en": "Brand Storytelling Site (Tea)", "zh": "品牌故事官网（以茶叶为例）"},
        "price": {"en": "980元", "zh": "980元"},
        "delivery": {"en": "7–10 business days", "zh": "7–10 个工作日"},
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: Premium Tea Brand",
                "Story-driven layout with photos and short videos",
                "Origin story, process, packaging and gallery sections",
                "Lead capture form for distributors and importers"
            ],
            "zh": [
                "基于：高端茶叶品牌演示站",
                "以图片与短视频为主的品牌故事布局",
                "原产地故事 / 制作过程 / 包装展示 / 图库模块",
                "用于收集代理商与进口商信息的表单"
            ]
        },
        "excluded": {
            "en": [
                "Professional photo/video shooting",
                "Domain/hosting fees (billed by providers)",
                "Paid ad campaigns (can be quoted separately)"
            ],
            "zh": [
                "专业拍摄（照片/视频）",
                "域名/主机费用（由供应商收取）",
                "广告投放服务（可单独报价）"
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
        "name": {"en": "Export E-Commerce Shop", "zh": "出口型独立商城"},
        "price": {"en": "1980元", "zh": "1980元"},
        "delivery": {"en": "3–5 weeks (depends on catalog size)", "zh": "3–5 周（取决于产品数量）"},
        "recommended": False,
        "bullets": {
            "en": [
                "Based on: SkyLane Shop (basket + login + checkout)",
                "Product catalog, shopping cart and demo checkout flow",
                "User account area with sample orders",
                "Ready for payment integration (Stripe/PayPal/bank transfer)"
            ],
            "zh": [
                "基于：SkyLane 商城演示站（含购物车 / 登录 / 结算）",
                "产品目录、购物车及演示结算流程",
                "带示例订单的用户中心页面",
                "可扩展接入支付（Stripe/PayPal/银行转账）"
            ]
        },
        "excluded": {
            "en": [
                "Payment provider fees and business verification",
                "Complex shipping/tax automation (quoted separately)",
                "Large-scale product import/ERP*** sync (quoted separately)"
            ],
            "zh": [
                "支付平台手续费及商户资质认证",
                "复杂运费/税务自动化（需单独报价）",
                "大规模商品导入/ERP*** 同步（需单独报价）"
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

# -------------------------
# Dashboard demo data
# -------------------------
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
        "status": "online",
        "leads_30d": 7,
        "ai_rfq": True,
        "ai_chat": False,
    },
    {
        "id": "shop",
        "name_en": "SkyLane Shop (B2C)",
        "name_zh": "SkyLane B2C 商城",
        "url": "https://shop.skylaneai.com/",
        "type": "E-Commerce",
        "status": "online",
        "leads_30d": 9,
        "ai_rfq": False,
        "ai_chat": True,
    },
]

LANGUAGE_TIERS = [
    {"id": "starter", "name": {"en": "Starter", "zh": "Starter"}, "max_lang": 3, "add_price": 0},
    {"id": "business", "name": {"en": "Business", "zh": "Business"}, "max_lang": 5, "add_price": 1500},
    {"id": "pro", "name": {"en": "Pro", "zh": "Pro"}, "max_lang": 10, "add_price": 3000},
]

BANKING_SERVICE_NOTE = {
    "en": "Banking / payment-related services are handled individually and quoted separately.",
    "zh": "银行/收款相关服务为单独评估与单独报价。"
}


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
    total_sites = len(DASHBOARD_SITES)
    total_leads_30d = sum(s.get("leads_30d", 0) for s in DASHBOARD_SITES)
    ai_enabled_sites = sum(1 for s in DASHBOARD_SITES if s.get("ai_rfq") or s.get("ai_chat"))

    sites_localized = []
    for site in DASHBOARD_SITES:
        s = dict(site)
        s["display_name"] = site["name_zh"] if lang == "zh" else site["name_en"]

        ai_labels = []
        if site.get("ai_rfq"):
            ai_labels.append("AI Smart RFQ**" if lang == "en" else "AI 智能 RFQ**")
        if site.get("ai_chat"):
            ai_labels.append("AI Chat" if lang == "en" else "AI 在线咨询")
        s["ai_label_str"] = ", ".join(ai_labels) if ai_labels else ("None" if lang == "en" else "暂无")

        sites_localized.append(s)

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


# -------------------------
# Add-ons (Multilingual) & Support Policy (for templates)
# -------------------------
ADDONS = [
    {
        "id": "addon_domain",
        "name": {"en": "Website address", "zh": "网站地址"},
        "price": "150元 / year",
        "desc": {
            "en": "The price is not guaranteed and depends on the domain.",
            "zh": "价格不保证，取决于域名。",
        },
    },
    {
        "id": "addon_seo",
        "name": {"en": "Search Engine SEO Setup", "zh": "搜索引擎 SEO 基础设置"},
        "price": "250元",
        "desc": {
            "en": "On-page SEO essentials: titles/meta, site structure, sitemap, and indexing guidance (no ranking guarantee). Also covers basic performance and crawlability checks (canonical/robots) to reduce indexing issues.",
            "zh": "站内 SEO 基础设置：标题/描述、站点结构、站点地图与收录指引（不承诺排名）。同时包含基础性能与可抓取性检查（canonical/robots），以减少收录与索引问题。",
        },
    },
    {
        "id": "addon_copywriting",
        "name": {"en": "Professional Language Copywriting", "zh": "专业语言文案撰写"},
        "price": "200元",
        "desc": {
            "en": "Conversion-focused, polished copy for key pages (based on your materials). Includes tone and terminology alignment plus one revision round to match your brand voice.",
            "zh": "为关键页面提供更地道、更具转化力的专业文案（基于你提供的资料）。包含语气与行业用语统一，并提供 1 轮修改以贴合您的品牌风格。",
        },
    },
    {
        "id": "addon_messaging",
        "name": {"en": "Website Messaging + Seller Inbox Dashboard", "zh": "网站站内消息 + 商家后台收件箱"},
        "price": "200元",
        "desc": {
            "en": "Visitor can send a message from the website (name + email + message). Seller can view messages and reply in a dashboard (inbox + conversation thread).",
            "zh": "访客可在网站发送消息（姓名/邮箱/内容）。商家可在后台仪表盘查看与回复（收件箱 + 对话线程）。",
        },
    },
        {
        "id": "addon_product_manager",
        "name": {"en": "Product Manager Dashboard", "zh": "商品管理后台"},
        "price": "450元",
        "desc": {
            "en": "Seller can add, edit, hide/remove products and update prices in a secure dashboard. Product data is stored in a database and updates sync to the storefront immediately (basic catalog management; no inventory/ERP).",
            "zh": "商家可在安全后台新增/编辑/下架商品并修改价格。商品数据存入数据库，前台展示实时同步更新（基础商品目录管理，不含库存/ERP）。",
        },
    },
]


def localize_addons(lang: str):
    lang = "zh" if (lang or "").lower().startswith("zh") else "en"
    items = []
    for a in ADDONS:
        items.append(
            {
                "id": a["id"],
                "display_name": a["name"][lang],
                "price": a["price"],
                "display_desc": a["desc"][lang],
            }
        )
    return items

def localize_language_tiers(lang: str):
    lang = "zh" if (lang or "").lower().startswith("zh") else "en"
    items = []
    for t in LANGUAGE_TIERS:
        items.append({
            "id": t["id"],
            "display_name": t["name"][lang],
            "max_lang": t["max_lang"],
            "add_price": t["add_price"],
        })
    return items

def localize_language_tiers(lang: str):
    lang = "zh" if (lang or "").lower().startswith("zh") else "en"
    return [{
        "id": t["id"],
        "display_name": t["name"][lang],
        "max_lang": t["max_lang"],
        "add_price": t["add_price"],
    } for t in LANGUAGE_TIERS]


def get_support_policy(lang: str):
    lang = "zh" if (lang or "").lower().startswith("zh") else "en"
    if lang == "zh":
        return {
            "hours": "周一-周三 09:00-12:00<br>周四-周五 09:00-18:00",
            "missed_calls": "未接来电：1 个工作日内回拨",
            "browsing": "支持手机端与电脑端访问",
            "multi_lang": "Starter 3 种语言<br>Business 5 种语言<br>Pro 10 种语言",
            "contact_email": "可选：展示公司邮箱（如 info@skylaneia.com）",
        }
    return {
        "hours": "Mon–Wed 09:00–12:00; <br>Thu–Fri 09:00–18:00",
        "missed_calls": "Missed calls: call back within 1 business day",
        "browsing": "Mobile and PC browsing supported",
        "multi_lang": "Starter 3; <br>Business 5; <br>Pro 10 languages",
        "contact_email": "Optional: display your company email (e.g., info@skylaneia.com)",
    }


def localize_projects(lang: str):
    localized = []
    for p in PROJECTS:
        p_copy = dict(p)
        desc = p_copy.get("desc")
        if isinstance(desc, dict):
            p_copy["desc"] = desc.get(lang, desc.get("en"))
        localized.append(p_copy)
    return localized


def localize_packages(lang: str):
    project_map = {p["id"]: p for p in PROJECTS}
    localized = []

    for pkg in PACKAGES:
        p = dict(pkg)

        # Localize
        def pick(d, fallback=""):
            if isinstance(d, dict):
                return d.get(lang, d.get("en")) or fallback
            return d or fallback

        p["display_name"] = pick(p.get("name"), "")
        p["display_price"] = pick(p.get("price"), "")
        p["display_delivery"] = pick(p.get("delivery"), "")
        p["display_bullets"] = pick(p.get("bullets"), []) or []
        p["display_excluded"] = pick(p.get("excluded"), []) or []
        p["display_ai_options"] = pick(p.get("ai_options"), []) or []

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
    if lang == "zh":
        base_instructions = """
你是一名外贸手工具/一般工业品的资深业务员，擅长把客户的原始需求整理成结构化的询盘/报价单（RFQ**）。
请根据下面信息，生成：

1) 一份【英文】RFQ**，结构清晰、适合发送给中国工厂或外贸公司的业务员；
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

1) A clear ENGLISH RFQ** suitable to send to Chinese factories or trading companies.
2) A CHINESE version of the same RFQ** for internal use or for factories.

Requirements:
- Use clear sections (e.g., Buyer info, Product spec, Quality, Packaging, Incoterms, QC, Others).
- No email greetings (no “Dear Sir/Madam”); start directly with the RFQ** sections.
- You may reasonably fill in common missing details, marking them as “to be confirmed”.
Return the result as JSON with two string fields: rfq_en and rfq_zh.
"""

    parts = []

    def add_line(label: str, key: str):
        value = (data.get(key) or "").strip()
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
        header = "客户提供的信息如下（可能不完整）：\n"
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
        header = "Buyer provided the following raw info (may be incomplete):\n"

    user_text = "\n".join(parts) if parts else "(no structured info provided)"
    return base_instructions + "\n\n" + header + user_text


AI_KB = {
    "agency_en": """
SkyLane AI Studio is a small web studio focused on multilingual export websites for Chinese factories and trading companies.
We build:
- Factory profile sites (tools, hardware, manufacturing)
- Service / sourcing agency sites
- Simple e-commerce / B2C sites
Strengths: English content writing, Chinese/English multilingual layouts, SEO-friendly structure, WeChat H5 friendly pages.
Typical questions: MOQ info, how many pages, pricing packages, what content is needed from the factory, how long to finish a site.
    """,
    "agency_zh": """
SkyLane AI Studio（天航智网工作室）专注为中国工厂和外贸公司打造出口型多语言网站。
我们主要制作：
- 工厂形象与产品网站（工具、五金、制造业等）
- 采购 / 外贸服务型网站
- 简单独立站类 B2C 网站
特点：多语言结构、英文文案优化、基础 SEO 布局、支持微信 H5 访问。
常见问题：需要哪些资料？起步价和不同套餐？制作周期？网站能否展示证书、质检流程、出运信息等。
    """
}


def build_ai_system_prompt(lang: str) -> str:
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


# -------------------------
# Routes
# -------------------------
@app.get("/")
def index_pc():
    lang = get_lang(default=DEFAULT_LANG)
    return render_template(
        "index_pc.html",
        projects=localize_projects(lang),
        support_policy=get_support_policy(lang),
        addons=localize_addons(lang),
        packages=localize_packages(lang),
        lang=lang,
        is_wechat=False,
        enable_ai_chat=ENABLE_AI_CHAT,
        enable_smart_rfq=ENABLE_SMART_RFQ,
    )


@app.get("/wechat")
def index_wechat():
    # Default to Chinese for WeChat, but can be switched by ?lang=en
    lang = get_lang(default="zh")
    return render_template(
        "index_wechat.html",
        projects=localize_projects(lang),
        support_policy=get_support_policy(lang),
        addons=localize_addons(lang),
        packages=localize_packages(lang),
        lang=lang,
        is_wechat=True,
        enable_ai_chat=ENABLE_AI_CHAT,
        enable_smart_rfq=ENABLE_SMART_RFQ,
    )


@app.get("/dashboard")
def dashboard():
    lang = get_lang(default=DEFAULT_LANG)
    summary = build_dashboard_summary(lang)
    return render_template(
        "dashboard.html",
        lang=lang,
        is_wechat=False,
        enable_ai_chat=ENABLE_AI_CHAT,
        enable_smart_rfq=ENABLE_SMART_RFQ,
        summary=summary,
    )


@app.post("/contact")
def contact_submit():
    name = request.form.get("name") or ""
    lang = request.form.get("lang") or get_lang(default=DEFAULT_LANG)

    if lang == "zh":
        flash(f"谢谢 {name}！您的需求已经发送，我会在24小时内回复。", "success")
    else:
        flash(f"Thanks {name}! Your inquiry has been sent. I will reply within 24 hours.", "success")

    return redirect(url_for("index_pc", lang=lang))


# -------------------------
# Legal / compliance pages
# -------------------------
@app.get("/privacy")
def privacy():
    lang = get_lang(default=DEFAULT_LANG)
    return render_template("privacy.html", lang=lang, is_wechat=False)


@app.get("/terms")
def terms():
    lang = get_lang(default=DEFAULT_LANG)
    return render_template("terms.html", lang=lang, is_wechat=False)


@app.get("/cookies")
def cookies():
    lang = get_lang(default=DEFAULT_LANG)
    return render_template("cookies.html", lang=lang, is_wechat=False)


# -------------------------
# robots + sitemap (SEO basics)
# -------------------------
@app.get("/robots.txt")
def robots_txt():
    sitemap_url = url_for("sitemap_xml", _external=True)
    body = "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
        ""
    ])
    return Response(body, mimetype="text/plain")


@app.get("/sitemap.xml")
def sitemap_xml():
    pages = ["index_pc", "dashboard", "privacy", "terms", "cookies"]
    urls = []

    for endpoint in pages:
        for lng in ("zh", "en"):
            loc = url_for(endpoint, _external=True, lang=lng)
            urls.append((loc, datetime.utcnow().date().isoformat()))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{loc}</loc>")
        xml.append(f"    <lastmod>{lastmod}</lastmod>")
        xml.append("  </url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


@app.get("/health")
def health():
    return {"ok": True}


# -------------------------
# APIs
# -------------------------
@app.post("/api/smart-rfq")
def api_smart_rfq():
    if not ENABLE_SMART_RFQ:
        return jsonify({"error": "Smart RFQ is disabled"}), 403

    if os.environ.get("OPENAI_API_KEY") is None:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server"}), 500

    data = request.get_json(silent=True) or {}
    lang = data.get("lang", "en")
    lang = "zh" if (lang and str(lang).lower() in ("zh", "cn", "zh-cn", "zh-hans")) else "en"

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
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=900,
            temperature=0.4,
        )
        raw = (completion.choices[0].message.content or "").strip()

        try:
            parsed = json.loads(raw)
            rfq_en = (parsed.get("rfq_en") or "").strip()
            rfq_zh = (parsed.get("rfq_zh") or "").strip()
        except Exception:
            rfq_en = raw
            rfq_zh = "（AI 输出未按 JSON 格式返回，以下为英文原文，请人工翻译或重新生成。）\n\n" + rfq_en

        return jsonify({"rfq_en": rfq_en, "rfq_zh": rfq_zh})

    except Exception as e:
        return jsonify({"error": "Smart RFQ generation failed", "detail": str(e)}), 500


@app.post("/api/ai-chat")
def api_ai_chat():
    if not ENABLE_AI_CHAT:
        return jsonify({"error": "AI chat is disabled"}), 403

    if os.environ.get("OPENAI_API_KEY") is None:
        return jsonify({"error": "OPENAI_API_KEY is not set on the server"}), 500

    data = request.get_json(silent=True) or {}
    user_messages = data.get("messages", [])
    lang = data.get("lang", "en")
    lang = "zh" if str(lang).lower() in ("zh", "cn", "zh-cn", "zh-hans") else "en"

    if not user_messages:
        return jsonify({"error": "No messages provided"}), 400

    system_prompt = build_ai_system_prompt(lang)

    messages = [{"role": "system", "content": system_prompt}]
    for m in user_messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if content:
            messages.append({"role": role, "content": content})

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=450,
            temperature=0.4,
        )
        reply = completion.choices[0].message.content or ""
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": "AI chat request failed", "detail": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
