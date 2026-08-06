import os
import shutil
import requests
from flask import Flask, render_template, send_from_directory, request, jsonify
import yt_dlp
import requests


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

    # Liste d'instances de secours (si une est temporairement indisponible, on passe à la suivante)
    invidious_instances = [
        "https://inv.riverside.rocks",
        "https://invidious.nerdvpn.de",
        "https://yewtu.be",
        "https://invidious.drgns.space"
    ]

    for instance in invidious_instances:
        try:
            url = f"{instance}/api/v1/videos/{video_id}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                video_data = response.json()
                adaptive_formats = video_data.get('adaptiveFormats', [])
                audio_streams = [
                    fmt for fmt in adaptive_formats 
                    if fmt.get('type', '').startswith('audio/')
                ]

                if audio_streams:
                    stream_url = audio_streams[0].get('url')
                    return jsonify({
                        'status': 'success',
                        'stream_url': stream_url,
                        'title': video_data.get('title'),
                        'channel': video_data.get('author'),
                        'thumbnail': video_data.get('videoThumbnails', [{}])[-1].get('url')
                    })
        except Exception as e:
            print(f"Échec avec l'instance {instance}: {e}")
            continue 

    return jsonify({'status': 'error', 'message': 'Impossible de récupérer le flux audio depuis les API de secours.'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)