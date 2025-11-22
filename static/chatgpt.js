// static/chatgpt.js - final polished client
const chatForm = document.getElementById("chat-form");
const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message");
const suggestionsPlaceholder = document.getElementById("suggestions-placeholder");

function scrollToBottom() {
  if (!chatBox) return;
  // small delay helps when images/code inserted
  setTimeout(() => { chatBox.scrollTop = chatBox.scrollHeight; }, 40);
}

function autoResizeTextarea(el) {
  if (!el) return;
  el.style.height = "1px";
  el.style.height = Math.min(el.scrollHeight, 420) + "px";
}

if (messageInput) {
  messageInput.addEventListener("input", (e) => autoResizeTextarea(e.target));
  autoResizeTextarea(messageInput);
}

// showdown markdown converter
const converter = new showdown.Converter({tables:true, simplifiedAutoLink:true, strikethrough:true, tasklists:true});
if (window.hljs) { hljs.configure({ignoreUnescapedHTML: true}); }

// helper to create a message row (returns appended row)
function appendUserMessage(text, timeLabel="just now") {
  const row = document.createElement("div");
  row.className = "msg-row right";

  const bubble = document.createElement("div");
  bubble.className = "msg user";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `You • ${timeLabel}`;

  const content = document.createElement("div");
  content.className = "content";
  content.textContent = text;

  bubble.appendChild(meta);
  bubble.appendChild(content);

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar user";
  avatar.textContent = "You";

  row.appendChild(bubble);
  row.appendChild(avatar);

  chatBox.appendChild(row);
  scrollToBottom();
  return {row, bubble, content};
}

function appendAssistantMessageHtml(htmlContent, timeLabel="just now") {
  const row = document.createElement("div");
  row.className = "msg-row left";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar bot";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "msg bot";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `Bot • ${timeLabel}`;

  const content = document.createElement("div");
  content.className = "content";
  content.innerHTML = htmlContent;

  bubble.appendChild(meta);
  bubble.appendChild(content);

  row.appendChild(avatar);
  row.appendChild(bubble);
  chatBox.appendChild(row);

  // highlight codeblocks if present
  if (window.hljs) bubble.querySelectorAll('pre code').forEach((b) => hljs.highlightElement(b));

  scrollToBottom();
  return {row, bubble, content};
}

function createTypingNode() {
  const row = document.createElement("div");
  row.className = "msg-row left";
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar bot";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "msg typing";

  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `Bot • just now`;

  const content = document.createElement("div");
  content.className = "content";
  content.innerHTML = `<span class="typing-dots"><span></span><span></span><span></span></span>`;

  bubble.appendChild(meta);
  bubble.appendChild(content);
  row.appendChild(avatar);
  row.appendChild(bubble);
  chatBox.appendChild(row);
  scrollToBottom();
  return row;
}

if (chatForm) {
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = (messageInput.value || "").trim();
    if (!text) return;

    // append user message immediately
    appendUserMessage(text, "just now");
    messageInput.value = "";
    autoResizeTextarea(messageInput);

    // show typing
    const typingNode = createTypingNode();

    // clear suggestions area
    if (suggestionsPlaceholder) suggestionsPlaceholder.innerHTML = "AI suggestions will appear after each reply.";

    const sessionId = chatForm.dataset.session;
    const data = new URLSearchParams();
    data.append("message", text);

    try {
      const res = await fetch(`/send/${sessionId}`, { method: "POST", body: data });
      const json = await res.json();

      // remove typing
      typingNode.remove();

      // render assistant reply (supports markdown -> HTML)
      const md = json.reply || "";
      const html = converter.makeHtml(md);
      const node = appendAssistantMessageHtml(html, "just now");

      // render code highlight (if present)
      if (window.hljs) node.bubble && node.bubble.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));

      // suggestions
      if (json.suggestions && json.suggestions.length && suggestionsPlaceholder) {
        suggestionsPlaceholder.innerHTML = "";
        const box = document.createElement("div");
        box.className = "suggestion-box";
        json.suggestions.forEach(s => {
          const btn = document.createElement("button");
          btn.className = "suggestion-btn";
          btn.textContent = s;
          btn.addEventListener("click", () => {
            messageInput.value = s;
            autoResizeTextarea(messageInput);
            messageInput.focus();
          });
          box.appendChild(btn);
        });
        suggestionsPlaceholder.appendChild(box);
      }

      scrollToBottom();
    } catch (err) {
      typingNode.remove();
      appendAssistantMessageHtml("<p><strong>System:</strong> Failed to send. Try again.</p>", "System");
    }
  });

  // Enter to send, Shift+Enter for newline
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.requestSubmit();
    }
  });
}
