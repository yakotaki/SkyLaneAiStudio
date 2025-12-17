window.SkyLaneSmartRFQ = (function () {
    let state = {
        lang: "en",
        busy: false
    };

    function init(config) {
        state.lang = (config && config.lang) || "en";
    }

    function setStatus(text) {
        const el = document.getElementById("smartRfqStatus");
        if (el) {
            el.textContent = text;
        }
    }

    function showResult(enText, zhText) {
        const wrap = document.getElementById("smartRfqResult");
        const enBox = document.getElementById("smartRfqEn");
        const zhBox = document.getElementById("smartRfqZh");

        if (!wrap || !enBox || !zhBox) return;

        enBox.value = enText || "";
        zhBox.value = zhText || "";
        wrap.style.display = "flex";
    }

    async function submit() {
        if (state.busy) return false;

        const form = document.getElementById("smartRfqForm");
        if (!form) return false;

        const formData = new FormData(form);
        const payload = {
            lang: state.lang
        };

        for (let [key, value] of formData.entries()) {
            payload[key] = value.trim();
        }

        // simple validation: product at least
        if (!payload.product) {
            if (state.lang === "zh") {
                setStatus("请至少填写“产品方向”，例如：套筒组套、手工具等。");
            } else {
                setStatus("Please at least fill in 'Product focus' (e.g. socket sets, tools, etc.).");
            }
            return false;
        }

        state.busy = true;
        if (state.lang === "zh") {
            setStatus("AI 正在生成结构化 RFQ，请稍候...");
        } else {
            setStatus("AI is generating a structured RFQ, please wait...");
        }

        try {
            const resp = await fetch("/api/smart-rfq", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();
            state.busy = false;

            if (data.error) {
                if (state.lang === "zh") {
                    setStatus("生成失败：" + data.error);
                } else {
                    setStatus("Generation failed: " + data.error);
                }
                return false;
            }

            showResult(data.rfq_en || "", data.rfq_zh || "");

            if (state.lang === "zh") {
                setStatus("已生成 RFQ，可复制到邮件或聊天工具中使用。");
            } else {
                setStatus("RFQ generated. You can copy it into your email or chat with factories.");
            }

        } catch (e) {
            state.busy = false;
            if (state.lang === "zh") {
                setStatus("网络或服务器错误，请稍后重试。");
            } else {
                setStatus("Network or server error, please try again later.");
            }
        }

        return false; // prevent real form submit
    }

    return {
        init,
        submit
    };
})();
