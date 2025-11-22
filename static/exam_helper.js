function initExamHelper() {
    document.getElementById("exam-generate").onclick = function () {
        const subject = document.getElementById("exam-subject").value.trim();
        const resultBox = document.getElementById("exam-result");

        if (!subject) {
            alert("Enter a subject!");
            return;
        }

        resultBox.innerHTML = `<p style='padding:20px;'>Generating... ⏳</p>`;

        fetch("/exam-helper", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject })
        })
        .then(r => r.json())
        .then(res => {
            resultBox.innerHTML = `
                <div class="exam-section">
                    <h3>🔥 Important Topics</h3>
                    <p>${res.topics.join("<br>")}</p>
                </div>

                <div class="exam-section">
                    <h3>❓ Expected Questions</h3>
                    <p>${res.questions.join("<br>")}</p>
                </div>

                <div class="exam-section">
                    <h3>📝 Revision Notes</h3>
                    <p>${res.notes}</p>
                </div>

                <div class="exam-section">
                    <h3>⏳ 1-Day Revision Plan</h3>
                    <p>${res.plan.replace(/\n/g, "<br>")}</p>
                </div>
            `;
        })
        .catch(err => {
            resultBox.innerHTML = "<p style='color:red;padding:20px'>Error generating result.</p>";
        });
    };
}
