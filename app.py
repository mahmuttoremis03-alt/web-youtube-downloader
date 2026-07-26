from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<title>Video İndirici</title>
</head>
<body class="bg-dark text-light">
<div class="container py-5" style="max-width:720px">
<h2 class="mb-4 text-center">Video İndirici</h2>
<form method="post">
<input class="form-control mb-3" name="url" placeholder="Video bağlantısı" value="{{ request.form.get('url', '') }}">
<button class="btn btn-success w-100">Bilgileri Getir ve İndirmeye Hazırla</button>
</form>

{% if error %}
<div class="alert alert-danger mt-3">{{ error }}</div>
{% endif %}

{% if info %}
<div class="card mt-4 bg-secondary text-light">
<div class="card-body">
<h4>{{ info.title }}</h4>
<p>Süre: {{ info.duration }} sn</p>
<p>Kanal: {{ info.uploader }}</p>
<a href="{{ info.download_url }}" class="btn btn-primary w-100 mt-3" target="_blank">Videoyu Cihaza İndir</a>
</div>
</div>
{% endif %}
</div>
</body>
</html>
"""

import yt_dlp

@app.route("/", methods=["GET","POST"])
def home():
    info=None
    error=None
    if request.method=="POST":
        url=request.form.get("url","")
        opts={
            "quiet":True,
            "noplaylist":True,
            "no_warnings":True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
                
                # Doğrudan oynatılabilir/indirilebilir medya adresini alıyoruz
                download_url = data.get("url")
                if not download_url and "formats" in data:
                    # Alternatif olarak en iyi formatın URL'sini seç
                    formats = data.get("formats", [])
                    for f in formats:
                        if f.get("url") and f.get("vcodec") != "none":
                            download_url = f.get("url")
                            break

                info={
                    "title": data.get("title"),
                    "duration": data.get("duration"),
                    "uploader": data.get("uploader"),
                    "download_url": download_url
                }
        except Exception as e:
            error=str(e)
    return render_template_string(HTML, info=info, error=error)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
