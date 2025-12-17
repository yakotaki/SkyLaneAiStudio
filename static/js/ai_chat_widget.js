window.SkyLaneAIChat = (function () {
    let state = {
        lang: "en",
        messages: []
    };

    function init(config) {
        state.lang = config.lang || "en";
        const input = document.getElementById("aiChatInput");
        if (input) {
            input.addEventListener("keydown", function (e) {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                }
            });
        }
    }

    function toggleWindow() {
        const win = document.getElementById("aiChatWindow");
        if (!win) return;
        const isVisible = win.style.display === "flex";
        win.style.display = isVisible ? "none" : "flex";
    }

    function appendMessage(role, text) {
        const body = document.getElementById("aiChatBody");
        if (!body) return;

        const msgWrapper = document.createElement("div");
        msgWrapper.className = "ai-msg " + (role === "user" ? "ai-user" : "ai-bot");

        const bubble = document.createElement("div");
        bubble.className = "ai-msg-bubble";
        bubble.textContent = text;

        msgWrapper.appendChild(bubble);
        body.appendChild(msgWrapper);
        body.scrollTop = body.scrollHeight;
    }

    function appendLoader() {
        const body = document.getElementById("aiChatBody");
        if (!body) return;
        const loader = document.createElement("div");
        loader.className = "ai-chat-loader";
        loader.id = "aiChatLoader";
        loader.textContent = state.lang === "zh"
            ? "正在思考合适的建议..."
            : "Thinking about the best suggestion...";
        body.appendChild(loader);
        body.scrollTop = body.scrollHeight;
    }

    function removeLoader() {
        const loader = document.getElementById("aiChatLoader");
        if (loader && loader.parentNode) {
            loader.parentNode.removeChild(loader);
        }
    }

    async function send() {
        const input = document.getElementById("aiChatInput");
        if (!input) return;
        const text = input.value.trim();
        if (!text) return;

        // show user message
        appendMessage("user", text);
        state.messages.push({ role: "user", content: text });
        input.value = "";
        appendLoader();

        try {
            const response = await fetch("/api/ai-chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    messages: state.messages,
                    lang: state.lang
                })
            });

            const data = await response.json();
            removeLoader();

            if (data.error) {
                appendMessage("assistant", data.error);
                return;
            }

            if (data.reply) {
                appendMessage("assistant", data.reply);
                state.messages.push({ role: "assistant", content: data.reply });
            }
        } catch (err) {
            removeLoader();
            appendMessage(
                "assistant",
                state.lang === "zh"
                    ? "抱歉，AI 服务暂时不可用，请稍后再试。"
                    : "Sorry, the AI service is temporarily unavailable. Please try again later."
            );
        }
    }

    return {
        init,
        toggleWindow,
        send
    };
})();
