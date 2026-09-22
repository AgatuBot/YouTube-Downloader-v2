import os

if os.name == "nt":
    import tkinter as tk
    from tkinter import filedialog

from flask import Flask, render_template, request, jsonify, send_file
from downloader import (
    create_job,
    get_job,
    request_cancel,
    request_pause,
    request_resume,
)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/choose-folder", methods=["GET"])
def choose_folder():
    if os.name != "nt":
        return jsonify({"folder": "downloads"})

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    folder = filedialog.askdirectory(
        title="Choose download folder"
    )

    root.destroy()

    return jsonify({
        "folder": folder
    })


@app.route("/start", methods=["POST"])
def start_download():
    data = request.get_json(silent=True) or {}

    url = data.get("url", "").strip()
    quality = data.get("quality", "360")
    save_folder = data.get("save_folder", "").strip()

    if not save_folder:
        save_folder = "downloads"

    if not url:
        return jsonify({
            "error": "Please enter a YouTube URL."
        }), 400

    if quality not in {"360", "480", "720"}:
        return jsonify({
            "error": "Invalid video quality."
        }), 400

    job_id = create_job(url, quality, save_folder)

    return jsonify({
        "job_id": job_id
    })


@app.route("/status/<job_id>", methods=["GET"])
def download_status(job_id):
    job = get_job(job_id)

    if job is None:
        return jsonify({
            "error": "Download job not found."
        }), 404

    return jsonify(job)


@app.route("/download/<job_id>", methods=["GET"])
def download_file(job_id):
    job = get_job(job_id)

    if job is None or job.get("status") != "completed":
        return jsonify({
            "error": "Download file is not available."
        }), 404

    file_path = job.get("file_path")

    if not file_path or not os.path.isfile(file_path):
        return jsonify({
            "error": "Download file is no longer available."
        }), 404

    return send_file(
        file_path,
        as_attachment=True
    )


@app.route("/pause/<job_id>", methods=["POST"])
def pause_download(job_id):
    if request_pause(job_id):
        return jsonify({
            "success": True,
            "message": "Pause requested."
        })

    return jsonify({
        "success": False,
        "message": "Unable to pause this download."
    }), 400


@app.route("/resume/<job_id>", methods=["POST"])
def resume_download(job_id):
    if request_resume(job_id):
        return jsonify({
            "success": True,
            "message": "Resume requested."
        })

    return jsonify({
        "success": False,
        "message": "Unable to resume this download."
    }), 400


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_download(job_id):
    if request_cancel(job_id):
        return jsonify({
            "success": True,
            "message": "Cancellation requested."
        })

    return jsonify({
        "success": False,
        "message": "Unable to cancel this download."
    }), 400


from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

@app.route("/youtube-check", methods=["GET"])
def youtube_check():
    url = "https://www.youtube.com/watch?v=BaW_jenozKc"
    try:
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urlopen(request, timeout=20) as response:
            return jsonify({
                "status": response.status,
                "message": "YouTube request succeeded."
            })
    except HTTPError as error:
        return jsonify({
            "status": error.code,
            "message": "YouTube returned an HTTP error."
        }), 200
    except URLError as error:
        return jsonify({
            "status": None,
            "message": "Unable to reach YouTube.",
            "reason": str(error.reason)
        }), 200
    except Exception as error:
        return jsonify({
            "status": None,
            "message": "Unexpected error.",
            "reason": str(error)
        }), 200

if __name__ == "__main__":
    app.run(debug=False)
