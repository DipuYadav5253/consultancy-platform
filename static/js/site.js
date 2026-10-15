(() => {
  "use strict";
  const doc = document.documentElement;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Sticky header gets a solid background after scrolling.
  const header = document.querySelector("[data-header]");
  if (header) {
    const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Mobile menu.
  const burger = document.querySelector("[data-burger]");
  const menu = document.querySelector("[data-menu]");
  if (burger && menu) {
    const setOpen = (open) => {
      burger.setAttribute("aria-expanded", String(open));
      menu.classList.toggle("open", open);
      document.body.style.overflow = open ? "hidden" : "";
    };
    burger.addEventListener("click", () => setOpen(burger.getAttribute("aria-expanded") !== "true"));
    menu.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") setOpen(false); });
    window.matchMedia("(min-width: 901px)").addEventListener("change", (e) => { if (e.matches) setOpen(false); });
  }

  // Scroll reveal with staggered children (used by the sections we add next).
  if (!reduced && "IntersectionObserver" in window) {
    doc.classList.add("reveal-ready");
    document.querySelectorAll("[data-stagger]").forEach((group) => {
      [...group.children].forEach((el, i) => el.style.setProperty("--d", `${Math.min(i, 8) * 90}ms`));
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add("in"); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
  }

  // Cursor spotlight on cards (fine pointers only).
  if (!reduced && window.matchMedia("(pointer: fine)").matches) {
    document.addEventListener("pointermove", (e) => {
      const card = e.target.closest && e.target.closest(".spot");
      if (!card) return;
      const r = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - r.left}px`);
      card.style.setProperty("--my", `${e.clientY - r.top}px`);
    }, { passive: true });
  }

  // IELTS slider: live value and link to filtered results (added in a later step).
  const range = document.getElementById("ielts-range");
  if (range) {
    const out = document.getElementById("ielts-out");
    const link = document.getElementById("ielts-link");
    const update = () => {
      const v = Number(range.value);
      const pct = ((v - range.min) / (range.max - range.min)) * 100;
      range.style.setProperty("--pct", `${pct}%`);
      out.textContent = v.toFixed(1);
      link.href = `${range.dataset.base}?ielts=${v.toFixed(1)}`;
    };
    range.addEventListener("input", update);
    update();
  }

  // Pause the SVG plane animation for people who prefer reduced motion.
  if (reduced) document.querySelectorAll("svg.globe").forEach((svg) => svg.pauseAnimations && svg.pauseAnimations());
})();