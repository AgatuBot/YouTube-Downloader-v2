import os
import threading
import uuid

import yt_dlp


DOWNLOAD_FOLDER = "downloads"

FFMPEG_LOCATION = (
    r"C:\Users\ADMIN\Downloads\ffmpeg"
    r"\ffmpeg-9.0.2-essentials_build\bin"
)

jobs = {}
jobs_lock = threading.Lock()


class DownloadCancelled(Exception):
    pass


def create_job(url, quality, save_folder):
    job_id = str(uuid.uuid4())

    job = {
        "id": job_id,
        "url": url,
        "quality": quality,
        "save_folder": save_folder,
        "status": "starting",
        "progress": 0,
        "downloaded": "0 B",
        "total": "Unknown",
        "speed": "Unknown",
        "eta": "Unknown",
        "error": None,
        "cancel_requested": False,
        "pause_requested": False,
    }

    with jobs_lock:
        jobs[job_id] = job

    thread = threading.Thread(
        target=_run_download,
        args=(job_id, False),
        daemon=True,
    )

    thread.start()

    return job_id


def get_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return None

        return job.copy()


def request_cancel(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return False

        if job["status"] in {
            "completed",
            "cancelled",
            "failed",
            "already_exists",
        }:
            return False

        if job["status"] == "paused":
            job["cancel_requested"] = True
            job["pause_requested"] = False
            job["status"] = "cancelled"
            job["error"] = None
            return True

        job["cancel_requested"] = True
        job["pause_requested"] = False

        return True


def request_pause(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return False

        if job["status"] not in {
            "starting",
            "downloading",
        }:
            return False

        job["pause_requested"] = True

        return True


def request_resume(job_id):
    with jobs_lock:
        job = jobs.get(job_id)

        if job is None:
            return False

        if job["status"] != "paused":
            return False

        job["pause_requested"] = False
        job["status"] = "starting"

    thread = threading.Thread(
        target=_run_download,
        args=(job_id, True),
        daemon=True,
    )

    thread.start()

    return True


def _update_job(job_id, **updates):
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(updates)


def _snapshot_mp4_files():
    snapshot = {}

    if not os.path.isdir(DOWNLOAD_FOLDER):
        return snapshot

    for filename in os.listdir(DOWNLOAD_FOLDER):

        if not filename.lower().endswith(".mp4"):
            continue

        path = os.path.join(
            DOWNLOAD_FOLDER,
            filename,
        )

        try:
            stat = os.stat(path)

            snapshot[path] = (
                stat.st_size,
                stat.st_mtime_ns,
            )

        except OSError:
            continue

    return snapshot


def _has_new_or_changed_mp4(before, after):
    for path, state in after.items():

        if path not in before:
            return True

        if before[path] != state:
            return True

    return False


def _progress_hook(job_id, data):
    status = data.get("status")

    if status != "downloading":
        return

    downloaded = data.get(
        "downloaded_bytes",
        0,
    )

    total = (
        data.get("total_bytes")
        or data.get("total_bytes_estimate")
        or 0
    )

    progress = 0

    if total:
        progress = round(
            (downloaded / total) * 100,
            1,
        )

    speed = data.get("speed")

    if speed:
        speed_text = (
            f"{speed / 1024 / 1024:.2f} MiB/s"
        )
    else:
        speed_text = "Unknown"

    eta = data.get("eta")

    if eta is not None:
        minutes, seconds = divmod(
            int(eta),
            60,
        )

        if minutes:
            eta_text = (
                f"{minutes}m {seconds}s"
            )
        else:
            eta_text = f"{seconds}s"
    else:
        eta_text = "Unknown"

    _update_job(
        job_id,
        status="downloading",
        progress=progress,
        downloaded=_format_bytes(downloaded),
        total=(
            _format_bytes(total)
            if total
            else "Unknown"
        ),
        speed=speed_text,
        eta=eta_text,
    )

    with jobs_lock:
        job = jobs.get(job_id)

        if job:

            if job["cancel_requested"]:
                raise DownloadCancelled(
                    "cancelled"
                )

            if job["pause_requested"]:
                raise DownloadCancelled(
                    "paused"
                )


def _run_download(job_id, resume=False):

    job = get_job(job_id)

    if not job:
        return

    save_folder = job["save_folder"]

    os.makedirs(
        save_folder,
        exist_ok=True,
    )

    height = int(job["quality"])

    job_marker = f"[job-{job_id}]"



    if resume:
        continue_download = True
        force_overwrites = False
    else:
        continue_download = False
        force_overwrites = True

    ydl_opts = {
        "format": (
            f"bestvideo[height<={height}]"
            f"+bestaudio/"
            f"best[height<={height}]"
        ),

        "outtmpl": os.path.join(
            save_folder,
            f"%(title)s [%(id)s] [{height}p] {job_marker}.%(ext)s",
        ),

        "merge_output_format": "mp4",

        "ffmpeg_location": FFMPEG_LOCATION,

        "noplaylist": True,

        "js_runtimes": {
            "deno": {}
        },

        "force_overwrites": force_overwrites,

        "continuedl": continue_download,

        "nopart": False,

        "retries": 10,

        "fragment_retries": 10,

        "progress_hooks": [
            lambda data: _progress_hook(
                job_id,
                data,
            )
        ],
    }

    try:

        _update_job(
            job_id,
            status="starting",
            error=None,
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            result = ydl.download(
                [job["url"]]
            )

        current = get_job(job_id)

        if not current:
            return

        if current["cancel_requested"]:

            _update_job(
                job_id,
                status="cancelled",
                error=None,
            )

            return

        if current["pause_requested"]:

            _update_job(
                job_id,
                status="paused",
                error=None,
            )

            return

        if result != 0 and resume:

            for filename in os.listdir(save_folder):

                if (
                    job_marker in filename
                    and (
                        filename.endswith(".part")
                        or filename.endswith(".ytdl")
                    )
                ):

                    try:
                        os.remove(
                            os.path.join(
                                save_folder,
                                filename,
                            )
                        )
                    except OSError:
                        pass

            retry_opts = dict(ydl_opts)

            retry_opts["continuedl"] = False
            retry_opts["force_overwrites"] = False

            with yt_dlp.YoutubeDL(retry_opts) as ydl:

                result = ydl.download(
                    [job["url"]]
                )

        if result != 0:

            _update_job(
                job_id,
                status="failed",
                error=(
                    f"yt-dlp returned code {result}"
                ),
            )

            return

        job_files = []

        for filename in os.listdir(save_folder):

            if (
                job_marker in filename
                and filename.lower().endswith(".mp4")
            ):

                job_files.append(
                    os.path.join(
                        save_folder,
                        filename,
                    )
                )

        if not job_files:

            _update_job(
                job_id,
                status="failed",
                error=(
                    "Download completed, but the final MP4 file "
                    "could not be found."
                ),
            )

            return

        temporary_file = job_files[0]

        temporary_name = os.path.basename(
            temporary_file
        )

        clean_name = temporary_name.replace(
            f" {job_marker}.mp4",
            ".mp4",
        )

        final_file = os.path.join(
            save_folder,
            clean_name,
        )

        counter = 1

        while os.path.exists(final_file):

            name_without_extension = os.path.splitext(
                clean_name
            )[0]

            final_file = os.path.join(
                save_folder,
                f"{name_without_extension} ({counter}).mp4",
            )

            counter += 1

        os.replace(
            temporary_file,
            final_file,
        )

        _update_job(
            job_id,
            status="completed",
            progress=100,
            speed="",
            eta="",
            error=None,
        )

    except DownloadCancelled as exc:

        reason = str(exc)

        current = get_job(job_id)

        if not current:
            return

        if reason == "cancelled":

            _update_job(
                job_id,
                status="cancelled",
                error=None,
            )

        elif reason == "paused":

            _update_job(
                job_id,
                status="paused",
                error=None,
            )

    except Exception as exc:

        _update_job(
            job_id,
            status="failed",
            error=str(exc),
        )


def _format_bytes(value):

    if not value:
        return "0 B"

    units = [
        "B",
        "KiB",
        "MiB",
        "GiB",
    ]

    size = float(value)

    for unit in units:

        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} GiB"









