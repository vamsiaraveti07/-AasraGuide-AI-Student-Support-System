function highlightSelection() {
    const editor = document.getElementById("note-content");
    let sel = window.getSelection();

    if (!sel.rangeCount) return alert("Select text to highlight!");

    let range = sel.getRangeAt(0);

    const mark = document.createElement("mark");
    mark.className = "hl-soft";    

    try {
        range.surroundContents(mark);
    } catch (e) {
        alert("Highlight failed — try selecting shorter text.");
    }
}

function makeBold() {
    document.execCommand("bold");
}

function initQuickNotes() {
    document.getElementById('save-note-btn').onclick = function () {

        const title = document.getElementById('note-title').value.trim();
        const content = document.getElementById('note-content').innerHTML.trim();
        const tags = document.getElementById('note-tags').value.trim();
        const reminder_at = document.getElementById('note-reminder').value;

        if (!content) return alert("Write something!");

        fetch('/notes/add', {
            method: 'POST',
            body: new URLSearchParams({title, content, tags, reminder_at}),
            headers: {'Content-Type': 'application/x-www-form-urlencoded'}
        })
        .then(r => r.json())
        .then(res => {
            if (res.ok) {
                document.getElementById('note-title').value = "";
                document.getElementById('note-content').innerHTML = "";
                document.getElementById('note-tags').value = "";
                document.getElementById('note-reminder').value = "";

                loadNotes();
            } else alert(res.error);
        });
    };

    loadNotes();
}

function loadNotes() {
    fetch('/notes/list')
        .then(r => r.json())
        .then(notes => {
            const container = document.getElementById('notes-list');

            if (!notes.length) {
                container.innerHTML = "<div class='empty'>No notes yet.</div>";
                return;
            }

            container.innerHTML = notes.map(n => `
                <div class="note-item" data-id="${n.id}">
                    <div class="note-title-row">
                        <span>${n.title}</span>
                        <button class="tb-btn btn-note-delete" data-id="${n.id}">Delete</button>
                    </div>

                    <div class="note-content">${n.content}</div>

                    <div class="note-tags" style="font-size:12px;color:#3fa9ff;margin-top:6px;">
                        Tags: ${n.tags || "<em>none</em>"}
                    </div>

                    <!-- Upload attachments -->
                    <div style="margin-top:10px;">
                        <input type="file" class="note-file-input" data-id="${n.id}">
                        <button class="tb-btn btn-note-upload" data-id="${n.id}">Upload</button>
                    </div>

                    <!-- Preview attachments -->
                    <div class="attachments-box" data-id="${n.id}" style="margin-top:10px;">
                        ${
                            n.attachments.length
                            ? n.attachments.map(f => {
                                let low = f.toLowerCase();
                                if (low.endsWith(".jpg") || low.endsWith(".png") || low.endsWith(".jpeg") || low.endsWith(".gif")) {
                                    return `<img src="/static/uploads/notes/${f}" class="thumb" 
                                            style="width:120px;border-radius:6px;margin:6px;cursor:pointer;"
                                            onclick="openImage('/static/uploads/notes/${f}')">`;
                                }
                                return `📎 <a target="_blank" href="/static/uploads/notes/${f}">${f}</a>`;
                            }).join("")
                            : "<em>No attachments</em>"
                        }
                    </div>

                    <!-- Share -->
                    <div style="margin-top:6px;">
                        <button class="tb-btn btn-share-note" data-id="${n.id}">Share</button>
                        <input class="share-username-input" data-id="${n.id}" type="text" placeholder="Friend username"
                               style="width:130px;display:none;">
                        <button class="tb-btn btn-share-send" data-id="${n.id}" style="display:none;">Send</button>
                    </div>

                    <div style="font-size:11px;color:#18b46e;margin-top:6px;">
                        Shared with: ${n.shared_with || "<em>none</em>"}
                    </div>
                </div>
            `).join("");

            setupDeleteHandlers();
            setupUploadHandlers();
            setupShareHandlers();
        });
}
function setupDeleteHandlers() {
    document.querySelectorAll('.btn-note-delete').forEach(btn => {
        btn.onclick = () => {
            let id = btn.dataset.id;
            fetch('/notes/delete/' + id, {method:'POST'})
                .then(() => loadNotes());
        };
    });
}
function setupUploadHandlers() {
    document.querySelectorAll('.btn-note-upload').forEach(btn => {
        btn.onclick = () => {
            let id = btn.dataset.id;
            let input = document.querySelector(`.note-file-input[data-id='${id}']`);

            if (!input.files.length) return alert("Choose a file");

            let fd = new FormData();
            fd.append("file", input.files[0]);

            fetch('/notes/upload/' + id, {method:"POST", body:fd})
                .then(r => r.json())
                .then(res => {
                    if (res.ok) loadNotes();
                    else alert(res.error);
                });
        };
    });
}

function setupShareHandlers() {
    document.querySelectorAll('.btn-share-note').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.id;
            document.querySelector(`.share-username-input[data-id='${id}']`).style.display = "";
            document.querySelector(`.btn-share-send[data-id='${id}']`).style.display = "";
        };
    });

    document.querySelectorAll('.btn-share-send').forEach(btn => {
        btn.onclick = () => {
            const id = btn.dataset.id;
            const input = document.querySelector(`.share-username-input[data-id='${id}']`);
            const username = input.value.trim();
            if (!username) return alert("Enter username");

            fetch('/notes/share/' + id, {
                method:"POST",
                body:new URLSearchParams({username}),
                headers:{'Content-Type': 'application/x-www-form-urlencoded'}
            })
            .then(r => r.json())
            .then(res => {
                if (res.ok) loadNotes();
                else alert(res.error);
            });
        };
    });
}


// ---------------------
// OPEN IMAGE POPUP
// ---------------------
function openImage(src) {
    let w = window.open("", "img", "width=600,height=600");
    w.document.write(`<img src="${src}" style="width:100%">`);
}
