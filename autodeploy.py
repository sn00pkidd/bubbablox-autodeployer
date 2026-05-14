import os
import sys
import subprocess
import shutil
import random
import string
import json
import re
import secrets
import ctypes
import winreg
import urllib.request
import ssl
import zipfile
import threading
import time
import builtins
from pathlib import Path
ssl._create_default_https_context = ssl._create_unverified_context

BBRepo = "https://github.com/harryzawg/bubbablox-v2.git"
PostgresPath = r"C:\Program Files\PostgreSQL\13\bin"
RBXRegPath = r"SOFTWARE\ROBLOX Corporation\Roblox"

OrigPrint = print
def print(*args, **kwargs):
    OrigPrint(*args, **kwargs)
    try:
        Log = os.path.join(GetAppData(), "bbdeployer.log")
        with open(Log, "a", encoding="utf-8") as f:
            f.write(" ".join(str(a) for a in args) + "\n")
    except:
        pass
        
INSTALLERS = {
    "node": {
        "url": "https://nodejs.org/dist/v18.16.1/node-v18.16.1-x64.msi",
        "file": "node-v18.16.1-x64.msi",
        "cmd": 'msiexec /i "{file}" /quiet /qn /norestart'
    },
    "postgres": {
        "url": "https://sbp.enterprisedb.com/getfile.jsp?fileid=1258627",
        "file": "postgresql-13-windows-x64.exe",
        "cmd": '"{file}" --mode unattended --unattendedmodeui none --superpassword "{password}"'
    },
    "dotnet": {
        "url": "https://builds.dotnet.microsoft.com/dotnet/Sdk/6.0.412/dotnet-sdk-6.0.412-win-x64.exe",
        "file": "dotnet-sdk-6.0.412-win-x64.exe",
        "cmd": '"{file}" /quiet /norestart'
    },
    "go": {
        "url": "https://go.dev/dl/go1.20.6.windows-amd64.msi",
        "file": "go1.20.6.windows-amd64.msi",
        "cmd": 'msiexec /i "{file}" /quiet /qn /norestart'
    },
    "python": {
        "url": "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe",
        "file": "python-3.12.8-amd64.exe",
        "cmd": '"{file}" /quiet InstallAllUsers=1 PrependPath=1'
    },
    "git": {
        "url": "https://github.com/git-for-windows/git/releases/download/v2.53.0.windows.2/Git-2.53.0.2-64-bit.exe",
        "file": "Git-2.53.0.2-64-bit.exe",
        "cmd": '"{file}" /VERYSILENT /NORESTART'
    }
}

def RunCmd(command, cwd=None, shell=True, check=True, silent=False):
    if not silent:
        print(f"Running: {command}")
    try:
        result = subprocess.run(command, cwd=cwd, shell=shell, check=check, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if not check and result.returncode != 0:
            return None
        return result.stdout.strip() if result.stdout else ""
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"Error running command: {e}")
            print(f"Output: {e.output}")
            print(f"Error: {e.stderr}")
        if check:
            raise e
        return None
    except FileNotFoundError as e:
        if not silent:
            print(f"Executable not found for command: {command}")
        if check:
            raise e
        return None

class Spinner:
    def __init__(self, message="Working"):
        self.message = message
        self.running = False
        self.thread = None

    def spin(self):
        dots = 1
        while self.running:
            sys.stdout.write(f"\r{self.message}{'.' * dots}{' ' * (3 - dots)}")
            sys.stdout.flush()
            dots = dots + 1 if dots < 3 else 1
            time.sleep(0.4)
        sys.stdout.write(f"\r{' ' * (len(self.message) + 10)}\r")
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

def CheckDeps():
    deps = {
        "git": "git --version",
        "node": "node -v",
        "npm": "npm -v",
        "dotnet": "dotnet --version",
        "go": "go version",
        "python": "python --version",
        # Postgres usually is not in path but i dont really care the other check works anyway
        "postgres": "psql --version",
        "ffmpeg": "ffmpeg -version"
    }
    
    missing = []
    for name, cmd in deps.items():
        if RunCmd(cmd, check=False, silent=True) is None:
            if name == "postgres":
                if not os.path.exists(r"C:\Program Files\PostgreSQL"):
                    missing.append(name)
            elif name != "npm":
                missing.append(name)
    return missing
    
