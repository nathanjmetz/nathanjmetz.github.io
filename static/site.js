// Small extras. The site works fully without this file.

// Show recent times as "3 hours ago" in the reader's own clock.
(function relativeTimes() {
  var now = Date.now();
  document.querySelectorAll(".meta time[datetime]").forEach(function (el) {
    var then = Date.parse(el.getAttribute("datetime"));
    if (isNaN(then)) return;
    var mins = Math.round((now - then) / 60000);
    if (mins < 0 || mins > 60 * 36) return;
    el.title = el.textContent;
    if (mins < 60) el.textContent = mins <= 1 ? "Just now" : mins + " min ago";
    else {
      var hrs = Math.round(mins / 60);
      el.textContent = hrs + (hrs === 1 ? " hour ago" : " hours ago");
    }
  });
})();

// Source filter chips on topic pages.
(function sourceFilter() {
  var bar = document.querySelector(".filters");
  if (!bar) return;
  bar.hidden = false;
  var chips = bar.querySelectorAll(".chip");
  var empty = document.querySelector("[data-filter-empty]");

  bar.addEventListener("click", function (e) {
    var chip = e.target.closest(".chip");
    if (!chip) return;
    var want = chip.dataset.filter;
    chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });

    var shown = 0;
    document.querySelectorAll(".day").forEach(function (day) {
      var any = false;
      day.querySelectorAll(".story").forEach(function (s) {
        var match = !want || s.dataset.source === want;
        s.hidden = !match;
        if (match) any = true;
      });
      day.hidden = !any;
      if (any) shown++;
    });
    if (empty) empty.hidden = shown > 0;
  });
})();

// The front page heading shows the reader's own today, even between morning updates.
(function todayHeading() {
  var h = document.querySelector(".front-head h1");
  if (!h) return;
  h.textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });
})();
