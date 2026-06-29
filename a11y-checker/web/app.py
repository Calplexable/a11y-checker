"""
app.py

Simple Flask web wrapper around the accessibility checker. Lets users
either enter a URL or paste raw HTML directly, and view the resulting
report in the browser.
"""

from flask import Flask, render_template, request

from checker import check_html, check_url

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    error = None
    url_value = ""
    html_value = ""

    if request.method == "POST":
        url_value = request.form.get("url", "").strip()
        html_value = request.form.get("html", "").strip()

        try:
            if url_value:
                report = check_url(url_value)
            elif html_value:
                report = check_html(html_value, source="Pasted HTML")
            else:
                error = "Please enter a URL or paste some HTML to check."
        except Exception as exc:
            error = f"Couldn't check that page: {exc}"

    return render_template(
        "index.html",
        report=report,
        error=error,
        url_value=url_value,
        html_value=html_value,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
