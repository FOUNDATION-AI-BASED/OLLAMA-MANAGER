import os
import json
import requests
import subprocess
import platform
import socket
import shutil
import zipfile
import tarfile
import magic
import re
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import threading
import atexit

app = Flask(__name__)
app.secret_key = "supersecretkey"

VERSION_FILE = "version.json"
CONFIG_FILE = "config.json"

# Global variables for tracking progress
model_progress = {}
installation_status = "idle"
progress = 0

# Load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"theme": "light", "ollama_auto_start": True, "ollama_keep_running": True}

# Save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# Ensure config is loaded at startup
config = load_config()

@app.before_request
def before_request():
    session.permanent = True
    if 'theme' not in session:
        session['theme'] = config.get('theme', 'light')
    if 'ollama_auto_start' not in session:
        session['ollama_auto_start'] = config.get('ollama_auto_start', True)
    if 'ollama_keep_running' not in session:
        session['ollama_keep_running'] = config.get('ollama_keep_running', True)

# Function to start Ollama
def start_ollama_service():
    if config.get('ollama_auto_start', True):  # Use config instead of session
        host = "localhost"
        port = "11434"
        model_dir = "~/.ollama/models"
        command = f"OLLAMA_HOST={host}:{port} OLLAMA_MODEL_DIR={model_dir} ollama serve &"
        os.system(command)
        print("Ollama service started automatically.")

# Start Ollama when the WebUI starts
start_ollama_service()

# Function to stop Ollama when the WebUI stops
def stop_ollama_service():
    if not config.get('ollama_keep_running', True):  # Use config instead of session
        os.system("pkill ollama")
        print("Ollama service stopped.")

# Register the stop function to run when the WebUI exits
atexit.register(stop_ollama_service)

def get_supported_architectures(version_data):
    architectures = []
    os_types = ["Windows", "macOS", "Linux"]
    arch_types = ["amd64", "arm64", "universal"]
    
    for os_type in os_types:
        for arch in arch_types:
            download_url = version_data.get(os_type, {}).get(arch)
            if download_url and download_url.lower() not in ["none", ""]:
                architectures.append(f"{os_type.lower()}-{arch}")
    
    return sorted(architectures)

def update_version_list():
    try:
        if os.path.exists(VERSION_FILE):
            os.remove(VERSION_FILE)

        url = "https://raw.githubusercontent.com/FOUNDATION-AI-BASED/OLLAMA-VERSIONS/main/version.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            versions_data = response.json()
            enhanced_versions = {}
            for version, data in versions_data.items():
                enhanced_versions[version] = {
                    "architectures": get_supported_architectures(data),
                    **data
                }
            with open(VERSION_FILE, "w") as f:
                json.dump(enhanced_versions, f)
            return True
        return False
    except Exception as e:
        print(f"Error updating version list: {e}")
        return False

def get_file_type(file_path):
    """Detect MIME type using python-magic"""
    mime = magic.Magic(mime=True)
    return mime.from_file(file_path).lower()

def is_elf(file_path):
    """Check if file is an ELF executable using magic bytes"""
    try:
        with open(file_path, 'rb') as f:
            return f.read(4) == b'\x7fELF'
    except Exception as e:
        print(f"Error checking ELF magic bytes: {e}")
        return False

def extract_file(file_path, extract_path):
    """Extract files based on MIME type or ELF magic bytes"""
    try:
        # Check for ELF first using magic bytes
        if is_elf(file_path):
            os.makedirs(extract_path, exist_ok=True)
            dest = os.path.join(extract_path, "ollama")
            shutil.copy2(file_path, dest)
            os.chmod(dest, 0o755)
            print(f"Copied ELF binary to {extract_path}")
            return

        # Proceed with MIME type detection
        file_type = get_file_type(file_path)
        
        if file_type == 'application/zip':
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_path)
            print(f"Extracted ZIP file to {extract_path}")
        elif file_type in ['application/gzip', 'application/x-tar', 'application/x-compressed-tar']:
            with tarfile.open(file_path, "r:*") as tar_ref:
                tar_ref.extractall(extract_path)
            print(f"Extracted TAR.GZ/TGZ file to {extract_path}")
        elif 'executable' in file_type or file_type in ['application/x-executable', 'application/x-sharedlib']:
            os.makedirs(extract_path, exist_ok=True)
            dest = os.path.join(extract_path, "ollama")
            shutil.copy2(file_path, dest)
            os.chmod(dest, 0o755)
            print(f"Copied executable to {extract_path}")
        else:
            raise Exception(f"Unsupported file type: {file_type}")
    except Exception as e:
        print(f"Error during extraction: {e}")
        raise

