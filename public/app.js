document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-query-form");
    const queryInput = document.getElementById("user-query-input");
    const submitBtn = document.getElementById("submit-query-btn");
    const messagesWrapper = document.getElementById("messages-list-wrapper");
    const welcomeContainer = document.getElementById("welcome-container");
    const examplesGrid = document.getElementById("example-questions-grid");
    const chatHistoryWrapper = document.getElementById("chat-history-wrapper");

    // Initialize Page Configurations
    async function loadConfig() {
        try {
            const res = await fetch("/api/config");
            if (!res.ok) throw new Error("Config fetch failed");
            
            const data = await res.json();
            
            // Render example question cards
            if (data.example_questions && data.example_questions.length > 0) {
                examplesGrid.innerHTML = "";
                data.example_questions.forEach(q => {
                    const card = document.createElement("div");
                    card.className = "suggestion-card";
                    card.innerHTML = `
                        <span>"${q}"</span>
                        <i class="fa-solid fa-arrow-right"></i>
                    `;
                    card.addEventListener("click", () => {
                        queryInput.value = q;
                        submitQuery(q);
                    });
                    examplesGrid.appendChild(card);
                });
            }
        } catch (err) {
            console.error("Error loading config:", err);
            // Load hardcoded fallback example cards if server is slow or fails
            examplesGrid.innerHTML = `
                <div class="suggestion-card" id="fallback-q1">
                    <span>"What is the expense ratio of HDFC Small Cap Fund?"</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
                <div class="suggestion-card" id="fallback-q2">
                    <span>"Who is the fund manager of HDFC Mid-Cap Opportunities?"</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
                <div class="suggestion-card" id="fallback-q3">
                    <span>"What exit load is applicable to HDFC Defence Fund?"</span>
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
            `;
            
            document.getElementById("fallback-q1").addEventListener("click", () => {
                queryInput.value = "What is the expense ratio of HDFC Small Cap Fund?";
                submitQuery("What is the expense ratio of HDFC Small Cap Fund?");
            });
            document.getElementById("fallback-q2").addEventListener("click", () => {
                queryInput.value = "Who is the fund manager of HDFC Mid-Cap Opportunities?";
                submitQuery("Who is the fund manager of HDFC Mid-Cap Opportunities?");
            });
            document.getElementById("fallback-q3").addEventListener("click", () => {
                queryInput.value = "What exit load is applicable to HDFC Defence Fund?";
                submitQuery("What exit load is applicable to HDFC Defence Fund?");
            });
        }
    }

    // Scroll chat history to bottom
    function scrollToBottom() {
        chatHistoryWrapper.scrollTop = chatHistoryWrapper.scrollHeight;
    }

    // Show Typing Indicator
    function showTypingIndicator() {
        const row = document.createElement("div");
        row.className = "message-row assistant";
        row.id = "typing-indicator-row";
        row.innerHTML = `
            <div class="message-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        messagesWrapper.appendChild(row);
        scrollToBottom();
    }

    // Remove Typing Indicator
    function removeTypingIndicator() {
        const row = document.getElementById("typing-indicator-row");
        if (row) {
            row.remove();
        }
    }

    // Append Message Bubble
    function appendMessage(sender, text, intent = "FACTUAL", chunks = []) {
        // Hide welcome panel once a message is exchange
        if (welcomeContainer.style.display !== "none") {
            welcomeContainer.style.display = "none";
        }

        const row = document.createElement("div");
        row.className = `message-row ${sender === "user" ? "user" : "assistant"}`;
        
        let bubbleContent = text;
        let citationHTML = "";
        let footerHTML = "";

        if (sender === "assistant") {
            let cleanedText = text;
            let citationUrl = null;
            let lastUpdatedDate = null;

            // 1. Extract Groww source link if present
            const growwMatch = cleanedText.match(/(?:\[Source:\s*)?(https?:\/\/(?:www\.)?groww\.in\/[^\s)\]]+)(?:\s*\])?/i);
            if (growwMatch) {
                citationUrl = growwMatch[1];
                cleanedText = cleanedText.replace(growwMatch[0], "").trim();
            }

            // 2. Extract date footer if present in text
            const footerMatch = cleanedText.match(/\n\nLast updated from sources:\s*([^\n]+)/i);
            if (footerMatch) {
                lastUpdatedDate = footerMatch[1];
                cleanedText = cleanedText.replace(footerMatch[0], "").trim();
            } else if (chunks && chunks.length > 0) {
                // Fetch date from chunks if not in the response text directly
                lastUpdatedDate = chunks[0]?.metadata?.last_updated_date;
                if (lastUpdatedDate && lastUpdatedDate.includes("T")) {
                    lastUpdatedDate = lastUpdatedDate.split("T")[0];
                }
            }

            // 3. Format lines
            bubbleContent = cleanedText.replace(/\n/g, "<br>");

            // 4. Build Citation Badge
            if (citationUrl) {
                citationHTML = `
                    <div class="citation-container">
                        <a href="${citationUrl}" target="_blank" rel="noopener noreferrer" class="citation-badge">
                            <i class="fa-solid fa-up-right-from-square"></i> View Source Factsheet
                        </a>
                    </div>
                `;
            }

            // 5. Build Date Footer
            if (lastUpdatedDate) {
                footerHTML = `
                    <div class="message-footer">
                        <i class="fa-solid fa-clock"></i> Updated: ${lastUpdatedDate}
                    </div>
                `;
            }
        }

        // Apply special style if advisory refusal
        const isRefusalClass = (sender === "assistant" && intent === "ADVISORY") ? " refusal" : "";

        row.innerHTML = `
            <div class="message-bubble${isRefusalClass}">
                <div class="message-text">${bubbleContent}</div>
                ${citationHTML}
                ${footerHTML}
            </div>
        `;
        
        messagesWrapper.appendChild(row);
        scrollToBottom();
    }

    // Submit user query to backend API
    async function submitQuery(query) {
        if (!query.trim()) return;

        // Add user bubble
        appendMessage("user", query);
        
        // Prepare UI state
        queryInput.value = "";
        queryInput.disabled = true;
        submitBtn.disabled = true;
        
        // Show loading indicator
        showTypingIndicator();

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: query })
            });

            removeTypingIndicator();

            if (!res.ok) {
                throw new Error("Chat request failed");
            }

            const data = await res.json();
            
            // Route response logic
            const responseText = data.response || "Factual information service is temporarily unavailable.";
            appendMessage("assistant", responseText, data.intent, data.chunks);

        } catch (err) {
            console.error("Error in chat transaction:", err);
            removeTypingIndicator();
            appendMessage(
                "assistant", 
                "An unexpected network error occurred. Please make sure your server connection is active.", 
                "ADVISORY"
            );
        } finally {
            queryInput.disabled = false;
            submitBtn.disabled = false;
            queryInput.focus();
        }
    }

    // Form Event Listeners
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        submitQuery(query);
    });

    // Run Initial Config Fetch
    loadConfig();
});
