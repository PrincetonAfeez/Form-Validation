""" Template tags for the form validation showcase. """

from __future__ import annotations

from django import forms, template

register = template.Library()


def bound_field_context(
    form, field, *, state: str | None = None, message: str | None = None
):
    """Build template context for forms/_field.html."""
    if state is None or message is None:
        state, message = form.field_state(field.name)
    # RadioSelect / CheckboxSelectMultiple have an empty id_for_label, so fall
    # back to auto_id to keep wrapper/message ids unique.
    field_id = field.id_for_label or field.auto_id
    message_id = f"{field_id}-message"
    wrapper_id = f"{field_id}-wrap"

    use_fieldset = isinstance(
        field.field.widget,
        (forms.RadioSelect, forms.CheckboxSelectMultiple),
    )

    if field.is_hidden:
        field_html = None
    else:
        widget_attrs = {}
        if not use_fieldset:
            widget_attrs["aria-describedby"] = message_id
        if state == "invalid":
            widget_attrs["aria-invalid"] = "true"
        field_html = (
            field.as_widget(attrs=widget_attrs)
            if widget_attrs
            else field.as_widget()
        )

    return {
        "form": form,
        "field": field,
        "field_html": field_html,
        "wrapper_id": wrapper_id,
        "message_id": message_id,
        "state": state,
        "message": message,
        "use_fieldset": use_fieldset and not field.is_hidden,
    }


@register.inclusion_tag("forms/_field.html")
def render_bound_field(form, field):
    """Render a bound field with state/message from FieldStateMixin.field_state()."""
    return bound_field_context(form, field)
