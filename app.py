from flask import Flask, render_template_string, request, Response
import yt_dlp
import requests

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
<button class="btn btn-success w-100">Bilgileri Getir ve Önizle</button>
</form>

{% if error %}
<div class="alert alert-danger mt-3">{{ error }}</div>
{% endif %}

{% if info %}
<div class="card mt-4 bg-secondary text-light">
<div class="card-body">
<h4 class="mb-3">{{ info.title }}</h4>
<p>Süre: {{ info.duration }} sn</p>
<p>Kanal: {{ info.uploader }}</p>

{% if info.download_url %}
<div class="ratio ratio-16x9 mb-3 bg-black rounded overflow-hidden">
<video controls class="w-100 h-100" preload="metadata">
<source src="{{ info.download_url }}" type="video/mp4">
Tarayıcınız video etiketini desteklemiyor.
</video>
</div>
<a href="/download?url={{ info.download_url }}&title={{ info.title }}" class="btn btn-primary w-100">Videoyu Cihaza İndir</a>
{% else %}
<div class="alert alert-warning">Bu video için doğrudan oynatılabilir akış bağlantısı bulunamadı.</div>
{% endif %}

</div>
</div>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    info=None
    error=None
    if request.method=="POST":
        url=request.form.get("url","")
        opts={
            "quiet": True,
            "noplaylist": True,
            "no_warnings": True,
            # X.com için en kararlı format seçimi
            "format": "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=mp4]/best",
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
                
                download_url = None
                
                # Önce doğrudan formatlar arasında mp4 uzantılı ve video içeren bir link arayalım
                formats = data.get("formats", [])
                for f in formats:
                    if f.get("ext") == "mp4" and f.get("url") and f.get("vcodec") != "none":
                        download_url = f.get("url")
                        # Eğer ses de içeriyorsa (X videoları genelde tek dosyadır) doğrudan bunu seçelim
                        if f.get("acodec") != "none":
                            break

                # Eğer formatlar arasında bulamadıysa genel url'ye bakalım
                if not download_url:
                    download_url = data.get("url")

                info={
                    "title": data.get("title") or data.get("description") or "video",
                    "duration": data.get("duration"),
                    "uploader": data.get("uploader") or data.get("uploader_id"),
                    "download_url": download_url
                }
        except Exception as e:
            error=str(e)
    return render_template_string(HTML, info=info, error=error)

@app.route("/download")
def download_file():
    video_url = request.args.get("url")
    title = request.args.get("title", "video")
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
    if not safe_title:
        safe_title = "video"
    
    if not video_url:
        return "Geçersiz bağlantı", 400

    def generate():
        try:
            r = requests.get(video_url, stream=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        except Exception:
            pass

    headers = {
        "Content-Disposition": f"attachment; filename={safe_title}.mp4",
        "Content-Type": "video/mp4"
    }
    return Response(generate(), headers=headers)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
