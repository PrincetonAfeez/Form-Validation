(function () {
  function showToast(text) {
    const region = document.getElementById("toast-region");
    if (!region || !text) return;
    region.textContent = text;
    region.classList.remove("sr-only");
    region.classList.add(
      "fixed",
      "bottom-4",
      "right-4",
      "z-50",
      "max-w-sm",
      "rounded-md",
      "border",
      "border-slate-200",
      "bg-white",
      "px-4",
      "py-3",
      "text-sm",
      "font-medium",
      "text-slate-800",
      "shadow-lg",
      "dark:border-slate-700",
      "dark:bg-slate-900",
      "dark:text-slate-100"
    );
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(function () {
      region.textContent = "";
      region.classList.add("sr-only");
      region.classList.remove(
        "fixed",
        "bottom-4",
        "right-4",
        "z-50",
        "max-w-sm",
        "rounded-md",
        "border",
        "border-slate-200",
        "bg-white",
        "px-4",
        "py-3",
        "text-sm",
        "font-medium",
        "text-slate-800",
        "shadow-lg",
        "dark:border-slate-700",
        "dark:bg-slate-900",
        "dark:text-slate-100"
      );
    }, 4000);
  }

  document.body.addEventListener("fieldValidated", function (event) {
    const detail = event.detail || {};
    if (detail.state === "valid") {
      showToast(detail.message || "Field looks good.");
    } else if (detail.state === "invalid") {
      showToast(detail.message || "Please fix this field.");
    }
  });

  document.body.addEventListener("cardBrandDetected", function (event) {
    const cvvLength = (event.detail && event.detail.cvvLength) || 3;
    const cvv = document.getElementById("id_cvv");
    if (cvv) {
      cvv.maxLength = cvvLength;
    }
    showToast("Card brand updated — enter a " + cvvLength + "-digit CVV.");
  });

  document.body.addEventListener("htmx:xhr:progress", function (event) {
    const bar = document.getElementById("upload-progress");
    if (!bar || !event.detail.lengthComputable) return;
    bar.classList.remove("hidden");
    bar.value = Math.round((event.detail.loaded / event.detail.total) * 100);
  });

  document.body.addEventListener("htmx:afterRequest", function (event) {
    const bar = document.getElementById("upload-progress");
    if (bar && event.detail.successful) {
      window.setTimeout(function () {
        bar.classList.add("hidden");
        bar.value = 0;
      }, 600);
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    document.querySelectorAll(".field-wrap[data-dismissed='true']").forEach(function (wrap) {
      wrap.removeAttribute("data-dismissed");
    });
    document.querySelectorAll(".field-wrap").forEach(function (wrap) {
      const message = wrap.querySelector(".field-message");
      const control = wrap.querySelector("[aria-invalid='true']");
      if (!message || !control) return;
      if (message.textContent.trim()) {
        message.textContent = "";
        message.classList.remove("text-red-700", "dark:text-red-300");
        message.classList.add("text-slate-500", "dark:text-slate-400");
        control.removeAttribute("aria-invalid");
        control.closest(".field-wrap")?.setAttribute("data-dismissed", "true");
        const border = wrap.querySelector("[class*='border-red']");
        if (border) {
          border.classList.remove("[&_*]:border-red-500");
        }
      }
    });
  });
})();
