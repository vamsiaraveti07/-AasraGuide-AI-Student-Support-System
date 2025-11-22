const openBtn = document.getElementById("openSidebar");
const closeBtn = document.getElementById("closeSidebar");
const sidebar = document.getElementById("sidebar");

if (openBtn && sidebar) openBtn.addEventListener("click", () => sidebar.classList.toggle("show"));
if (closeBtn && sidebar) closeBtn.addEventListener("click", () => sidebar.classList.remove("show"));

function toggleArchived() {
  const box = document.getElementById("archivedList");
  if (box) box.style.display = (box.style.display === "none") ? "block" : "none";
}
window.toggleArchived = toggleArchived;

function toggleMenu(id) {
  document.querySelectorAll(".chat-options-menu").forEach(m => m.style.display = "none");
  const menu = document.getElementById("menu-" + id);
  if (menu) menu.style.display = "block";
}
window.toggleMenu = toggleMenu;
// sidebar.js - small helpers
document.addEventListener("click", (e) => {
  // close any popup menus if you add them later
  if (!e.target.closest(".chat-options-menu")) {
    document.querySelectorAll(".chat-options-menu").forEach(m => m.style.display = 'none');
  }
});
