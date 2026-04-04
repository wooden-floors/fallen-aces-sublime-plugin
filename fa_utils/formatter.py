# utils/formatter.py
import html

def format_hint_html(definition):
    """
    Formats a function definition into an HTML hint suitable for popups.
    """
    name = definition["name"]
    args = definition["args"]
    description = definition.get("description")
    usage = definition.get("usage")

    html_content = []
    html_content.append("<b>{}({})</b>".format(name, ", ".join(args)))
    
    if description:
        html_content.append("<div style='margin-top: 5px;'>{}</div>".format(html.escape(description).replace("\n", "<br>")))
    
    if usage:
        html_content.append("<br><b>How to use</b>")
        html_content.append("<div style='background-color:#272822;color:#f8f8f2;padding:8px;margin-top:5px;border-radius:4px;font-family:monospace;'>{}</div>".format(
            html.escape(usage).replace("\n", "<br>").replace(" ", "&nbsp;")
        ))

    return "".join(html_content)
