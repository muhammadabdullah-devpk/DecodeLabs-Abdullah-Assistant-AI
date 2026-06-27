/**
 * static/js/main.js — General SaaS UI Animations
 * =============================================
 * Handles scrolling header fades and parallax scroll alignments.
 */

document.addEventListener("DOMContentLoaded", () => {
    const header = document.querySelector(".main-header");

    // Scroll Header Blur Effect
    window.addEventListener("scroll", () => {
        if (window.scrollY > 20) {
            header.style.background = "rgba(10, 11, 16, 0.75)";
            header.style.borderBottomColor = "rgba(255, 255, 255, 0.08)";
        } else {
            header.style.background = "var(--bg-glass)";
            header.style.borderBottomColor = "var(--border-color)";
        }
    });

    // Animate features cards sequentially as they enter view
    const cards = document.querySelectorAll(".feature-card");
    if (cards.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = "1";
                        entry.target.style.transform = "translateY(0)";
                    }, index * 100);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => {
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            card.style.transition = "opacity 0.6s ease-out, transform 0.6s ease-out";
            observer.observe(card);
        });
    }
});
