/**
 * static/js/chat.js — Active Chat Interface Controller
 * ====================================================
 * Coordinates AJAX fetching, event streaming, folder views, search,
 * likes/dislikes, drag-and-drop file mock actions, and speech triggers.
 */

document.addEventListener("DOMContentLoaded", () => {
    // ── DOM Binding ──────────────────────────────────────────────────────────
    const sidebarList = document.getElementById("conversation-history-list");
    const chatLog = document.getElementById("conversation-message-log");
    const scrollBox = document.getElementById("chat-messages-scroll-box");
    const emptyWelcome = document.getElementById("empty-state-welcome");
    const chatForm = document.getElementById("chat-input-form");
    const promptInput = document.getElementById("chat-prompt-input");
    const typingIndicator = document.getElementById("typing-indicator");
    const statusIndicator = document.getElementById("model-status-indicator");
    const newChatBtn = document.getElementById("new-chat-btn");
    const chatSearch = document.getElementById("chat-search");
    const streamCancelRow = document.getElementById("stream-cancel-controls");
    const stopGenBtn = document.getElementById("stop-generation-btn");
    
    const voiceBtn = document.getElementById("voice-input-btn");
    const ttsBtn = document.getElementById("tts-feedback-btn");
    const exportBtn = document.getElementById("export-chat-btn");
    const clearBtn = document.getElementById("clear-chat-btn");
    const modelMetaName = document.getElementById("meta-model-name");
    const fileSelector = document.getElementById("file-selector");
    const dragOverlay = document.getElementById("drag-drop-zone");

    // ── Internal States ──────────────────────────────────────────────────────
    let activeConversationId = ACTIVE_CONVERSATION_ID || null;
    let activeStream = null;
    let activeTTSUtterance = null;
    const voiceManager = new VoiceManager();

    // ── Initialize Marked Markdown Options (with CDN fallback safety) ─────────
    if (typeof marked !== 'undefined' && marked.setOptions) {
        let highlightConfig = {};
        if (typeof hljs !== 'undefined' && hljs.getLanguage) {
            highlightConfig = {
                highlight: function(code, lang) {
                    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                    return hljs.highlight(code, { language }).value;
                },
                langPrefix: 'hljs language-'
            };
        }
        marked.setOptions({
            ...highlightConfig,
            breaks: true
        });
    }

    // Run startup processes
    loadConversations();
    checkEngineStatus();
    setupTextareaAutoResize();
    setupDragAndDrop();

    // ── Chat Listing ─────────────────────────────────────────────────────────
    function loadConversations(selectId = null) {
        fetch("/api/conversations")
            .then(res => res.json())
            .then(data => {
                sidebarList.innerHTML = "";
                if (data.length === 0) {
                    sidebarList.innerHTML = '<div class="text-center py-4 text-muted">No active chats.</div>';
                    showWelcome();
                    return;
                }

                // Render Pinned chats first, then general list
                const pinned = data.filter(c => c.is_pinned);
                const general = data.filter(c => !c.is_pinned);

                if (pinned.length > 0) {
                    const pinHeader = document.createElement("div");
                    pinHeader.className = "history-section-header text-muted font-bold mt-2 mb-1 px-2";
                    pinHeader.style.fontSize = "0.75rem";
                    pinHeader.innerText = "📌 PINNED CHATS";
                    sidebarList.appendChild(pinHeader);
                    
                    pinned.forEach(c => renderConversationItem(c));
                }

                if (general.length > 0) {
                    const genHeader = document.createElement("div");
                    genHeader.className = "history-section-header text-muted font-bold mt-3 mb-1 px-2";
                    genHeader.style.fontSize = "0.75rem";
                    genHeader.innerText = "💬 ALL CONVERSATIONS";
                    sidebarList.appendChild(genHeader);
                    
                    general.forEach(c => renderConversationItem(c));
                }

                // Auto-load target selection
                const targetId = selectId || activeConversationId;
                if (targetId) {
                    setActiveConversation(targetId);
                } else if (data.length > 0) {
                    setActiveConversation(data[0].id);
                }
            })
            .catch(() => {
                sidebarList.innerHTML = '<div class="text-center py-4 text-danger">Error loading history.</div>';
            });
    }

    function renderConversationItem(c) {
        const item = document.createElement("div");
        item.className = `conversation-item ${c.id === activeConversationId ? 'active' : ''} ${c.is_pinned ? 'pinned-state' : ''}`;
        item.dataset.id = c.id;

        item.innerHTML = `
            <i class="fa-solid fa-message chat-icon"></i>
            <div class="conversation-title-wrapper">
                <span class="title-text">${escapeHtml(c.title)}</span>
            </div>
            <div class="item-actions">
                <button class="action-btn pin-btn" title="Pin / Unpin"><i class="fa-solid fa-thumbtack"></i></button>
                <button class="action-btn rename-btn" title="Rename"><i class="fa-solid fa-pen"></i></button>
                <button class="action-btn delete delete-btn" title="Delete"><i class="fa-solid fa-trash"></i></button>
            </div>
        `;

        // Click Event -> Switch Active chat
        item.addEventListener("click", (e) => {
            if (e.target.closest(".action-btn")) return;
            setActiveConversation(c.id);
        });

        // Pin Button Toggle
        item.querySelector(".pin-btn").addEventListener("click", () => {
            fetch(`/api/conversations/${c.id}/pin`, { method: "POST" })
                .then(res => res.json())
                .then(() => loadConversations(c.id));
        });

        // Rename Focus Handler
        item.querySelector(".rename-btn").addEventListener("click", () => {
            const titleWrap = item.querySelector(".conversation-title-wrapper");
            const textSpan = item.querySelector(".title-text");
            const oldTitle = textSpan.innerText;

            const input = document.createElement("input");
            input.type = "text";
            input.className = "rename-input";
            input.value = oldTitle;
            titleWrap.replaceChild(input, textSpan);
            input.focus();

            function saveRename() {
                const newTitle = input.value.trim();
                if (newTitle && newTitle !== oldTitle) {
                    fetch(`/api/conversations/${c.id}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ title: newTitle })
                    }).then(() => {
                        textSpan.innerText = newTitle;
                        titleWrap.replaceChild(textSpan, input);
                        loadConversations(c.id);
                    });
                } else {
                    titleWrap.replaceChild(textSpan, input);
                }
            }

            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") saveRename();
                if (e.key === "Escape") titleWrap.replaceChild(textSpan, input);
            });
            input.addEventListener("blur", saveRename);
        });

        // Delete Handler
        item.querySelector(".delete-btn").addEventListener("click", () => {
            if (confirm("Delete this conversation?")) {
                fetch(`/api/conversations/${c.id}`, { method: "DELETE" })
                    .then(() => {
                        if (activeConversationId === c.id) {
                            activeConversationId = null;
                        }
                        loadConversations();
                    });
            }
        });

        sidebarList.appendChild(item);
    }

    // ── Active Conversation Management ───────────────────────────────────────
    function setActiveConversation(convId) {
        activeConversationId = convId;
        
        // Highlight active sidebar item
        document.querySelectorAll(".conversation-item").forEach(el => {
            el.classList.remove("active");
            if (el.dataset.id === convId) el.classList.add("active");
        });

        chatLog.innerHTML = '<div class="text-center py-5 text-muted"><i class="fa-solid fa-spinner fa-spin"></i> Loading context...</div>';
        emptyWelcome.classList.add("hidden");

        fetch(`/api/conversations/${convId}`)
            .then(res => res.json())
            .then(data => {
                chatLog.innerHTML = "";
                if (!data.messages || data.messages.length === 0) {
                    showWelcome();
                    return;
                }
                
                data.messages.forEach(msg => appendMessageBubble(msg.role, msg.content, msg.id, msg.rating));
                scrollToBottom();
            });
    }

    function showWelcome() {
        chatLog.innerHTML = "";
        emptyWelcome.classList.remove("hidden");
    }

    // ── Bubble Rendering ─────────────────────────────────────────────────────
    function appendMessageBubble(role, content, msgId = null, rating = 0) {
        emptyWelcome.classList.add("hidden");
        const block = document.createElement("div");
        block.className = `message-block animate-fade-in ${role}`;
        if (msgId) block.dataset.msgId = msgId;

        const isUser = role === "user";
        const bubbleHtml = isUser ? `
            <div class="message-bubble-content">
                <div class="bubble-payload">${escapeHtml(content)}</div>
            </div>
            <div class="message-avatar-wrap">
                <img src="${CURRENT_USER_AVATAR}" alt="User Avatar" class="avatar-sm">
            </div>
        ` : `
            <div class="message-avatar-wrap">
                <div class="avatar-sm glass" style="display:flex; align-items:center; justify-content:center; background: var(--accent-gradient); color: #fff;">
                    <i class="fa-solid fa-robot" style="font-size:0.9rem;"></i>
                </div>
            </div>
            <div class="message-bubble-content">
                <div class="bubble-payload markdown-body">${parseMarkdown(content)}</div>
                <div class="message-control-row">
                    <button class="message-control-btn copy-bubble-btn" title="Copy Text"><i class="fa-solid fa-copy"></i></button>
                    <button class="message-control-btn speech-bubble-btn" title="Read Aloud"><i class="fa-solid fa-volume-high"></i></button>
                    <button class="message-control-btn like-btn ${rating === 1 ? 'active-like' : ''}" title="Like"><i class="fa-solid fa-thumbs-up"></i></button>
                    <button class="message-control-btn dislike-btn ${rating === -1 ? 'active-dislike' : ''}" title="Dislike"><i class="fa-solid fa-thumbs-down"></i></button>
                </div>
            </div>
        `;

        block.innerHTML = bubbleHtml;
        chatLog.appendChild(block);
        
        // Bind event listeners for actions on assistant bubbles
        if (!isUser) {
            bindBubbleEvents(block, content, msgId);
        }
    }

    function bindBubbleEvents(block, rawContent, msgId) {
        const copyBtn = block.querySelector(".copy-bubble-btn");
        const speechBtn = block.querySelector(".speech-bubble-btn");
        const likeBtn = block.querySelector(".like-btn");
        const dislikeBtn = block.querySelector(".dislike-btn");

        // Copy plain text
        copyBtn.addEventListener("click", () => {
            navigator.clipboard.writeText(rawContent).then(() => {
                copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
                setTimeout(() => copyBtn.innerHTML = '<i class="fa-solid fa-copy"></i>', 2000);
            });
        });

        // Speech output synthesis read-aloud
        speechBtn.addEventListener("click", () => {
            voiceManager.toggleTTS(active => {
                if (active) {
                    voiceManager.speak(rawContent);
                    speechBtn.innerHTML = '<i class="fa-solid fa-stop"></i>';
                    speechBtn.title = "Stop Reading";
                } else {
                    voiceManager.stopSpeaking();
                    speechBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
                    speechBtn.title = "Read Aloud";
                }
            });
        });

        // Rating hooks
        if (msgId) {
            likeBtn.addEventListener("click", () => rateMessage(msgId, likeBtn.classList.contains("active-like") ? 0 : 1, likeBtn, dislikeBtn));
            dislikeBtn.addEventListener("click", () => rateMessage(msgId, dislikeBtn.classList.contains("active-dislike") ? 0 : -1, likeBtn, dislikeBtn));
        }
    }

    function rateMessage(msgId, value, likeBtn, dislikeBtn) {
        fetch(`/api/conversations/${activeConversationId}/message/${msgId}/rate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rating: value })
        })
        .then(res => res.json())
        .then(data => {
            likeBtn.classList.remove("active-like");
            dislikeBtn.classList.remove("active-dislike");
            
            if (data.rating === 1) likeBtn.classList.add("active-like");
            if (data.rating === -1) dislikeBtn.classList.add("active-dislike");
        });
    }

    // ── Pipeline Submit Handler (AI EventSource Streaming) ────────────────────
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = promptInput.value.trim();
        if (!text) return;

        // Reset input field heights
        promptInput.value = "";
        promptInput.style.height = "auto";

        if (!activeConversationId) {
            // First message triggers conversation record creation
            fetch("/api/conversations", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: text.substring(0, 30) })
            })
            .then(res => res.json())
            .then(data => {
                activeConversationId = data.id;
                loadConversations(data.id);
                triggerStreamFlow(text);
            });
        } else {
            triggerStreamFlow(text);
        }
    });

    function triggerStreamFlow(prompt) {
        // Stop any active Speech reading
        voiceManager.stopSpeaking();

        // 1. Render user message prompt immediately
        appendMessageBubble("user", prompt);
        scrollToBottom();

        // 2. Render typing indicator and streaming controls
        typingIndicator.classList.remove("hidden");
        streamCancelRow.classList.remove("hidden");
        scrollToBottom();

        // 3. Initiate SSE connection
        const streamUrl = `/chat/stream/${activeConversationId}?message=${encodeURIComponent(prompt)}`;
        activeStream = new EventSource(streamUrl);

        // Pre-create Assistant bubble block to populate chunk-by-chunk
        const botBlock = document.createElement("div");
        botBlock.className = "message-block assistant animate-fade-in";
        
        botBlock.innerHTML = `
            <div class="message-avatar-wrap">
                <div class="avatar-sm" style="display:flex; align-items:center; justify-content:center; background: var(--accent-gradient); color: #fff;">
                    <i class="fa-solid fa-robot" style="font-size:0.9rem;"></i>
                </div>
            </div>
            <div class="message-bubble-content">
                <div class="bubble-payload markdown-body"></div>
                <div class="message-control-row hidden">
                    <button class="message-control-btn copy-bubble-btn" title="Copy Text"><i class="fa-solid fa-copy"></i></button>
                    <button class="message-control-btn speech-bubble-btn" title="Read Aloud"><i class="fa-solid fa-volume-high"></i></button>
                    <button class="message-control-btn like-btn" title="Like"><i class="fa-solid fa-thumbs-up"></i></button>
                    <button class="message-control-btn dislike-btn" title="Dislike"><i class="fa-solid fa-thumbs-down"></i></button>
                </div>
            </div>
        `;
        
        const payloadDiv = botBlock.querySelector(".bubble-payload");
        const controls = botBlock.querySelector(".message-control-row");
        chatLog.appendChild(botBlock);

        let fullText = "";

        activeStream.onmessage = (event) => {
            // Unescape \\n back to real newlines (server escapes them for SSE framing)
            const chunk = event.data.replace(/\\n/g, "\n");
            fullText += chunk;
            
            // Render text in real time using markdown parser
            payloadDiv.innerHTML = parseMarkdown(fullText);
            
            // Format dynamic scroll boxes and highlight code blocks
            if (typeof hljs !== 'undefined' && hljs.highlightElement) {
                payloadDiv.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));
            }
            scrollToBottom();
        };

        activeStream.onerror = () => {
            closeStream();
            
            // Enable controls and populate buttons
            controls.classList.remove("hidden");
            
            // Read response aloud if TTS is globally active
            if (voiceManager.ttsEnabled) {
                voiceManager.speak(fullText);
            }

            // Sync database mappings back by fetching message metadata
            fetch(`/api/conversations/${activeConversationId}`)
                .then(res => res.json())
                .then(data => {
                    const messages = data.messages;
                    if (messages && messages.length > 0) {
                        const lastMsg = messages[messages.length - 1];
                        botBlock.dataset.msgId = lastMsg.id;
                        bindBubbleEvents(botBlock, fullText, lastMsg.id);
                    }
                });
        };
    }

    function closeStream() {
        if (activeStream) {
            activeStream.close();
            activeStream = null;
        }
        typingIndicator.classList.add("hidden");
        streamCancelRow.classList.add("hidden");
    }

    stopGenBtn.addEventListener("click", () => {
        closeStream();
    });

    // ── Custom Code Block Copy Handlers ─────────────────────────────────────
    function parseMarkdown(md) {
        if (typeof marked === 'undefined' || !marked.parse) {
            const escaped = md
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\n/g, "<br>");
            return `<p>${escaped}</p>`;
        }
        // Setup custom marked renderer to append copy button elements to pre-code tags
        const rawHtml = marked.parse(md);
        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = rawHtml;

        // Enhance Pre elements
        tempDiv.querySelectorAll("pre").forEach(pre => {
            const codeEl = pre.querySelector("code");
            const lang = codeEl ? codeEl.className.replace("hljs language-", "") : "Code";
            
            const copyHeader = document.createElement("div");
            copyHeader.className = "code-header-row";
            copyHeader.innerHTML = `
                <span>${lang.toUpperCase()}</span>
                <button class="copy-code-btn" type="button"><i class="fa-solid fa-copy"></i> Copy Code</button>
            `;
            
            pre.insertBefore(copyHeader, pre.firstChild);
            
            const btn = copyHeader.querySelector(".copy-code-btn");
            btn.addEventListener("click", () => {
                const codeText = codeEl ? codeEl.innerText : pre.innerText;
                navigator.clipboard.writeText(codeText).then(() => {
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                    setTimeout(() => btn.innerHTML = '<i class="fa-solid fa-copy"></i> Copy Code', 2000);
                });
            });
        });

        return tempDiv.innerHTML;
    }

    // ── Voice Speech Controls ────────────────────────────────────────────────
    voiceBtn.addEventListener("click", () => {
        voiceManager.startListening(
            (text) => {
                promptInput.value += text + " ";
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
                voiceBtn.classList.remove("recording-pulse");
            },
            () => {
                voiceBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
                voiceBtn.classList.add("recording-pulse");
            },
            () => {
                voiceBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
                voiceBtn.classList.remove("recording-pulse");
            }
        );
    });

    ttsBtn.addEventListener("click", () => {
        const active = voiceManager.toggleTTS(enabled => {
            if (enabled) {
                ttsBtn.innerHTML = '<i class="fa-solid fa-volume-high"></i>';
                ttsBtn.title = "Text-to-Speech Output (On)";
                ttsBtn.style.color = "var(--success)";
            } else {
                ttsBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i>';
                ttsBtn.title = "Text-to-Speech Output (Off)";
                ttsBtn.style.color = "var(--text-primary)";
            }
        });
    });

    // ── UI Helpers ────────────────────────────────────────────────────────────
    function scrollToBottom() {
        scrollBox.scrollTop = scrollBox.scrollHeight;
    }

    function checkEngineStatus() {
        fetch("/api/usage")
            .then(res => res.json())
            .then(() => {
                statusIndicator.querySelector(".indicator-text").innerText = "Engine online";
                statusIndicator.querySelector(".indicator-dot").className = "indicator-dot green";
            })
            .catch(() => {
                statusIndicator.querySelector(".indicator-text").innerText = "Offline/Fallback Active";
                statusIndicator.querySelector(".indicator-dot").className = "indicator-dot yellow";
            });
    }

    function setupTextareaAutoResize() {
        promptInput.addEventListener("input", function() {
            this.style.height = "auto";
            this.style.height = (this.scrollHeight) + "px";
        });
        
        promptInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    }

    // ── Drag & Drop file attachment mock ──────────────────────────────────────
    function setupDragAndDrop() {
        ["dragenter", "dragover"].forEach(event => {
            document.body.addEventListener(event, (e) => {
                e.preventDefault();
                dragOverlay.classList.add("active");
            }, false);
        });

        ["dragleave", "drop"].forEach(event => {
            document.body.addEventListener(event, (e) => {
                e.preventDefault();
                dragOverlay.classList.remove("active");
            }, false);
        });

        document.body.addEventListener("drop", (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                attachMockFile(files[0]);
            }
        });

        fileSelector.addEventListener("change", () => {
            if (fileSelector.files.length > 0) {
                attachMockFile(fileSelector.files[0]);
            }
        });
    }

    function attachMockFile(file) {
        promptInput.value += `\n[Attached File: ${file.name} (${(file.size/1024).toFixed(1)} KB)]\n`;
        promptInput.dispatchEvent(new Event("input"));
    }

    // ── Utilities (Search, Export, Clean) ────────────────────────────────────
    newChatBtn.addEventListener("click", () => {
        showWelcome();
        activeConversationId = null;
        document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
        promptInput.focus();
    });

    chatSearch.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        document.querySelectorAll(".conversation-item").forEach(el => {
            const titleEl = el.querySelector(".title-text");
            if (!titleEl) return;
            const title = titleEl.innerText.toLowerCase();
            if (title.includes(query)) {
                el.classList.remove("hidden");
            } else {
                el.classList.add("hidden");
            }
        });
    });

    exportBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (!activeConversationId) return;

        fetch(`/api/conversations/${activeConversationId}`)
            .then(res => res.json())
            .then(data => {
                let markdownContent = `# Chat Log: ${data.title}\n\n`;
                data.messages.forEach(m => {
                    markdownContent += `### **${m.role.toUpperCase()}** (${m.timestamp})\n\n${m.content}\n\n---\n\n`;
                });
                
                const blob = new Blob([markdownContent], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `chat-log-${activeConversationId}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            });
    });

    clearBtn.addEventListener("click", (e) => {
        e.preventDefault();
        if (!activeConversationId) return;
        if (confirm("Are you sure you want to clear all message logs for this chat?")) {
            fetch(`/api/conversations/${activeConversationId}`, { method: "DELETE" })
                .then(() => {
                    activeConversationId = null;
                    loadConversations();
                });
        }
    });

    // Handle suggestion cards clicks
    document.querySelectorAll(".prompt-suggestion-card").forEach(card => {
        card.addEventListener("click", () => {
            const val = card.dataset.prompt;
            promptInput.value = val;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    function escapeHtml(string) {
        return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
});
