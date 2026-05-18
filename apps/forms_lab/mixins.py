from __future__ import annotations

from django import forms


class FieldStateMixin:
    """Compute neutral / valid / invalid display state for bound fields."""

    def field_state(self, field_name: str) -> tuple[str, str]:
        if not self.is_bound:
            return "neutral", ""
        errors = self.errors.get(field_name)
        if errors:
            return "invalid", errors[0]
        field = self.fields.get(field_name)
        if not field:
            return "neutral", ""
        raw = field.widget.value_from_datadict(
            self.data, self.files, self.add_prefix(field_name)
        )
        if not field.required and not raw:
            return "neutral", ""
        return "valid", "Looks good."


class HTMXFormMixin(FieldStateMixin):
    """Shared helpers for full-page and single-field HTMX rendering."""

    validator_names: list[str] = []
    demonstrates: list[str] = []
    # Fields to clean before a single-field HTMX check
    # (e.g. country before postal_code).
    htmx_field_dependencies: dict[str, tuple[str, ...]] = {}

    def add_htmx_attrs(
        self,
        field_name: str,
        url: str,
        *,
        trigger: str = "blur",
        target: str | None = None,
        swap: str = "outerHTML",
        indicator: str | None = "#htmx-spinner",
    ) -> None:
        field = self.fields[field_name]
        default_target = f"#{self[field_name].id_for_label}-wrap"
        attrs = {
            "hx-post": url,
            "hx-trigger": trigger,
            "hx-target": target or default_target,
            "hx-swap": swap,
        }
        if indicator:
            attrs["hx-indicator"] = indicator
        field.widget.attrs.update(attrs)


class TailwindFormMixin:
    base_input_class = (
        "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm "
        "text-slate-900 shadow-sm outline-none transition focus:border-teal-600 "
        "focus:ring-2 focus:ring-teal-500/20 dark:border-slate-600 "
        "dark:bg-slate-900 dark:text-slate-100"
    )

    checkbox_class = (
        "h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
    )

    def style_fields(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.RadioSelect, forms.CheckboxSelectMultiple)):
                # Class lands on the option-group wrapper; sizing utilities
                # would collapse it, so style the wrapper for layout only.
                css = "space-y-1 accent-teal-600"
            elif isinstance(widget, forms.CheckboxInput):
                css = self.checkbox_class
            elif isinstance(widget, forms.HiddenInput):
                continue
            else:
                css = self.base_input_class
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css}".strip()
