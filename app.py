from flask import Flask, render_template_string, request, send_file
import yt_dlp
import os
import glob

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>YouTube Downloader</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body{
    background:#f5f5f5;
}
.container{
    max-width:700px;
}
</style>

</head>

<body>

<div class="container mt-5">

<div class="card shadow">

<div class="card-body">

<h2 class="text-center mb-4">
YouTube Downloader
</h2>

<form method="POST">

<input
class="form-control form-control-lg mb-3"
type="text"
name="url"
placeholder="YouTube Linki"
required>

<button
class="btn btn-success w-100 btn-lg">

Video Bilgilerini Getir

</button>

</form>

{% if error %}

<div class="alert alert-danger mt-3">

{{error}}

</div>

{% endif %}

{% if title %}

<div class="card mt-4">

<div class="card-header">

<b>{{title}}</b>

</div>

<ul class="list-group list-group-flush">

{% for f in formats %}

<li class="list-group-item d-flex justify-content-between">

<span>

{{f.label}}

</span>

<a
class="btn btn-primary btn-sm"
href="/download?url={{url}}&format={{f.id}}">

İndir

</a>

</li>

{% endfor %}

</ul>

</div>

{% endif %}

</div>

</div>

</div>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():

    title = ""
    formats = []
    error = None
    url = ""

    if request.method == "POST":

        url = request.form["url"]

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "no_warnings": True
        }

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(url, download=False)

                title = info.get("title", "Video")

                for f in info["formats"]:

                    if f.get("vcodec") == "none":
                        continue

                    height = f.get("height")

                    if not height:
                        continue

                    formats.append({
                        "id": f["format_id"],
                        "label": f"{height}p ({f['ext']})"
                    })

        except Exception as e:

            error = str(e)

    return render_template_string(
        HTML,
        title=title,
        formats=formats,
        error=error,
        url=url
    )


@app.route("/download")
def download():

    url = request.args.get("url")
    format_id = request.args.get("format")

    for file in glob.glob(DOWNLOAD_DIR + "/*"):
        try:
            os.remove(file)
        except:
            pass

    ydl_opts = {
        "format": f"{format_id}+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": DOWNLOAD_DIR + "/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            base = os.path.splitext(filename)[0]

            if os.path.exists(base + ".mp4"):
                filename = base + ".mp4"

            return send_file(filename, as_attachment=True)

    except Exception as e:

        return str(e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
app.py
requirements.txt
Procfile
runtime.txt
cookies.txt
