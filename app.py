import os
import shutil
import requests
from flask import Flask, render_template, send_from_directory, request, jsonify
import yt_dlp


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

    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        print("Erreur: Clé YOUTUBE_API_KEY non configurée")
        return jsonify({'error': 'Clé API non configurée'}), 500

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query.strip(),
        'type': 'video',
        'maxResults': 10,
        'key': api_key
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code != 200:
            print(f"Erreur API YouTube: {data}")
            return jsonify({'error': 'Erreur lors de la recherche'}), 500

        cleaned_results = []
        for item in data.get('items', []):
            snippet = item.get('snippet', {})
            video_id = item.get('id', {}).get('videoId')

            if video_id:
                thumbnails = snippet.get('thumbnails', {})
                # Récupère la meilleure résolution de miniature disponible
                thumb_data = thumbnails.get('high') or thumbnails.get('medium') or thumbnails.get('default') or {}
                
                cleaned_results.append({
                    'id': video_id,
                    'title': snippet.get('title'),
                    'link': f"https://www.youtube.com/watch?v={video_id}",
                    'thumbnail': thumb_data.get('url'),
                    'channel': snippet.get('channelTitle')
                })

        return jsonify({'videos': cleaned_results})

    except Exception as e:
        print(f"Error search: {e}")
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/stream', methods=['POST'])
def get_stream_url():
    data = request.get_json()
    
    if not data or 'id' not in data:
        return jsonify({'status': 'error', 'message': 'ID manquant'}), 400

    video_id = data.get('id')
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    cookie_file = get_cookie_path()

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "web"]
            }
        }
    }

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if not info:
                return jsonify({'status': 'error', 'message': 'Impossible de lire les informations de la vidéo'}), 500

            stream_url = info.get('url')

            if not stream_url and 'formats' in info and info['formats']:
                for fmt in info['formats']:
                    if fmt.get('acodec') != 'none' and fmt.get('url'):
                        stream_url = fmt.get('url')
                        break

            if not stream_url:
                return jsonify({'status': 'error', 'message': 'Impossible d\'extraire le flux audio'}), 500

            return jsonify({
                'status': 'success',
                'stream_url': stream_url,
                'title': info.get('title'),
                'channel': info.get('channel') or info.get('uploader') or 'Artiste inconnu',
                'thumbnail': info.get('thumbnail')
            })

    except Exception as e:
        print(f"Error stream : {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)