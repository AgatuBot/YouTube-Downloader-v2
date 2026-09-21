# YouTube Downloader



A lightweight Flask-based YouTube video downloader with quality selection, download progress tracking, pause/resume controls, cancellation, and a custom local save-location option.



> **Live Demo:** Coming soon - the application is being prepared for deployment on Render.



## Features



* YouTube video downloads using `yt-dlp`

* 360p, 480p, and 720p quality selection

* Real-time download progress

* Download percentage

* Downloaded size, speed, and ETA

* Pause and resume support

* Download cancellation

* Custom local save-folder selection

* Automatic MP4 merging through FFmpeg

* Duplicate downloads are preserved instead of overwritten

* Browser-based interface

* Responsive layout

* Responsible-use and copyright notice



## Technology Stack



| Technology | Purpose                                    |

| ---------- | ------------------------------------------ |

| Python     | Application logic                          |

| Flask      | Web application framework                  |

| yt-dlp     | Video download engine                      |

| FFmpeg     | Video/audio processing and MP4 merging     |

| HTML5      | Application structure                      |

| CSS3       | User interface styling                     |

| JavaScript | Frontend interaction and progress updates  |

| Gunicorn   | Production web server for cloud deployment |

| Render     | Cloud deployment platform                  |



## Application Workflow



```text

User

&#x20; â”‚

&#x20; â–¼

Web Interface

&#x20; â”‚

&#x20; â–¼

Flask Application

&#x20; â”‚

&#x20; â–¼

Download Manager

&#x20; â”‚

&#x20; â”œâ”€â”€ yt-dlp

&#x20; â”‚

&#x20; â””â”€â”€ FFmpeg

&#x20; â”‚

&#x20; â–¼

Downloaded MP4

```



## Project Structure



```text

YouTube-Downloader-v2/

â”‚

â”œâ”€â”€ app.py

â”œâ”€â”€ downloader.py

â”œâ”€â”€ requirements.txt

â”œâ”€â”€ README.md

â”œâ”€â”€ .gitignore

â”‚

â”œâ”€â”€ static/

â”‚   â”œâ”€â”€ css/

â”‚   â”‚   â””â”€â”€ style.css

â”‚   â””â”€â”€ js/

â”‚       â””â”€â”€ app.js

â”‚

â””â”€â”€ templates/

&#x20;   â””â”€â”€ index.html

```



## Local Installation



### 1. Clone the repository



```bash

git clone YOUR_GITHUB_REPOSITORY_URL

cd YouTube-Downloader-v2

```



Replace `YOUR_GITHUB_REPOSITORY_URL` with the actual GitHub repository URL.



### 2. Create a virtual environment



On Windows PowerShell:



```powershell

python -m venv .venv

```



### 3. Activate the virtual environment



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



### 4. Install the dependencies



```powershell

pip install -r requirements.txt

```



### 5. Install FFmpeg



FFmpeg is required when separate video and audio streams need to be merged.



For the local Windows version, configure the FFmpeg location in `downloader.py` according to your local FFmpeg installation.



### 6. Start the application



```powershell

python .\\app.py

```



Then open:



```text

http://127.0.0.1:5000

```



## Usage



1\. Enter a YouTube video URL.

2\. Select the desired video quality.

3\. Click **Choose folder** to select a local destination.

4\. Click **Download video**.

5\. Monitor the download progress.

6\. Use **Pause** when you need to temporarily stop a