def detect_os():
    system = platform.system().lower()
    machine = platform.machine().lower()

    os_type = "Unknown"
    if system == "windows":
        os_type = "Windows"
    elif system == "darwin":
        os_type = "macOS"
    elif system == "linux":
        os_type = "Linux"

    architecture = "amd64"
    if "arm" in machine or "aarch" in machine:
        architecture = "arm64"

    return os_type, architecture

def install_ollama(download_url):
    global progress, installation_status
    progress = 0
    installation_status = "in_progress"
    os_type, architecture = detect_os()

    if download_url.lower() == "none":
        flash(f"Your CPU architecture ({architecture}) is not supported for this version.", "error")
        installation_status = "failed"
        return False

    try:
        temp_dir = "ollama_temp"
        installer_path = os.path.join(temp_dir, "ollama_installer")
        os.makedirs(temp_dir, exist_ok=True)
        
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
                        if total_length > 0:
                            progress = int((downloaded / total_length) * 50)

        print("Download completed. Starting installation...")
        progress = 50

        extract_path = os.path.join(temp_dir, "extracted")
        extract_file(installer_path, extract_path)
        progress = 75

        # Search for the executable in the extracted directory
        extracted_file_path = None
        for root, dirs, files in os.walk(extract_path):
            for file in files:
                if file == "ollama" or file == "ollama.exe":
                    extracted_file_path = os.path.join(root, file)
                    break
            if extracted_file_path:
                break

        if not extracted_file_path:
            raise Exception(f"Extracted file 'ollama' not found in {extract_path}")

        if os_type == "Windows":
            dest_dir = "C:/Program Files/Ollama"
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, "ollama.exe")
            shutil.move(extracted_file_path, dest_path)
        else:  # macOS and Linux
            dest_path = "/usr/local/bin/ollama"
            dest_dir = os.path.dirname(dest_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            if not os.access(dest_dir, os.W_OK):
                subprocess.run(["sudo", "mv", extracted_file_path, dest_path], check=True)
                subprocess.run(["sudo", "chmod", "755", dest_path], check=True)
            else:
                shutil.move(extracted_file_path, dest_path)
                os.chmod(dest_path, 0o755)

        shutil.rmtree(temp_dir)
        progress = 100
        installation_status = "success"
        print("Installation completed successfully!")
        return True

    except Exception as e:
        print(f"Installation failed: {str(e)}")
        installation_status = "failed"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return False

def is_ollama_installed():
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_installed_ollama_version():
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "Not installed"

def get_installed_models():
    """Get list of installed models"""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output to get model names
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    model_name = line.split()[0]
                    models.append(model_name)
            return models
        return []
    except Exception as e:
        print(f"Error getting installed models: {e}")
        return []

def pull_model_task(model_name):
    global model_progress
    model_progress[model_name] = {"progress": 0, "status": "downloading"}
    
    try:
        # First check if model is already installed
        installed_models = get_installed_models()
        if model_name in installed_models:
            model_progress[model_name] = {"progress": 100, "status": "completed"}
            return True

        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"Output from ollama pull: {output.strip()}")  # Debugging: Print the output
                # Parse the output to extract progress
                if "downloading" in output.lower():
                    try:
                        # Extract progress percentage using regex
                        match = re.search(r'(\d+)%', output)
                        progress = int(match.group(1)) if match else 0
                        model_progress[model_name] = {"progress": progress, "status": "downloading"}
                    except Exception as e:
                        print(f"Error parsing progress: {e}")
                        # If progress cannot be parsed, continue
                        pass
                
        returncode = process.poll()
        if returncode == 0:
            model_progress[model_name] = {"progress": 100, "status": "completed"}
            return True
        else:
            error_output = process.stderr.read()
            print(f"Model pull failed with error: {error_output}")
            model_progress[model_name] = {"progress": 0, "status": "failed"}
            return False
            
    except Exception as e:
        print(f"Error pulling model: {e}")
        model_progress[model_name] = {"progress": 0, "status": "failed"}
        return False

@app.route("/")
def home():
    os_type, architecture = detect_os()
    ollama_installed = is_ollama_installed()
    installed_version = get_installed_ollama_version()

    if not ollama_installed:
        return render_template("home.html", os_type=os_type, architecture=architecture, 
                             ollama_installed=ollama_installed, installed_version=installed_version, 
                             redirect_to_install=True)
    
    return render_template("home.html", os_type=os_type, architecture=architecture, 
                         ollama_installed=ollama_installed, installed_version=installed_version, 
                         redirect_to_install=False)

@app.route("/install")
def install():
    if not os.path.exists(VERSION_FILE):
        update_version_list()
    with open(VERSION_FILE, "r") as f:
        versions = json.load(f)
    return render_template("install.html", versions=versions)

