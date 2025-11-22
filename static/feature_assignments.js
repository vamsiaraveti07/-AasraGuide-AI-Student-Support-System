async function loadReminders(days = 3) {
    const res = await fetch(`/api/assignments/reminders?days=${days}`);
    const reminders = await res.json();
    const reminderBox = document.getElementById("reminder-panel");
    if (Array.isArray(reminders) && reminders.length > 0) {
        reminderBox.innerHTML = reminders.map(a => 
            `<div class="reminder-row">
                <strong>${a.title}</strong> 
                (${a.subject || 'No subject'}) 
                <span>Due: ${a.due_date}</span>
                <p>${a.notes || ''}</p>
            </div>`
        ).join("");
    } else {
        reminderBox.innerHTML = "<p>No assignments due soon!</p>";
    }
}
