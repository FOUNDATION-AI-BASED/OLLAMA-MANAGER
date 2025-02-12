import os
import json
import requests
import subprocess
import platform
import socket
import shutil
import zipfile
import tarfile
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Required for session management

# Path to the local version.json file
VERSION_FILE = "version.json"

# Global variable to track installation progress
progress = 0
installation_status = "idle"  # Can be "idle", "in_progress", "success", "failed"

# Function to download the latest version.json from GitHub
def update_version_list():
    url = "https://raw.githubusercontent.com/FOUNDATION-AI-BASED/OLLAMA-VERSIONS/main/version.json"
    response = requests.get(url)
    if response.status_code == 200:
        with open(VERSION_FILE, "w") as f:
            f.write(response.text)
        return True
    return False

# Function to detect the OS and architecture
def detect_os():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        os_type = "Windows"
    elif system == "darwin":
        os_type = "macOS"
    elif system == "linux":
        os_type = "Linux"
    else:
        os_type = "Unknown"

    # Detect architecture
    if "arm" in machine or "aarch" in machine:
        architecture = "arm64"
    else:
        architecture = "amd64"

    return os_type, architecture

# Function to check if Ollama is installed
def is_ollama_installed():
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

# Function to get installed Ollama version
def get_installed_ollama_version():
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Not installed"

# Function to install Ollama
def install_ollama(download_url):
    global progress, installation_status
    progress = 0
    installation_status = "in_progress"
    os_type, architecture = detect_os()

    try:
        # Download the installer
        installer_path = "ollama_installer.zip" if os_type != "Linux" else "ollama_installer.tgz"
        print(f"Downloading installer from {download_url}...")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            total_length = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)
                        progress = int((downloaded / total_length) * 100) if total_length > 0 else 0
                        print(f"Progress: {progress}%")  # Debugging: Print progress to console

        # Extract the installer based on OS
        print(f"Extracting installer for {os_type}...")
        if os_type == "macOS":
            with zipfile.ZipFile(installer_path, "r") as zip_ref:
                zip_ref.extractall("ollama_temp")
            shutil.move("ollama_temp/ollama.app", "/Applications/ollama.app")
        elif os_type == "Linux":
            with tarfile.open(installer_path, "r:gz") as tar_ref:
                tar_ref.extractall("ollama_temp")
            shutil.move("ollama_temp/bin/ollama", "/usr/local/bin/ollama")
            shutil.move("ollama_temp/lib", "/usr/local/lib/ollama")
        elif os_type == "Windows":
            with zipfile.ZipFile(installer_path, "r") as zip_ref:
                zip_ref.extractall("ollama_temp")
            shutil.move("ollama_temp/ollama-windows-" + architecture, "C:/Program Files/Ollama")

        # Clean up
        print("Cleaning up temporary files...")
        os.remove(installer_path)
        shutil.rmtree("ollama_temp")

        progress = 100
        installation_status = "success"
        print("Installation completed successfully!")
        return True
    except Exception as e:
        print(f"Installation failed: {str(e)}")
        installation_status = "failed"
        return False

# Homepage route
@app.route("/")
def home():
    os_type, architecture = detect_os()
    ollama_installed = is_ollama_installed()
    installed_version = get_installed_ollama_version()

    if not ollama_installed:
        # Redirect to install page after 10 seconds if Ollama is not installed
        return render_template("home.html", os_type=os_type, architecture=architecture, ollama_installed=ollama_installed, installed_version=installed_version, redirect_to_install=True)
    
    return render_template("home.html", os_type=os_type, architecture=architecture, ollama_installed=ollama_installed, installed_version=installed_version, redirect_to_install=False)

# Installation page route
@app.route("/install")
def install():
    if not os.path.exists(VERSION_FILE):
        update_version_list()
    with open(VERSION_FILE, "r") as f:
        versions = json.load(f)
    return render_template("install.html", versions=versions)

# Route to update the version list
@app.route("/update_version_list", methods=["POST"])
def update_version_list_route():
    if update_version_list():
        flash("Version list updated successfully!", "success")
    else:
        flash("Failed to update version list.", "error")
    return redirect(url_for("install"))

# Route to handle version installation
@app.route("/install_version", methods=["POST"])
def install_version():
    version = request.form.get("version")
    os_type, architecture = detect_os()

    with open(VERSION_FILE, "r") as f:
        versions = json.load(f)

    # Get the download URL based on OS and architecture
    download_url = versions.get(version, {}).get(os_type, {}).get(architecture)
    if download_url:
        if install_ollama(download_url):
            flash("Installation successful!", "success")
        else:
            flash("Installation failed.", "error")
    else:
        flash("Download URL not found for the selected version and architecture.", "error")

    return jsonify({"success": True})

# Route to get installation progress
@app.route("/get_progress")
def get_progress():
    global progress, installation_status
    return jsonify({"progress": progress, "status": installation_status})

# Settings page route
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        # Save settings to session
        session["ollama_max_loaded_models"] = request.form.get("ollama_max_loaded_models")
        session["ollama_num_parallel"] = request.form.get("ollama_num_parallel")
        session["ollama_max_queue"] = request.form.get("ollama_max_queue")
        session["ollama_flash_attention"] = request.form.get("ollama_flash_attention")
        session["ollama_kv_cache_type"] = request.form.get("ollama_kv_cache_type")
        session["ollama_origins"] = request.form.get("ollama_origins")
        flash("Settings saved successfully!", "success")
    return render_template("settings.html", session=session)

# Route to start Ollama service
@app.route("/start_ollama", methods=["POST"])
def start_ollama():
    host = request.form.get("host", "localhost")
    port = request.form.get("port", "11434")
    model_dir = request.form.get("model_dir", "~/.ollama/models")

    # Check if the port is already in use
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind((host, int(port)))
        test_socket.close()
    except socket.error:
        flash(f"Port {port} is already in use. Please use a different port.", "error")
        return redirect(url_for("home"))

    # Start Ollama service
    command = f"OLLAMA_HOST={host}:{port} OLLAMA_MODEL_DIR={model_dir} ollama serve &"
    os.system(command)
    flash("Ollama service started successfully!", "success")
    return redirect(url_for("home"))

# Route to stop Ollama service
@app.route("/stop_ollama", methods=["POST"])
def stop_ollama():
    os.system("pkill ollama")
    flash("Ollama service stopped successfully!", "success")
    return redirect(url_for("home"))

# Route to shutdown the web UI
@app.route("/shutdown")
def shutdown():
    os._exit(0)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
