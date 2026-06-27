/**
 * static/js/theme.js — Theme Management System
 * ============================================
 * Handles persistent dark/light theme switching.
 * Intercepts loading early to prevent UI flash.
 */

(function () {
    const currentTheme = localStorage.getItem("theme") || "dark";
    document.documentElement.setAttribute("data-theme", currentTheme);
})();

document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("theme-toggle");
    if (!toggleBtn) return;

    // Set initial icon state based on loaded theme
    updateIcon(document.documentElement.getAttribute("data-theme"));

    toggleBtn.addEventListener("click", () => {
        let theme = document.documentElement.getAttribute("data-theme");
        let nextTheme = theme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("theme", nextTheme);
        updateIcon(nextTheme);
        
        // Sync setting to database if user is logged in
        fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme: nextTheme })
        }).catch(() => {}); // Silently fail if guest or network is off
    });

    function updateIcon(theme) {
        const icon = toggleBtn.querySelector("i");
        if (!icon) return;
        if (theme === "dark") {
            icon.className = "fa-solid fa-sun";
            toggleBtn.title = "Switch to Light Mode";
        } else {
            icon.className = "fa-solid fa-moon";
            toggleBtn.title = "Switch to Dark Mode";
        }
    }
});
