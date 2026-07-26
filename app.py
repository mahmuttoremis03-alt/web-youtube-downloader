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
<input class="form-control mb-3" name="url" placeholder="Video bağlantısı (YouTube, X, Facebook, Instagram, VK...)" value="{{ request.form.get('url', '') }}">
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
<video controls class="w-100 h-100">
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
            # X (Twitter) gibi sitelerde format seçimini iyileştirmek için:
            "format": "best[ext=mp4]/best",
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
                
                download_url = None
                
                # 1. Öncelik: Doğrudan URL alanı
                if data.get("url") and not data.get("url").endswith(".m3u8"):
                    download_url = data.get("url")
                
                # 2. Öncelik: Formats listesinden en iyi mp4 formatını seçme (X.com için kritik)
                if not download_url and "formats" in data:
                    for f in data.get("formats", []):
                        if f.get("url") and f.get("vcodec") != "none":
                            # MP4 uzantılı veya doğrudan progressive linkleri tercih et
                            if f.get("ext") == "mp4":
                                download_url = f.get("url")
                                break
                    # Eğer mp4 bulunamazsa çalışabilecek herhangi bir video formatı
                    if not download_url:
                        for f in data.get("formats", []):
                            if f.get("url") and f.get("vcodec") != "none":
                                download_url = f.get("url")
                                break

                # Eğer hala bulunamadıysa data.get("url") değerini son çare alalım
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
            r = requests.get(video_url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
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
