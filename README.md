<div align="center">
  <h1>Welcome To Ollama Manager!</h1>
  <img src="https://raw.githubusercontent.com/FOUNDATION-AI-BASED/OLLAMA-MANAGER/refs/heads/main/OLLAMA-MANAGER.webp" alt="Alt text" width="800">
</div>

<div align="center">
  
******************************************************************************************************************

<h1 align="center">Ollama Manager Webui</h1>
<p align="center">This Webui lets you easly manage ollama! No code or terminal knowledge needed just open a terminal and run the commands!</p>

<p align="center">
  <a href="https://ollama.ai">
    <img src="https://img.shields.io/badge/Powered%20by-Ollama-blue?style=flat-square" alt="Powered by Ollama">
  </a>
</p>


## ✨ Features

- 🖥️ Clean, modern interface for interacting with Ollama
- 💾 Local model storage
- 🚀 Fast and responsive
- 🔒 Privacy-focused: All proccess are being exectued locally
- ⏰ Ready to go in under 2 minutes
- ⚖️ Low resource consuming
- ✅ Ollama Based (Build on top of ollama, the webui interactes with ollamas api and your computer or server!)


## 🛣️ Roadmap

- [ ] Ui Enhancment
- ✅ Ollama Model Pulling
- ✅ Ollama Model Manager



## ✅ Systems tested on (V1.9.2) :

- [ ] MACOS MONTEREY
- [ ] MACOS SONOMA
- [~] MACOS VENTURA (Works partally! do not click update list on the install page!)
- [ ] MACOS SEQUOIA
- [ ] WINDOWS 10
- [ ] WINDOWS 11
- ✅ UBUNTU 20
- ✅ UBUNTU 22
- ✅ UBUNTU 24
- ✅ DEBIAN 12
- ✅ LINUX MINT
- ✅ Alma Linux 9.5 (localhost:5000 or 127.0.0.1:5000 only! On all Interfaces not supported therefore only on the device accessible!)
- Disclaimer Alma Linux ollama installer is only supported if you use the root user!
******************************************************************************************************************

What is this tool?

This tool lets consumer easly run ollama with no code knowledge!
With this tool you can install ollama and run it and manage ollama features like: Ollama max loaded models and more!

******************************************************************************************************************

⚠️ !!!! Ignore this if you have no knowledge or barely knowledge about programming languages etc. Just follow the guide below this!!!!!

What needs to be installed already?:

python3

python3 pip

python3 flask

python3 requests

******************************************************************************************************************

How to run this webui? (every thing will be installed automatically!)

LINUX | MACOS

Clone Repo!

git clone https://github.com/FOUNDATION-AI-BASED/OLLAMA-MANAGER.git

go into the cloned repository!

cd ollama-manager

Install required python tools!

pip install -r requirements.txt

run as sudo in order to be able to install ollama versions!

sudo python3 app.py

Or just use this:

git clone https://github.com/FOUNDATION-AI-BASED/OLLAMA-MANAGER.git && cd ollama-manager && pip install -r requirements.txt

Then run this command: sudo python3 app.py and if you are asked to enter your a password then enter your device password, it only asks for that because the tool needs previlidge to install ollama where it belongs to!

</div>

<div align="center">
  
******************************************************************************************************************

If you see this your done and you can access the webui!:

 <img src="https://raw.githubusercontent.com/FOUNDATION-AI-BASED/OLLAMA-MANAGER/refs/heads/main/terminal.webp" alt="Alt text" width="800">

You can access the webui by using either http://localhost:5000 or http://127.0.0.1:5000 or on a different device: http://192.168.51.47:5000

If you get an error open a new issue imeadiatly!

******************************************************************************************************************
STOP THE WEBUI:

To stop the Webui simply go back to the terminal and click ctrl and c on your keyboard!

******************************************************************************************************************
UNINSTALL THE WEBUI:

LINUX | MACOS

⚠️ For MACOS click first stop ollama if you plan to uninstall the webui!

simply run: pip unistall -r requirements.txt && cd .. && sudo rm -rf ollama-manager

This uninstalls everything that was installed by the webui except ollama that isn't uninstalled for that please follow this guide!:

WINDOWS: https://github.com/ollama/ollama/blob/main/docs/windows.md#uninstall

LINUX (UBUNTU 22 TESTED no others tested at the moment from our side!): https://github.com/ollama/ollama/blob/main/docs/linux.md#uninstall

MACOS: just stop ollama in the webui and delete the ollama app in the application folder!

</div>

******************************************************************************************************************

!!! IMPORTANT !!!

If you want to disable Keep Ollama Running otherwise you can't stop ollama!