def Download(url, destination, name):
    spinner = Spinner(f"Downloading {name}")
    spinner.start()
    try:
        urllib.request.urlretrieve(url, destination)
        spinner.stop()
        return True
    except Exception as e:
        spinner.stop()
        print(f"Failed to download {name}: {e}")
        return False
  
def InstallPackages():
    packages = "fastapi aiohttp pydub uvicorn python-magic-bin==0.4.14 python-multipart cryptography"
    
    def run(cmd):
        try:
            subprocess.check_call(cmd, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    if run(f"pip install {packages}"):
        return True
        
    os.system('cls' if os.name == 'nt' else 'clear')
    if run(f"python -m pip install {packages}"):
        return True

    print("Pip failed, trying other locations")
    paths = [
        r"C:\Program Files\Python311\python.exe",
        r"C:\Program Files\Python312\python.exe",
        r"C:\Program Files\Python313\python.exe",
        r"C:\Program Files\Python314\python.exe",
        r"C:\Program Files (x86)\Python311\python.exe",
        r"C:\Program Files (x86)\Python312\python.exe",
        r"C:\Program Files (x86)\Python313\python.exe",
        r"C:\Program Files (x86)\Python314\python.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python314\python.exe"),
    ]

    for py in paths:
        if os.path.exists(py):
            print(f"Trying: {py}")
            if run(f'"{py}" -m pip install {packages}'):
                return True
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Could not install any python packages, please manually install the packages!")
    print(f"They are: {packages}")
    input("Press enter to continue...")
    return False
    
def Install(name, RealDBPass=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    info = INSTALLERS[name]
    FilePath = os.path.join(GetAppData(), info["file"])
    
    if not os.path.exists(FilePath):
        if not Download(info["url"], FilePath, name):
            return False
    if name == "postgres":
        spinner = Spinner(f"Installing {name} (This may take a while, approx 3-8 minutes)")
    else:
        spinner = Spinner(f"Installing {name}")
    spinner.start()
    cmd = info["cmd"].format(file=FilePath, password=RealDBPass)
    try:
        RunCmd(cmd, silent=True)
        spinner.stop()
        if name == "postgres":
            with open(os.path.join(GetAppData(), "pg_autoinstalled.txt"), "w") as f:
                f.write("1")
        return True
    except Exception as e:
        spinner.stop()
        print(f"Installation failed or requires manual intervention for {name}: {e}")
        return False

def InstallFFMPEG():
    os.system('cls' if os.name == 'nt' else 'clear')
    name = "ffmpeg"
    FFMpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    Destination = os.path.join(GetAppData(), "ffmpeg-release-essentials.zip")
    if not os.path.exists(Destination):
        if not Download(FFMpegUrl, Destination, name):
            return False
            
    spinner = Spinner(f"Installing {name}")
    spinner.start()
    FFMpegFolder = r"C:\ffmpeg"
    os.makedirs(FFMpegFolder, exist_ok=True)
    try:
        with zipfile.ZipFile(Destination, 'r') as ZipFileRef:
            ZipFileRef.extractall(FFMpegFolder)
            
        Bin = None
        for root, dirs, files in os.walk(FFMpegFolder):
            if "ffmpeg.exe" in files:
                Bin = root
                break
                
        if Bin:
            PathCMD = f"[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine) + ';{Bin}', [EnvironmentVariableTarget]::Machine)"
            RunCmd(f'powershell -Command "{PathCMD}"', silent=True)
            spinner.stop()
            return True
        else:
            spinner.stop()
            print("Could not find ffmpeg.exe, bad bad")
            return False
    except Exception as e:
        spinner.stop()
        print(f"Failed to extract/install FFMPEG: {e}")
        return False

def PatchFile(FilePath, SearchBytes, ReplaceBytes, ReplaceAll=True):
    if not os.path.exists(FilePath):
        print(f"File {FilePath} wasn't found, cannot patch")
        return
    
    #print(f"Patching {FilePath}...")
    with open(FilePath, 'rb') as f:
        Content = f.read()
    
    if SearchBytes not in Content:
        print(f"Couldn't find target bytes in {FilePath}, will skip this file")
        return
    
    if ReplaceAll:
        NewContent = Content.replace(SearchBytes, ReplaceBytes)
    else:
        NewContent = Content.replace(SearchBytes, ReplaceBytes, 1)
        
    if len(NewContent) != len(Content):
        print(f"Not good: Patching this file changed the file size! This will break the exe. Please make sure your RSA key generated properly.")
    
    with open(FilePath, 'wb') as f:
        f.write(NewContent)
    #print(f"Successfully patched {FilePath}")

def GetAppData():
    d = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'BBDeployer')
    os.makedirs(d, exist_ok=True)
    return d
    
def IsUserAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
        
def GetRandomStr(length=48):
    Abcdefghijklmnopqrstuvwxyz = string.ascii_letters + string.digits
    return ''.join(secrets.choice(Abcdefghijklmnopqrstuvwxyz) for i in range(length))

def CleanAppData():
    folder = GetAppData()
    for name in os.listdir(folder):
        path = os.path.join(folder, name)

        if name == "bbdeployer.log":
            continue
        
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"Couldn't delete {path} cause {e}")
            
def main():
    if not IsUserAdmin():
        print("Please restart your shell/terminal as Administrator, or just re-run this as an Administrator.")
        input("Press Enter to close...")
        sys.exit(1)

    print("BubbaBlox AutoDeployer")
    Missing = CheckDeps()
    AppData = GetAppData()
    DBPass = os.path.join(AppData, "dbpass.txt")
    
    RealDBPass = ""
    if os.path.exists(DBPass):
        with open(DBPass, "r") as f:
            RealDBPass = f.read().strip()
    else:
        RealDBPass = input("Enter the password to your database: ").strip()
        while not RealDBPass:
            RealDBPass = input("Your DB password can't be empty, please enter a new one: ").strip()
        with open(DBPass, "w") as f:
            f.write(RealDBPass)

    if Missing:
        print(f"Found dependencies to be installed: {', '.join(Missing)}, will install now...")
        
        for m in Missing:
            print(f"\nInstalling {m}...")
            if m == "ffmpeg":
                InstallFFMPEG()
            elif m in INSTALLERS:
                Install(m, RealDBPass)
            else:
                print(f"Bad dependency: {m}, skipping")
                
        print("\nDependencies installed! Please restart your terminal/shell to update your PATH, then run the deployer again.")
        input("Press Enter to continue...")
        sys.exit(0)
        
    else:
        print("Dependencies installed, continuing...")

    while True:
        #While true is stupid way to do this but easisest
        os.system('cls' if os.name == 'nt' else 'clear')
        domain = input("Enter your site domain (has to be exactly 10 characters): ").strip()
        while len(domain) != 10:
            domain = input("Your domain has to be exactly 10 characters, please reenter: ").strip()

        PGInstalled_File = os.path.join(GetAppData(), "pg_autoinstalled.txt")
        if os.path.exists(PGInstalled_File):
            # if it was installed by the script, these are the default values
            db_name = "postgres"
            db_user = "postgres"
            pg_path = PostgresPath
        else:
            # if not installed by the script , then the user should manually enter their db values
            db_name = input("Enter your PostgreSQL database name: ").strip() or "postgres"
            db_user = input("Enter your PostgreSQL username: ").strip() or "postgres"
            pg_path = input(fr"Enter your bin path where PostgreSQL was installed (example: C:\Program Files\PostgreSQL\13\bin): ").strip() or PostgresPath
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("To get your client ID and secret, you will have to make a new app here:")
        print("https://discord.com/developers/applications")
        print("Your client ID and secret will be under the OAuth2 section")
        
        input("Press enter to continue...")
        
        os.system('cls' if os.name == 'nt' else 'clear')
        ClientID = input("Enter your Discord Client ID: ").strip()
        ClientSecret = input("Enter your Discord Client Secret: ").strip()
        os.system('cls' if os.name == 'nt' else 'clear')
        WebhookURL = input("Enter your webhook URL: ").strip()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        HosterIP = input("Enter the IP of your gameserver host (example: 74.125.224.72): ").strip()
        while not HosterIP:
            HosterIP = input("The IP cannot be empty, please reenter: ").strip()
            
        GSPortRange = input("Enter your gameserver port range (example: 200-215): ").strip()
        while not re.match(r'^\d+-\d+$', GSPortRange):
            GSPortRange = input("Bad format! Use a format like 5-10, please reenter: ").strip()
            
        StartingPorty, EndingPorty = map(int, GSPortRange.split('-'))
        if StartingPorty > EndingPorty:
            StartingPorty, EndingPorty = EndingPorty, StartingPorty
        
        os.system('cls' if os.name == 'nt' else 'clear')
        AccessKey = input("Enter your RCC's AccessKey (press Enter to generate randomly): ").strip()
        if not AccessKey:
            AccessKey = GetRandomStr()
            print(f"Generated Access Key: {AccessKey}")
            
        SettingsKey = input("Enter your RCC's SettingsKey (press Enter to generate randomly): ").strip()
        if not SettingsKey:
            SettingsKey = GetRandomStr()
            print(f"Generated SettingsKey: {SettingsKey}")

        JWTKey = GetRandomStr(64)
        BotAuth = GetRandomStr(48)
        Discorkey = GetRandomStr(48)
        IPSalt = GetRandomStr(64)
        SessionAuth = GetRandomStr(48)
        # We dont use bubbamons but idk if people use the apis for bad tihngs
        BubblemonsThisIsntEvenUsed = GetRandomStr(32)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Domain: {domain}")
        print(f"Discord Client ID: {ClientID}")
        print(f"Discord Client Secret: {ClientSecret}")
        print(f"Discord Webhook: {WebhookURL}")
        print(f"Public IP: {HosterIP}")
        print(f"Port Range: {StartingPorty}-{EndingPorty}")
        print(f"Access Key: {AccessKey}")
        print(f"Settings Key: {SettingsKey}")
        
        proceed = input("Are these correct? (y/n) ").lower()
        if proceed == 'y':
            break
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Please re-enter your settings")

    os.system('cls' if os.name == 'nt' else 'clear')
    CurrentDir = os.getcwd()
    RepoName = "bubbablox-v2"
    RepoDir = os.path.join(CurrentDir, RepoName)
    
    if not os.path.exists(RepoDir):
        spinner = Spinner(f"Cloning BubbaBlox, this may take a while")
        spinner.start()
        RunCmd(f"git clone {BBRepo}", silent=True)
        spinner.stop()
    else:
        print(f"The repo's directory already exists, so we will skip cloning")
        
    os.system('cls' if os.name == 'nt' else 'clear')
    spinner = Spinner(f"Installing Python packages")
    spinner.start()
    InstallPackages()
    spinner.stop()

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Setting up DB...")
    Schema = os.path.join(RepoDir, "api", "sql", "schema.sql")
    if os.path.exists(Schema):
        DestSchema = os.path.join(pg_path, "schema.sql")
        try:
            shutil.copy(Schema, DestSchema)
            os.environ['PGPASSWORD'] = RealDBPass
            RunCmd(f'psql --username={db_user} --dbname={db_name} < schema.sql', cwd=pg_path, silent=True)
        except Exception as e:
            print(f"Failed to copy/import schema: {e}")
            input("Press enter to continue...")
    else:
        print("Schema file not found! Please check your folder and make sure the script cloned the repo correctly.")
        
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Configuring website...")
    AppSettingsExample = os.path.join(RepoDir, "Roblox", "Roblox.Website", "appsettings.example.json")
    AppSettingsRealJson = os.path.join(RepoDir, "Roblox", "Roblox.Website", "appsettings.json")
    
    if os.path.exists(AppSettingsExample):
        with open(AppSettingsExample, 'r') as f:
            Content = f.read()

        PGPattern = r'"Postgres": "Host=127\.0\.0\.1; Database=.*?; Password=.*?; Username=.*?; Maximum Pool Size=20"'
        PgReplacement = f'"Postgres": "Host=127.0.0.1; Database={db_name}; Password={RealDBPass}; Username={db_user}; Maximum Pool Size=20"'
        Content = re.sub(PGPattern, PgReplacement, Content)
        
        EscapedDir = RepoDir.replace("\\", "\\\\") + "\\\\"
        Content = Content.replace("C:\\\\Users\\\\Admin\\\\Desktop\\\\Revival\\\\ecsr\\\\ecsrev-main\\\\services\\\\", EscapedDir)
        Content = Content.replace("C:\\\\Users\\\\Admin\\\\Desktop\\\\Revival\\\\ecsr\\\\ecsrev-main\\\\services2021\\\\", EscapedDir)
        
        JsonData = json.loads(Content)
        JsonData["BaseUrl"] = f"https://{domain}"
        
        JsonData["GSIPAddress"] = HosterIP
        if "GameServer" not in JsonData:
            JsonData["GameServer"] = {}
        JsonData["GameServer"]["AllowedNetworkPorts"] = list(range(StartingPorty, EndingPorty + 1))
        
        if WebhookURL:
            JsonData["Webhook"] = WebhookURL
            JsonData["SignupWebhook"] = WebhookURL
        
        JsonData["DiscordClientID"] = ClientID
        JsonData["DiscordClientSecret"] = ClientSecret
        JsonData["DiscordRedirect"] = f"https://{domain}/discordcb"
        JsonData["DiscordForgotPasswordRedirect"] = f"https://{domain}/forgotcb"
        JsonData["DiscordLoginRedirect"] = f"https://{domain}/logincb"
        JsonData["DiscordKey"] = Discorkey
        
        JsonData["IPSalt"] = IPSalt
        JsonData["Authorization"] = SessionAuth
        JsonData["BubbamonsApiKey"] = BubblemonsThisIsntEvenUsed
        
        if "Jwt" not in JsonData:
            JsonData["Jwt"] = {}
        JsonData["Jwt"]["Sessions"] = JWTKey
        
        if "Render" in JsonData:
            JsonData["Render"]["Authorization"] = AccessKey
            
        JsonData["GameServerAuthorization"] = AccessKey 
        JsonData["RccAuthorization"] = AccessKey
        JsonData["BotAuthorization"] = BotAuth
        
        JsonData["AllowedQuietGetJson"] = [
            "ClientAppSettings",
            f"RCCService{SettingsKey}",
            "avatar-colors",
            f"RCC2015M{SettingsKey}",
            f"RCC2017E{SettingsKey}",
            "2015MAppSettings",
            "2017fflag",
            SettingsKey
        ]
        
        with open(AppSettingsRealJson, 'w') as f:
            json.dump(JsonData, f, indent=4)
        if os.path.exists(AppSettingsExample):
            os.remove(AppSettingsExample)
        print("Configured appsettings.json")

    GSExample = os.path.join(RepoDir, "Roblox", "Roblox.Website", "game-servers.example.json")
    GSJson = os.path.join(RepoDir, "Roblox", "Roblox.Website", "game-servers.json")
    if os.path.exists(GSExample):
        shutil.copy(GSExample, GSJson)
        os.remove(GSExample)
        print("Created GS Json")

    print("Configuring renderer...")
    RenderExample = os.path.join(RepoDir, "renderer", "config.example.json")
    RenderJson = os.path.join(RepoDir, "renderer", "config.json")
    if os.path.exists(RenderExample):
        with open(RenderExample, 'r') as f:
            Render_JsonData = json.load(f)
        
        if "authorization" in Render_JsonData:
            Render_JsonData["authorization"] = AccessKey
        elif "Authorization" in Render_JsonData:
            Render_JsonData["Authorization"] = AccessKey
            
        if "websiteBotAuth" in Render_JsonData:
            Render_JsonData["websiteBotAuth"] = BotAuth
        if WebhookURL and "webhook" in Render_JsonData:
            Render_JsonData["webhook"] = WebhookURL
        elif WebhookURL:
            Render_JsonData["webhook"] = WebhookURL
            
        if "baseUrl" in Render_JsonData:
            Render_JsonData["baseUrl"] = f"https://{domain}"
        if "rcc" in Render_JsonData:
            Render_JsonData["rcc"] = os.path.join(RepoDir, "RCCService")

        with open(RenderJson, 'w') as f:
            json.dump(Render_JsonData, f, indent=4)
        if os.path.exists(RenderExample):
            os.remove(RenderExample)
        print("Renderer config done")

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Creating asset folders...")
    APIDirectory = os.path.join(RepoDir, "api")
    os.makedirs(os.path.join(APIDirectory, "storage", "asset"), exist_ok=True)
    os.makedirs(os.path.join(APIDirectory, "public", "images", "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(APIDirectory, "public", "images", "groups"), exist_ok=True)

    os.system('cls' if os.name == 'nt' else 'clear')
    CorsMiddleware = os.path.join(RepoDir, "Roblox", "Roblox.Website", "Middleware", "CorsMiddleware.cs")
    if os.path.exists(CorsMiddleware):
        with open(CorsMiddleware, 'r') as f:
            cors_Content = f.read()
        cors_Content = cors_Content.replace("bbblox.org", domain)
        with open(CorsMiddleware, 'w') as f:
            f.write(cors_Content)
        print("Patched CORS with domain")

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Building frontend, may take a while...")
    BuildDirs = [
        #os.path.join(RepoDir, "admin"),
        os.path.join(RepoDir, "2016-roblox-main"),
        os.path.join(RepoDir, "renderer")
    ]

    Frontend_2016Example = os.path.join(RepoDir, "2016-roblox-main", "config.example.json")
    Frontend_2016Config = os.path.join(RepoDir, "2016-roblox-main", "config.json")
    if os.path.exists(Frontend_2016Example):
        with open(Frontend_2016Example, 'r') as f:
            Frontend_2016Content = f.read()
        Frontend_2016Content = Frontend_2016Content.replace("your.domain", domain)
        with open(Frontend_2016Config, 'w') as f:
            f.write(Frontend_2016Content)
        if os.path.exists(Frontend_2016Example):
            os.remove(Frontend_2016Example)

    for BuildDir in BuildDirs:
        if os.path.exists(BuildDir):
            print(f"Building {BuildDir}...")
            RunCmd("npm i", cwd=BuildDir, silent=True)
            RunCmd("npm run build", cwd=BuildDir, silent=True)

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Setting up registry...")
    try:
        key = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, RBXRegPath, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_32KEY)
        winreg.SetValueEx(key, "AccessKey", 0, winreg.REG_SZ, AccessKey)
        winreg.SetValueEx(key, "SettingsKey", 0, winreg.REG_SZ, SettingsKey)
        winreg.CloseKey(key)
        print("Setup reg keys")
    except Exception as e:
        print(f"Failed to set registry keys: {e}")
        input("Press enter to continue...")

    SettingsJsonDir = os.path.join(RepoDir, "Roblox", "Roblox.Libraries", "Json")
    if os.path.exists(SettingsJsonDir):
        for File in os.listdir(SettingsJsonDir):
            if "RCCService" in File and File.endswith(".json"):
                old_path = os.path.join(SettingsJsonDir, File)
                new_path = os.path.join(SettingsJsonDir, f"RCCService{SettingsKey}.json")
                shutil.move(old_path, new_path)
                #print(f"Renamed {File} to RCCService{SettingsKey}.json")
                break

    os.system('cls' if os.name == 'nt' else 'clear')
    ClientData_cs = os.path.join(RepoDir, "Roblox", "Roblox.Website", "Controllers", "Internal", "Other", "ClientData.cs")
    if os.path.exists(ClientData_cs):
        with open(ClientData_cs, 'r') as f:
            Clientdata_content = f.read()
        Clientdata_content = Clientdata_content.replace("RCCServiceBubbleRev2021RCCIsSoTuff", f"RCCService{SettingsKey}")
        with open(ClientData_cs, 'w') as f:
            f.write(Clientdata_content)
        print("Updated ClientData")

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Generating RSA keys...")
    RSADir = os.path.join(RepoDir, "Roblox", "Roblox.Website", "RSA")
    if os.path.exists(RSADir):
        RunCmd("python Generate.py", cwd=RSADir)
        print("Generated RSA")

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Patching RCCs...") 
    RCCExes = [
        os.path.join(RepoDir, "RCCService", "RCCService.exe"),
        os.path.join(RepoDir, "RCCService2018", "RCCService.exe"),
        os.path.join(RepoDir, "RCCService2020", "RCCService.exe")
    ]

    for exe in RCCExes:
        if os.path.exists(exe):
            PatchFile(exe, b"bbblox.org", domain.encode('ascii'))
            Xml = os.path.join(os.path.dirname(exe), "AppSettings.xml")
            if os.path.exists(Xml):
                with open(Xml, 'r', encoding='utf-8', errors='ignore') as f:
                    xml_Content = f.read()
                xml_Content = xml_Content.replace("bbblox.org", domain)
                with open(Xml, 'w', encoding='utf-8') as f:
                    f.write(xml_Content)
                #print(f"Patched domain in {Xml}")

    Pub2016 = os.path.join(RSADir, "PublicKey2016.pub")
    Pub2020 = os.path.join(RSADir, "PublicKey2020.pub")
    
    Old2016Pub = b"BgIAAACkAABSU0ExAAQAAAEAAQCtO8yc3tUJvc0Pc4FJH/vzPdXQ4K8H5Ai+YvITK9wIbgTzIZWJeYzd1c+HmVHcKbvn7PqtL5BfuKnhJ9p8CHbyHHuFLUc3ER/JQ7wMtnSVveQONrK6eEUeWGA0YJodA3mmY3fXiutcS886aOB68BFmnstml+R+VOYJZ9j/2vrUtA=="
    Old2018Pub = b"BgIAAACkAABSU0ExAAQAAAEAAQCjbUyx9OXTBcWEAonZOfAoT7YhMS+L21WwAZlsEjvzHXQpulpasNFhC1U6tBX6c8Qey2fiRBXHpqbh7vAC7u2niT6dMLLqY9UzII0jyxKD/EUODcQHTKpbM18FRobqLcvK0DNdIaHwypr7NRnSWk4NXhtM0v40W7/mr35PxbJ8rQ=="
    if os.path.exists(Pub2016):
        with open(Pub2016, 'r') as f:
            NewPub = f.read().strip().encode('ascii')
        
        RCC2016 = os.path.join(RepoDir, "RCCService", "RCCService.exe")
        RCC2018 = os.path.join(RepoDir, "RCCService2018", "RCCService.exe")
        PatchFile(RCC2016, Old2016Pub, NewPub)
        PatchFile(RCC2018, Old2018Pub, NewPub)

    Old2020Pub = (
        "-----BEGIN PUBLIC KEY-----\n"
        "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuVlbbNtNyRwv1ylAdC29\n"
        "BR1ZVgHthkotie/6V7EchcSghiv65VZKMsYuQWr66bKK4RXNu6hERYatv6EMltXN\n"
        "IUw6hTuDg/id4zXADX81Z9v4ayrhYTsDpLjn0PDX2AqUnE4EMbU8UwySf07UtlAv\n"
        "RDCMWz/AfqTcazHJ1MqIWnkDdSdh0nLW0Djirx+AfAZ5pNcNqUx6kxJezgXCCc3A\n"
        "SS9h1mRNEnlMkzAvuf5Lm7xO1wlXRcAJmdZGnuIKYEpvt+BJoNjbMl2+6I7SWw2x\n"
        "dOn97H8MGHFp3f9vCxzcxRtilHNUKR/AjTp1x/3qGcyfIofbsozSFdEyCXfH4Qrp\n"
        "pwIDAQAB\n"
        "-----END PUBLIC KEY-----"
    )
    # Add this at the end cause its fuckign stupiud and fat
    Old2020Bytes = Old2020Pub.encode('ascii') + b'\x0A'
    
    if os.path.exists(Pub2020):
        with open(Pub2020, 'rb') as f:
            New2020Bytes = f.read().strip() + b'\x0A'
            
        RCC2020 = os.path.join(RepoDir, "RCCService2020", "RCCService.exe")
        PatchFile(RCC2020, Old2020Bytes, New2020Bytes)
    
    CleanAppData()
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Bubba deployed! Please do these things after install")
    print("1. Go back to the Discord Developer Portal, go into your app and in the OAuth2 section add these redirect URL's:")
    print(f"\nhttps://{domain}/discordcb, https://{domain}/forgotcb, https://{domain}/logincb\n")
    print("2. Run the site with the runall.bat file in the bubbablox-v2 directory")
    print("3. Create your admin account, it can be any name (example: Roblox)")
    print("4. Go to /admin and create a player with the ID 2500, and the name as UGC.")
    print("Then create the account with the ID 12, and the name as BadDecisions. Nullify the password for UGC and BadDecisions.")
    print("Finally, download and install DirectX onto your host so 2020 can work.")
    print("You can download and get patching instructions for clients at https://zawg.ca/assets/bubbaclients")
    print(f"You will also have to forward all the ports in your port range which was {StartingPorty}-{EndingPorty}")
    print("either through your firewall or your router. (or both)")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()