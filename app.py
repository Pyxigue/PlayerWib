from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for
import yt_dlp
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)


COOKIE_PATH = "/tmp/cookies.txt"
if "YOUTUBE_COOKIES" in os.environ:
    with open(COOKIE_PATH, "w") as f:
        f.write(os.environ["YOUTUBE_COOKIES"])


@app.route("/")
@app.route("/search")
def main():
    return render_template("index.html")

@app.route('/images/<path:filename>')
def serve_images(filename):
    images_dir = os.path.join(app.root_path, 'images')
    return send_from_directory(images_dir, filename)

@app.route('/listen', methods=['GET'])
def listen():
    return render_template("listen.html")


@app.route('/api/search', methods=['GET'])
def search_youtube():
    query = request.args.get('q')

    if not query or not query.strip():
        return jsonify({'videos': []})

    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query.strip()}", download=False)
            
            cleaned_results = []
            for entry in info.get('entries', []):
                thumbnails = entry.get('thumbnails', [])
                thumbnail_url = thumbnails[-1]['url'] if thumbnails else None

                cleaned_results.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'link': entry.get('url') or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    'thumbnail': thumbnail_url,
                    'duration': entry.get('duration'),
                    'channel': entry.get('uploader')
                })

            return jsonify({'videos': cleaned_results})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream', methods=['POST'])
def get_stream_url():
    data = request.get_json()
    
    if not data or 'id' not in data:
        return jsonify({'status': 'error', 'message': 'ID manquant'}), 400

    video_id = data.get('id')
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'ba/bestaudio/best', 
        'quiet': True,
        'noplaylist': True,
        'cookiefile': COOKIE_PATH if os.path.exists(COOKIE_PATH) else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get('url')

            if not stream_url and 'formats' in info:
                valid_formats = [f for f in info['formats'] if f.get('url')]
                audio_formats = [f for f in valid_formats if f.get('vcodec') == 'none']
                
                if audio_formats:
                    stream_url = audio_formats[-1].get('url')
                elif valid_formats:
                    stream_url = valid_formats[0].get('url')

            if not stream_url:
                return jsonify({'status': 'error', 'message': 'Impossible d\'extraire le flux'}), 500

            return jsonify({
                'status': 'success',
                'stream_url': stream_url,
                'title': info.get('title'),
                'channel': info.get('channel') or info.get('uploader') or 'Artiste inconnu',
                'thumbnail': info.get('thumbnail')
            })

    except Exception as e:
        print(f"[YTDLP STREAM ERROR]: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)