document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("download-form");
    const startButton = document.getElementById("start-button");

    const downloadPanel = document.getElementById("download-panel");
    const statusMessage = document.getElementById("status-message");

    const progressStatus = document.getElementById("progress-status");
    const progressPercent = document.getElementById("progress-percent");
    const progressFill = document.getElementById("progress-fill");

    const downloaded = document.getElementById("downloaded");
    const speed = document.getElementById("speed");
    const eta = document.getElementById("eta");

    const pauseButton = document.getElementById("pause-button");
    const resumeButton = document.getElementById("resume-button");
    const cancelButton = document.getElementById("cancel-button");

    const chooseFolderButton = document.getElementById("choose-folder-button");
    const folderStatus = document.getElementById("folder-status");

    let selectedFolder = "";
    let currentJobId = null;
    let pollTimer = null;


    function stopPolling() {
        if (pollTimer) {
            clearTimeout(pollTimer);
            pollTimer = null;
        }
    }


    function schedulePolling() {
        stopPolling();

        pollTimer = setTimeout(function () {
            if (currentJobId) {
                checkStatus();
            }
        }, 1000);
    }


    chooseFolderButton.addEventListener(
        "click",
        chooseFolder
    );
    async function chooseFolder() {

        chooseFolderButton.disabled = true;
        folderStatus.textContent = "Opening folder picker...";

        try {

            const response = await fetch(
                "/choose-folder"
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to choose folder."
                );
            }

            if (!data.folder) {
                folderStatus.textContent =
                    "No folder selected";

                selectedFolder = "";

                return;
            }

            selectedFolder = data.folder;

            folderStatus.textContent =
                data.folder;

        } catch (error) {

            folderStatus.textContent =
                error.message || "Unable to choose folder.";

        } finally {

            chooseFolderButton.disabled = false;

        }
    }


    function updateProgress(job) {

        const progress = Number(job.progress || 0);

        progressFill.style.width = `${progress}%`;
        progressPercent.textContent = `${progress}%`;

        progressStatus.textContent = job.status || "Starting...";

        downloaded.textContent = job.downloaded || "0 B";

        speed.textContent = job.speed
            ? job.speed
            : "Unknown";

        eta.textContent = job.eta
            ? `ETA: ${job.eta}`
            : "ETA: Unknown";
    }


        function updateControls(status) {

        // Reset visibility and disabled state every time.
        pauseButton.hidden = true;
        resumeButton.hidden = true;
        cancelButton.hidden = true;

        pauseButton.disabled = false;
        resumeButton.disabled = false;
        cancelButton.disabled = false;


        // Active download.
        if (
            status === "starting" ||
            status === "downloading"
        ) {
            pauseButton.hidden = false;
            cancelButton.hidden = false;
        }


        // Paused download.
        if (status === "paused") {
            resumeButton.hidden = false;
            cancelButton.hidden = false;
        }
    }



    async function checkStatus() {

        try {

            const response = await fetch(
                `/status/${currentJobId}`
            );

            const job = await response.json();

            if (!response.ok) {
                throw new Error(
                    job.error || "Unable to check download status."
                );
            }

            updateProgress(job);
            updateControls(job.status);


            if (job.status === "completed") {

                progressFill.style.width = "100%";
                progressPercent.textContent = "100%";

                progressStatus.textContent = "Completed";

                statusMessage.textContent =
                    "Download completed successfully.";

                stopPolling();

                startButton.disabled = false;
                startButton.textContent = "Download video";

                return;
            }


            if (job.status === "cancelled") {

                progressStatus.textContent = "Cancelled";

                statusMessage.textContent =
                    "Download cancelled.";

                stopPolling();

                startButton.disabled = false;
                startButton.textContent = "Download video";

                return;
            }


            if (job.status === "paused") {

                progressStatus.textContent = "Paused";

                statusMessage.textContent =
                    "Download paused.";

                startButton.disabled = false;
                startButton.textContent = "Download video";

                return;
            }


            if (job.status === "failed") {

                progressStatus.textContent = "Failed";

                statusMessage.textContent =
                    job.error || "Download failed.";

                stopPolling();

                startButton.disabled = false;
                startButton.textContent = "Download video";

                return;
            }


            schedulePolling();

        } catch (error) {

            statusMessage.textContent =
                error.message || "Unable to check download status.";

            stopPolling();

            startButton.disabled = false;
            startButton.textContent = "Download video";
        }
    }


    async function startDownload(event) {

        event.preventDefault();

        const url = document.getElementById("url").value.trim();
        const quality = document.getElementById("quality").value;

        if (!url) {
            statusMessage.textContent =
                "Please enter a YouTube URL.";

            return;
        }

        stopPolling();

        startButton.disabled = true;
        startButton.textContent = "Starting...";

        downloadPanel.hidden = false;

        progressFill.style.width = "0%";
        progressPercent.textContent = "0%";
        progressStatus.textContent = "Starting...";

        downloaded.textContent = "0 B";
        speed.textContent = "Unknown";
        eta.textContent = "ETA: Unknown";

        statusMessage.textContent =
            "Starting download...";


        try {

            const response = await fetch("/start", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    url: url,
                    quality: quality,
                    save_folder: selectedFolder
                })
            });


            const data = await response.json();


            if (!response.ok) {
                throw new Error(
                    data.error || "Unable to start download."
                );
            }


            currentJobId = data.job_id;

            startButton.textContent = "Downloading...";

            checkStatus();

        } catch (error) {

            statusMessage.textContent =
                error.message || "Unable to start download.";

            startButton.disabled = false;
            startButton.textContent = "Download video";
        }
    }


    async function pauseDownload() {

        if (!currentJobId) {
            return;
        }

        pauseButton.disabled = true;

        statusMessage.textContent =
            "Pausing download...";


        try {

            const response = await fetch(
                `/pause/${currentJobId}`,
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message || "Unable to pause download."
                );
            }

            checkStatus();

        } catch (error) {

            statusMessage.textContent =
                error.message || "Unable to pause download.";

            pauseButton.disabled = false;
        }
    }


    async function resumeDownload() {

        if (!currentJobId) {
            return;
        }

        resumeButton.disabled = true;

        statusMessage.textContent =
            "Resuming download...";


        try {

            const response = await fetch(
                `/resume/${currentJobId}`,
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message || "Unable to resume download."
                );
            }

            checkStatus();

        } catch (error) {

            statusMessage.textContent =
                error.message || "Unable to resume download.";

            resumeButton.disabled = false;
        }
    }


    async function cancelDownload() {

        if (!currentJobId) {
            return;
        }

        cancelButton.disabled = true;

        statusMessage.textContent =
            "Cancelling download...";


        try {

            const response = await fetch(
                `/cancel/${currentJobId}`,
                {
                    method: "POST"
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message || "Unable to cancel download."
                );
            }

            checkStatus();

        } catch (error) {

            statusMessage.textContent =
                error.message || "Unable to cancel download.";

            cancelButton.disabled = false;
        }
    }


    form.addEventListener(
        "submit",
        startDownload
    );

    pauseButton.addEventListener(
        "click",
        pauseDownload
    );

    resumeButton.addEventListener(
        "click",
        resumeDownload
    );

    cancelButton.addEventListener(
        "click",
        cancelDownload
    );

});





