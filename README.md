# Khadas Edge2 Lab: 
**_Up-to-date setup notes and some cool projects..._**

Edge2 is the latest and the most advanced embedded computer on the market, based on Rockchip RK3588S Arm64, 8nm technology. You can find out more on the official [Khadas web page](https://www.khadas.com/edge2).

**Base Hardware:**
- Khadas Edge2 Pro (16Gb Ram, 64GB eMMC, with original cooling)
- USB-C 24W, (up to 20V) charger
- USB-C Monitor
- USB-C v3.1 Cabel, with additional 4k video transfer capabilities [^1]
- Keyboard with cabel [^2]

**Hardware used for the projects**
- USB camera (Any) [^3]
- USB wired Joystick [^4]
- Arduino Mega 2560 Pro board [^5]
- LoRa E220 400T30S, 433Mhz radio modules [^6]
- Nooelec RTL-SDR v5 [^7]

**OS, Software modules**
- Ubuntu Linux Operating System. Up to date of this post, I use **UBUNTU 22.04**
- PyCharm IDE
- Arduino v2 IDE
- The native Python 3.10, and Python 3.9 for virtual environment
- For Ai, OpenCV, Mediapipe and Tensorflow is used
- PyGame and TKinter for visualisation
- FileZilla FTP client

# INITIAL SETUP
**_Last Update: 28 Jul 2023_**

_Initial Note_: The moment I decide to contribute all my work with Edge2, **was when I finally succeed to setup the device properly**. Below you can find up-to-date instructions and notes how to prepare your Edge2 for research & development purposes (R&D). Please note that **this instructions are only for UBUNTU OS**, which many people mostly prefer for R&D._ 

**1. Install the Operating System:**
>- The easiest way is with OOWOW boot firmware, that comes with the board.
>- The Operating system will be installed on your eMMC (integrated flash memory), which on the Pro version is 64GB.
>- You need **to connect your device to WiFi** (or LAN, using USB-C to Lan interface), in order to download and install the OS
>- To enter OOWOW menu, **press and release 'fun' + 'rst' buttons.** The board will restart and boot to OOWOW.
>- OOWOW works the same like the 'bios' on your regular PC, **but here you can easily download and install the latest OS, built especially for this board** from Khadas ressearch team.
>- IMPORTANT: make sure you **install the SERVER VERSION OF UBUNTU!** In order to install the OS properly with the GPU driver and your preffered desktop environment, install the server version of the OS first. Otherwise you may finish with partly working OS, with wide variaty of bugs and performance lack.

**2. Login to your new OS**
>- To login in UBUNTU OS, downloaded from Khadas (via OOWOW), use: **username: khadas  | password: khadas**

**3. Connect your OS to WiFi:**
>- The easiest way to connect to wifi via terminal (you have no desktop yet), **is with 'nmcli' module.** It is already installed, so simply type:
>```
>nmcli dev wifi connect 'myWiFi' password 'ThisIsVeryStrongPassword'
>```

**4. Create a user name you prefer**
>- This is the moment you should create the username you prefer, if you do not want to use 'khadas' username that comes with the OS.
>- Note that **YOU WILL INSTALL THE DRIVER FOR THE LOGIN USER ONLY!**.
>- If you create the user later, after you have the driver and the desktop installed, the new user will experience bugs like desktop freeze, flickering and other bad kind of stuff.
>- Also, you wont be able to setup a simple short password (easier to work with during R&D, but not preferred for security reasons), after you install the desktop environment.
>```
>sudo adduser myuser
>password: weakPss
>```

**5. Add rights of the new user as admin:***
>- Check the groups the user participates:
>`groups myuser`
>- Add the user to admin groups and other important groups:
>```
>sudo usermod -aG root myuser
>sudo usermod -aG video myuser
>sudo usermod -aG audio myuser
>sudo usermod -aG dialout myuser
>sudo usermod -aG tty myuser
>```

**6. Update:**
>```
>sudo apt update
>sudo apt upgrade
>sudo apt full-upgrade
>sudo reboot
>```

**7. Install the video driver:**
>- Note: There is a good tutorial from NikcD on the [Khadas Forum](https://forum.khadas.com/t/video-how-to-install-panfrost-gpu-driver-on-ubuntu-22-04/17501), how to install the PanFrost GPU driver on Edge2, but the driver link was moved. However, I was able to find it on another page and I simply upload it here in DRIVERS folder. 
>- Just download the `**mali_csffw.bin**` file, and transfer it to the home folder of your board via FTP client (I use FileZilla).
>- Back to ubuntu terminal, **move the file into the firmware folder:**
>```
>sudo cp mali_csffw.bin /lib/firmware
>```
>- Add a fork with some optimizetions:
>```
>sudo add-apt-repository ppa:liujianfeng1994/panfork-mesa
>```
>- Update again, so the optimization will apply:
>```
>sudo apt update && sudo apt upgrade
>```
>- You are now ready to install your preffered desktop environment. It will be installed with the PanFrost driver:
>- Important note: In some moment **the instalation freezes** with `snapd waiting to auto restart`. **Don't worry, it will continue in 5-10 minutes!**
>```
>sudo apt install ubuntu-desktop-minimal
>```
>- Other tested gnome desktops: `ubuntu-gnome-desktop`, `xubuntu-desktop`. If you preffer Cinnamon Desktop, in the [NicoD's tutorial](https://forum.khadas.com/t/video-how-to-install-panfrost-gpu-driver-on-ubuntu-22-04/17501), he saids 'gnome' should be installed first, after that, you can install Cinnamon.
>- **Voalá!** You made it to here. You have the brand new UBUNTU 22.04 OS with Desktop, ready to do cool stuff. **You can ckeck the video driver with:**
>```
>sudo apt install mesa-utils
>glxinfo -B
>```

**8. Setting-up the programming environment**
>- Note: Ubuntu 22.04 comes with Python 3.10 preinstalled. But for some projects, especially with Ai, you may need lower version of python. For example, for using 'mediapipe' module (for recognizing body motion, gestures, poses atc., python should be 3.9 or lower. In this setup, I use python 3.9 for the virtual environment.
>- Installing pip:
>```
>sudo apt install python3-dev python3-pip
>```
>- Installing essentials:
>```
>sudo apt install build-essential libssl-dev libffi-dev python3-dev
>```
>- Installing python 3.9. It will be installed allong with the native python3.10, and can be accessed via `python3.9 myscript.py`
>```
>sudo add-apt-repository ppa:deadsnakes/ppa
>sudo apt install python3.9 -y
>```
>- Get the exact version of python 3.9, to be used when virtual environment is created:
>```
>python3.9 --version
>```
>- Install the python3.9 add-ons. Note: Those are already installed in 3.10, but for this newly installed version they must be added too:
>```
>sudo apt install python3.9-dev python3.9-distutils
>```
>- Install the virtual environment module:
>```
>sudo pip3 install -U virtualenv
>```
>- Creating new virtual environment: Go to the folder where you will build yor project. There will be created the environment folder. Let's call our environment 'venv':
>```
>virtualenv --system-site-packages -p python3.9.17 ./venv
>```
>- To start the environment, type:
>```
>source ./venv/bin/activate
>```
>- Stop the environment with:
>```
>deactivate
>```
>- To remove the virtual environment for your project, simply recursively remove the 'venv' folder. Please note that **all installed modules with pip there will be removed.**
>```
>sudo rm -rf venv
>```

**9. Install packages in the new virtual environment:**
>- Important note: **When installing packages in 'venv', DO NOT TYPE `sudo`** in front of `pip`, because they will be installed in the main environment where python3.10 is, but not in the virtual environment.
>```
>pip3 install psutil
>pip3 install pygame
>pip3 install opencv-python
>pip3 install mediapipe
>pip3 install --upgrade pillow
>```
**Install Tensorflow:**
>- Note: If you followed the steps till now, all other requirements should be already satisfied. **It is important to keep protobuf==3.20.3.** This is the last version that mediapipe supports. For the newer versions (4.x..), you will start getting errors.
>```
>pip3 install scipy
>pip3 install tensorflow
>```
>- Note: Installing tensorflow, will install keras models automaticly. Numpy will also be upgraded. This won't affect the workflow of the other modules (opencv, mediapipe)

**10. Additional Stuff:**
**Enable SSH:**
>- This is not needed on Edge2, installed with official OS from OOWOW. The SSH functionality is already installed and activated. However, here is how to do it:
>```
>sudo apt install openssh-server -y
>sudo systemctl status ssh
>sudo systemctl enable --now ssh
>```
>- if you are using macbook with terminal, you may face the problem where **'Host key verification failed.'**, usually due to re-install the board (Edge2, Raspberry, etc) many times and >connect it via SSH to the same IP. To resolve this, in your macbook terminal simply type:
>```
>rm -f ~/.ssh/known_hosts
>```
>- Then you can connect to the board network ip (for example 192.168.100.33) with typing to Macbook terminal: 
>```
>ssh khadas@192.168.100.33
>```







**Notes:**
[^1]: Whehn you buy USB-C cabel for the monitor, just the 'version 3.1' and the 'fast-charge' capabilities are not enough. Make sure that is cleary stated that the cabel **is capable to transfer video**.
[^2]: For initial setup, the OOWOW integrated OS **requires wired keyboard**. Then you can use any bluetooth interface. I personally use Magic Keyboard (A1644) that can work with or without cabel).
[^3]: The camera I use is 'logi C920)', but any web camera should be fine.
[^4]: In this repo you will find an examples of using joystick with python and C++. I accidently found mine (Thrustmaster Classical USB joystick) on the local open-market, and I decide to give it a try. However, reading the data from the joystick turned out to be very easy.
[^5]: The easiest and safest way to work with external hardware is to have a microcontroller, connected via UART (or USB) to the Edge2 board. Even that the board has GPIO pins, it's always better to use the way more cheapest miccrocontrollers made especially for purpouse of using with sensors, servos, displays, etc. The unofficial Mega-Pro is ultra-small ATmega2560 based microcontroller board with 54 digital input/output pins, with pwm, analog-in, i2c, 4x uard, etc.
[^6]: Some of my projects are based on LoRa long range communication between devices. The module I use can send/receive data up to 10 Km. But you can use any LoRa module.
[^7]: There are some experiments, where I work with Software Defined Radio module to catch and use the radio-frequency data **for inserting entropy in my projects**. But there are way more cool stuff you can do with SDR's.