@app.route("/update_version_list", methods=["POST"])
def update_version_list_route():
    success = update_version_list()
    if success:
        flash("Version list updated successfully!", "success")
    else:
        flash("Failed to update version list.", "error")
    return jsonify({"success": success})

@app.route("/install_version", methods=["POST"])
def install_version():
    version = request.form.get("version")
    os_type, architecture = detect_os()

    with open(VERSION_FILE, "r") as f:
        versions = json.load(f)

    download_url = versions.get(version, {}).get(os_type, {}).get(architecture)
    if not download_url or download_url.lower() == "none":
        return jsonify({
            "success": False,
            "error": f"Download URL not found for {os_type} {architecture}"
        })

    # Start installation in a separate thread to not block
    thread = threading.Thread(target=install_ollama, args=(download_url,))
    thread.start()
    
    return jsonify({"success": True})

@app.route("/get_progress")
def get_progress():
    global progress, installation_status
    return jsonify({"progress": progress, "status": installation_status})

@app.route("/pull_model", methods=["POST"])
def pull_model():
    model_name = request.form.get("model_name")
    if not model_name:
        return jsonify({"success": False, "error": "No model name provided"})
    
    thread = threading.Thread(target=pull_model_task, args=(model_name,))
    thread.start()
    
    return jsonify({"success": True})

@app.route("/get_model_progress/<model_name>")
def get_model_progress(model_name):
    progress_data = model_progress.get(model_name, {"progress": 0, "status": "unknown"})
    return jsonify(progress_data)

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        session["ollama_max_loaded_models"] = request.form.get("ollama_max_loaded_models")
        session["ollama_num_parallel"] = request.form.get("ollama_num_parallel")
        session["ollama_max_queue"] = request.form.get("ollama_max_queue")
        session["ollama_flash_attention"] = request.form.get("ollama_flash_attention")
        session["ollama_kv_cache_type"] = request.form.get("ollama_kv_cache_type")
        session["ollama_origins"] = request.form.get("ollama_origins")
        flash("Settings saved successfully!", "success")
    return render_template("settings.html", session=session)

@app.route("/start_ollama", methods=["POST"])
def start_ollama():
    host = request.form.get("host", "localhost")
    port = request.form.get("port", "11434")
    model_dir = request.form.get("model_dir", "~/.ollama/models")

    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind((host, int(port)))
        test_socket.close()
    except socket.error:
        flash(f"Port {port} is already in use. Please use a different port.", "error")
        return redirect(url_for("home"))

    command = f"OLLAMA_HOST={host}:{port} OLLAMA_MODEL_DIR={model_dir} ollama serve &"
    os.system(command)
    flash("Ollama service started successfully!", "success")
    return redirect(url_for("home"))

@app.route("/stop_ollama", methods=["POST"])
def stop_ollama():
    if not session.get('ollama_keep_running', True):
        os.system("pkill ollama")
    flash("Ollama service stopped successfully!", "success")
    return redirect(url_for("home"))

@app.route("/shutdown")
def shutdown():
    # Stop Ollama if keep_running is disabled
    if not session.get('ollama_keep_running', True):
        os.system("pkill ollama")
    # Shutdown the WebUI
    os._exit(0)

@app.route("/delete_model", methods=["POST"])
def delete_model():
    model_name = request.form.get("model_name")
    try:
        result = subprocess.run(["ollama", "rm", model_name], capture_output=True, text=True)
        if result.returncode == 0:
            flash(f"Model '{model_name}' deleted successfully!", "success")
        else:
            flash(f"Failed to delete model '{model_name}'.", "error")
    except Exception as e:
        print(f"Error deleting model: {str(e)}")
        flash(f"Failed to delete model '{model_name}'.", "error")
    return redirect(url_for("model_manager"))

@app.route("/model_manager")
def model_manager():
    installed_models = get_installed_models()
    return render_template("model_manager.html", installed_models=installed_models)

@app.route("/set_theme", methods=["POST"])
def set_theme():
    theme = request.form.get("theme")
    if theme in ["light", "dark", "blue"]:
        session['theme'] = theme
        config['theme'] = theme
        save_config(config)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid theme"})

@app.route("/toggle_auto_start", methods=["POST"])
def toggle_auto_start():
    session['ollama_auto_start'] = not session.get('ollama_auto_start', True)
    config['ollama_auto_start'] = session['ollama_auto_start']
    save_config(config)
    return jsonify({"success": True, "ollama_auto_start": session['ollama_auto_start']})

@app.route("/toggle_keep_running", methods=["POST"])
def toggle_keep_running():
    session['ollama_keep_running'] = not session.get('ollama_keep_running', True)
    config['ollama_keep_running'] = session['ollama_keep_running']
    save_config(config)
    return jsonify({"success": True, "ollama_keep_running": session['ollama_keep_running']})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
