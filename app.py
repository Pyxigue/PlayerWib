from flask import Flask, render_template, send_from_directory, request, jsonify
import yt_dlp
from yt_dlp import YoutubeDL
import os, shutil

app = Flask(__name__)


def get_cookie_path():
    secret_path = "/etc/secrets/cookies.txt"
    tmp_path = "/tmp/cookies.txt"
    if os.path.exists(secret_path):
        shutil.copyfile(secret_path, tmp_path)
        return tmp_path

    return "cookies.txt" if os.path.exists("cookies.txt") else None



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

    cookie_file = get_cookie_path()

    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query.strip()}", download=False)
            if not info or 'entries' not in info:
                return jsonify({'videos': []})

            cleaned_results = []
            for entry in info.get('entries', []):
                if not entry:
                    continue
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
    
    # Récupération du chemin des cookies (copié dans /tmp pour éviter l'erreur Read-Only)
    cookie_file = get_cookie_path()

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Force des clients stables pour éviter SABR et PO-Token
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "web"]
            }
        }
    }

    # Si le fichier cookie existe dans /tmp ou localement, on l'injecte
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # 🛡️ Protection contre l'erreur 403 / NoneType
            if not info:
                return jsonify({'status': 'error', 'message': 'Impossible d\'extraire les infos (IP bloquée ou vidéo indisponible)'}), 500

            stream_url = info.get('url')

            # Si le lien direct n'est pas à la racine, on va le chercher dans les formats
            if not stream_url and 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('url'):
                        stream_url = fmt.get('url')
                        break

            if not stream_url:
                return jsonify({'status': 'error', 'message': 'Impossible d\'extraire le flux audio'}), 500

            thumbnail = info.get('thumbnail')

            return jsonify({
                'status': 'success',
                'stream_url': stream_url,
                'title': info.get('title'),
                'channel': info.get('channel') or info.get('uploader') or 'Artiste inconnu',
                'thumbnail': thumbnail
            })

    except Exception as e:
        print(f"Error : {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)