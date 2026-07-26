from flask import Flask, render_template_string, request, send_file
import yt_dlp
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <div class="container mt-5" style="max-width: 600px;">
        <h2 class="text-center mb-4">YouTube Video Downloader</h2>
        <form method="POST" class="card p-4 shadow-sm">
            <div class="form-group">
                <input type="text" name="url" class="form-control form-control-lg" placeholder="Paste YouTube URL here..." required>
            </div>
            <button type="submit" class="btn btn-success btn-lg btn-block">Download</button>
        </form>
        
        {% if error %}
            <div class="alert alert-danger mt-3">{{ error }}</div>
        {% endif %}

        {% if formats %}
            <div class="card mt-4 p-3 shadow-sm">
                <h4>{{ title }}</h4>
                <ul class="list-group mt-3">
                    {% for f in formats %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            {{ f.format_note }} ({{ f.ext }})
                            <a href="/download?url={{ url }}&format_id={{ f.format_id }}" class="btn btn-primary btn-sm">Download File</a>
                        </li>
                    {% endfor %}
                </ul>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    formats = []
    title = ""
    error = None
    url = ""
    
    if request.method == 'POST':
        url = request.form.get('url')
        try:
            ydl_opts = {
                'quiet': True,
                'extractor_args': {'youtube': {'player_client': ['android']}}
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video')
                formats = [{'format_id': f['format_id'], 'format_note': f.get('format_note', 'Standard'), 'ext': f['ext']} 
                           for f in info.get('formats', []) if f.get('vcodec') != 'none' or f.get('acodec'] != 'none']
        except Exception as e:
            error = str(e)
            
    return render_template_string(HTML_TEMPLATE, formats=formats, title=title, error=error, url=url)

@app.route('/download')
def download():
    url = request.args.get('url')
    format_id = request.args.get('format_id')
    
    output_template = 'downloads/%(title)s.%(ext)s'
    os.makedirs('downloads', exist_ok=True)
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_template,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"Download error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
