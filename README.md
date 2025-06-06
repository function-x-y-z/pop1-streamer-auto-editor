# Population One Stream Auto Editor

This tool automates the process of creating highlight clips from your Population One streams that are created used imjoh1's streaming mod. It allows you to filter clips by players and customize the duration before and after key events.

This tool is dependent on imjoh1's KillFeed mod, which is also dependent on his 'CastingMod', please reach out to him on discord for more information on these dependencies.

## Installation

Follow these steps to get the Stream Auto Editor up and running on your system.

### 1. Prerequisites

Before you begin, ensure you have the following software installed on your computer:

#### 1.1. Git

Git is a version control system used to manage the project's code.

**Installation Instructions:**

* **Windows:** Download and install Git for Windows from the official website: https://git-scm.com/download/win


After installation, you can verify it by opening your terminal or command prompt and running:

```bash
git --version 
```

#### 1.2. Python 3

Python 3 is the programming language the Stream Auto Editor is written in.

Installation Instructions:

    Windows: Download the latest Python 3 installer from the official website: https://www.python.org/downloads/windows/ Make sure to check the box that says "Add Python to PATH" during installation.

#### 1.3. FFmpeg

FFmpeg is a powerful command-line tool used for processing multimedia files, which this script relies on for video editing.

Installation Instructions:

    Windows:
        Go to the FFmpeg website: https://ffmpeg.org/download.html
        Download a pre-built binary (e.g., from a "builds" section or a third-party like BtbN builds: https://github.com/BtbN/FFmpeg-Builds/releases).
        Extract the downloaded archive to a directory on your computer (e.g., C:\FFmpeg).
        Add the bin subdirectory within the extracted FFmpeg folder to your system's PATH environment variable. This allows you to run ffmpeg commands from any terminal window. You can find instructions on how to do this by searching "add to PATH environment variable Windows".

### 2\. Getting the Code

Clone the project repository from GitHub to your local machine using Git:

```bash
git clone https://github.com/function-x-y-z/pop1-streamer-auto-editor.git
cd pop1-streamer-auto-editor
```

### 3\. Setting Up a Virtual Environment (Windows)

It's good practice to create a virtual environment to isolate the project's Python installation and dependencies.

1.  **Create the Virtual Environment:** Run the following command to create a new virtual environment named `venv`:

    ```bash
    python -m venv venv
    ```

    This command will create a `venv` folder within your project directory, containing a copy of the Python interpreter and the `pip` package installer.

### 4\. Activating the Virtual Environment (Windows)

You need to activate the virtual environment before running the script.

1.  **In Command Prompt:** Run the following command:

    ```bash
    .\venv\Scripts\activate
    ```

After successful activation, you should see `(venv)` at the beginning of your terminal prompt, indicating that the virtual environment is active.

### 5\. Installation 

    ```bash
    pip install -r requirements.txt
    ```

### 6\. Running the Stream Auto Editor (Windows)

To run the script, make sure your virtual environment is activated (see step 4) and you are in the project directory (`pop1-streamer-auto-editor`). Then execute:

```bash
python streamer-auto-editor.py