import chromedriver_autoinstaller
chromedriver_autoinstaller.install()

import subprocess
import os
import json
import time
import re
import tempfile
import threading
import urllib.request
import ctypes
import tkinter as tk
from tkinter import font as tkfont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import customtkinter as ctk

RESOURCES_DIR = os.path.join(os.getcwd(), "resources")
FONTS_DIR = os.path.join(RESOURCES_DIR, "fonts")

os.makedirs(FONTS_DIR, exist_ok=True)

FONT_PATH = os.path.join(FONTS_DIR, "SF-Pro-Display-Regular.otf")
FONT_LIGHT_PATH = os.path.join(FONTS_DIR, "SF-Pro-Display-Light.otf")

def load_custom_fonts():
    for url, path in [(FONT_PATH, FONT_LIGHT_PATH)]:
        if not os.path.exists(path) or os.path.getsize(path) < 10000:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    with open(path, "wb") as f:
                        f.write(r.read())
            except:
                pass
        if os.path.exists(path):
            try:
                if os.name == "nt":
                    ctypes.windll.gdi32.AddFontResourceExW(os.path.abspath(path), 0x10, 0)
                    ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
            except:
                pass
    
    reg_family = "Segoe UI"
    light_family = "Segoe UI"
    
    try:
        temp_app = tk.Tk()
        for family in tkfont.families(root=temp_app):
            fam_lower = family.lower()
            if "sf pro" in fam_lower:
                if "light" in fam_lower:
                    light_family = family
                else:
                    reg_family = family
        if light_family == "Segoe UI" and reg_family != "Segoe UI":
            light_family = reg_family
        temp_app.destroy()
    except:
        pass
        
    return reg_family, light_family

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

subprocess.run("color 2", shell=True)

print("""

88888888888                888       .d8888b.                    d8b                    .d8888b.   d888   
    888                    888      d88P  Y88b                   Y8P                   d88P  Y88b d8888   
    888                    888      888    888                                         Y88b. d88P   888   
    888   .d88b.   .d8888b 88888b.  888         .d88b.  88888b.  888 888  888 .d8888b   "Y88888"    888   
    888  d8P  Y8b d88P"    888 "88b 888  88888 d8P  Y8b 888 "88b 888 888  888 88K      .d8P""Y8b.   888   
    888  88888888 888      888  888 888    888 88888888 888  888 888 888  888 "Y8888b. 888    888   888   
    888  Y8b.     Y88b.    888  888 Y88b  d88P Y8b.     888  888 888 Y88b 888      X88 Y88b  d88P   888   
    888   "Y8888   "Y8888P 888  888  "Y8888P88  "Y8888  888  888 888  "Y88888  88888P'  "Y8888P"  8888888

""")

class TikTokUploader:
    def __init__(self, log_callback, done_callback, custom_caption=None):
        self.log = log_callback
        self.done = done_callback
        self.custom_caption = custom_caption
        self.driver = None

    def start(self, url, cookie_file):
        threading.Thread(target=self._run, args=(url, cookie_file), daemon=True).start()

    def _run(self, url, cookie_file):
        start_time = time.time()
        try:
            self.log("[+] Extracting", "white")

            info = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", url],
                capture_output=True, text=True
            )
            if info.returncode != 0:
                self.log("[-] Extraction Failed", "red")
                self.done()
                return

            video_info = json.loads(info.stdout)
            
            if self.custom_caption:
                base_name = self.custom_caption
                caption = self.custom_caption
            else:
                raw_title = video_info.get("title", "video")
                base_name = re.sub(r'#\w+', '', raw_title).strip()
                caption = video_info.get("description", "")
            
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', base_name)

            self.log("[+] Downloading [0%]", "white")
            
            dl_process = subprocess.Popen([
                "yt-dlp", "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                "-o", f"{safe_title}.%(ext)s",
                "--no-playlist", url
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            for line in dl_process.stdout:
                match = re.search(r'(\d+\.\d+)%', line)
                if match:
                    percent = float(match.group(1))
                    if percent >= 100.0:
                        self.log(f"[+] Downloading [100%]", "green", replace_last=True)
                    else:
                        self.log(f"[+] Downloading [{percent:.1f}%]", "white", replace_last=True)
            
            dl_process.wait()
            
            if dl_process.returncode != 0:
                self.log("[-] Download Failed", "red")
                self.done()
                return

            downloaded_file = f"{safe_title}.mp4"
            if not os.path.exists(downloaded_file):
                for f in os.listdir("."):
                    if f.endswith(".mp4") and safe_title[:10] in f:
                        downloaded_file = f
                        break
            
            if not os.path.exists(downloaded_file):
                self.log("[-] File not found", "red")
                self.done()
                return

            self.log("[+] Launching Browser", "white")

            temp_dir = tempfile.mkdtemp()
            options = Options()
            options.add_argument(f"--user-data-dir={temp_dir}")
            options.add_argument("--headless=new")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--mute-audio")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            self.driver = webdriver.Chrome(service=Service(), options=options)
            self.driver.get("https://www.tiktok.com/upload")
            time.sleep(3)

            self.log("[+] Logging In", "white")
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            for c in cookies:
                cd = {
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain", ".tiktok.com"),
                    "path": c.get("path", "/"),
                    "secure": c.get("secure", True),
                    "httpOnly": c.get("httpOnly", False),
                }
                if "expirationDate" in c:
                    cd["expiry"] = int(c["expirationDate"])
                if "sameSite" in c:
                    ss = c["sameSite"]
                    cd["sameSite"] = "None" if ss in ("no_restriction", "unspecified") else ss.capitalize()
                try:
                    self.driver.add_cookie(cd)
                except:
                    pass

            self.driver.refresh()
            time.sleep(4)

            self.log("[+] Uploading [0%]", "white")
            file_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            file_input.send_keys(os.path.abspath(downloaded_file))
            
            while True:
                percent_js = """
                var els = document.querySelectorAll('div, span');
                for (var i = 0; i < els.length; i++) {
                    var text = els[i].innerText;
                    if (text && text.trim().match(/^\\d+%$/)) {
                        return text.trim().replace('%', '');
                    }
                }
                return null;
                """
                percent_str = self.driver.execute_script(percent_js)
                if percent_str and percent_str.isdigit():
                    if percent_str == "100":
                        self.log("[+] Uploading [100%]", "green", replace_last=True)
                        break
                    else:
                        self.log(f"[+] Uploading [{percent_str}%]", "white", replace_last=True)
                
                try:
                    pb = self.driver.find_element(By.CSS_SELECTOR, "button[data-e2e='post_video_button']")
                    if pb.get_attribute("data-disabled") == "false":
                        self.log("[+] Uploading [100%]", "green", replace_last=True)
                        break
                except:
                    pass
                time.sleep(0.5)

            time.sleep(2)
            self.driver.execute_script("document.querySelectorAll('div.TUXModal-overlay, div[class*=\"modal\"], div[class*=\"overlay\"], div[class*=\"mask\"]').forEach(el => el.remove());")
            
            self.log("[+] Adding Caption", "white")
            caption_js = """
            var el = document.querySelector('div[contenteditable="true"], div.public-DraftEditor-content, div.notranslate');
            if (el) {
                el.focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('insertText', false, arguments[0]);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """
            self.driver.execute_script(caption_js, caption)
            time.sleep(3)

            for xpath in ["//button[contains(text(),'Cancel')]", "//button[contains(text(),'Turn on')]"]:
                try:
                    btn = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                except:
                    pass

            self.log("[+] Posting", "white")
            while True:
                self.driver.execute_script("document.querySelectorAll('div.TUXModal-overlay, div[class*=\"modal\"], div[class*=\"overlay\"], div[class*=\"mask\"]').forEach(el => el.remove());")
                try:
                    pb = self.driver.find_element(By.CSS_SELECTOR, "button[data-e2e='post_video_button']")
                    if pb.get_attribute("data-disabled") == "false" and pb.get_attribute("data-loading") == "false":
                        self.driver.execute_script("arguments[0].click();", pb)
                        self.log(f"Success", "green")
                        break
                    time.sleep(2)
                except:
                    time.sleep(2)

            time.sleep(5)
            try:
                os.remove(os.path.abspath(downloaded_file))
            except:
                pass

        except Exception as e:
            self.log(f"[-] Error: {str(e)[:120]}", "red")
        finally:
            if self.driver:
                self.driver.quit()
            self.done()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("https://github.com/techgenius81")
        self.geometry("850x600")
        self.configure(fg_color="#0F0F0F")
        self.is_posting = False

        self.font_family, self.font_family_light = load_custom_fonts()

        self.main_container = ctk.CTkFrame(self, fg_color="#0F0F0F", corner_radius=0)
        self.main_container.pack(fill=ctk.BOTH, expand=True, padx=40, pady=30)

        self.title_label = ctk.CTkLabel(
            self.main_container, text="Youtube Shorts 2 Tiktok", 
            font=(self.font_family, 24, "bold"), text_color="#FFFFFF"
        )
        self.title_label.pack(anchor=ctk.W, pady=(0, 20))

        self.url_label = ctk.CTkLabel(
            self.main_container, text="Link", 
            font=(self.font_family, 13), text_color="#AAAAAA"
        )
        self.url_label.pack(anchor=ctk.W, pady=(10, 5))

        self.url_entry = ctk.CTkEntry(
            self.main_container, placeholder_text="https://www.youtube.com/shorts/...",
            height=45, fg_color="#1E1E1E", border_color="#333333", text_color="#FFFFFF",
            placeholder_text_color="#555555", font=(self.font_family, 13),
            border_width=1, corner_radius=8
        )
        self.url_entry.pack(fill=ctk.X, pady=(0, 15))

        self.use_custom_caption = ctk.BooleanVar(value=False)
        self.custom_caption_cb = ctk.CTkCheckBox(
            self.main_container, text="Custom Caption", variable=self.use_custom_caption,
            command=self.toggle_custom_caption, font=(self.font_family, 13),
            text_color="#FFFFFF", checkbox_width=20, checkbox_height=20,
            fg_color="#FE2C55", hover_color="#FF3B62"
        )
        self.custom_caption_cb.pack(anchor=ctk.W, pady=(5, 8))

        self.caption_text = ctk.CTkTextbox(
            self.main_container, height=80, fg_color="#1A1A1A", border_color="#2A2A2A",
            text_color="#FFFFFF", font=(self.font_family, 13), border_width=1, corner_radius=8
        )
        self.caption_text.pack(fill=ctk.X, pady=(0, 20))
        self.caption_text.configure(state="disabled")

        self.post_btn = ctk.CTkButton(
            self.main_container, text="Post", command=self.post,
            height=46, font=(self.font_family_light, 14), text_color="#FFFFFF",
            fg_color="#FE2C55", hover_color="#FF3B62", corner_radius=23
        )
        self.post_btn.pack(fill=ctk.X, pady=(10, 25))

        self.console_label = ctk.CTkLabel(
            self.main_container, text="Console", 
            font=(self.font_family, 13), text_color="#AAAAAA"
        )
        self.console_label.pack(anchor=ctk.W, pady=(0, 5))

        self.console = ctk.CTkTextbox(
            self.main_container, fg_color="#0A0A0A", border_color="#222222",
            font=("Consolas", 12), border_width=1, corner_radius=8
        )
        self.console.pack(fill=ctk.BOTH, expand=True)
        self.console.configure(state="disabled")

        self.color_map = {"green": "#00FF66", "red": "#FF4444", "white": "#E0E0E0", "dim": "#555555"}

    def toggle_custom_caption(self):
        if self.use_custom_caption.get():
            self.caption_text.configure(state="normal", fg_color="#1E1E1E", border_color="#333333")
        else:
            self.caption_text.configure(state="disabled", fg_color="#1A1A1A", border_color="#2A2A2A")

    def log(self, msg, color="white", replace_last=False):
        self.after(0, self._update_log_ui, msg, color, replace_last)

    def _update_log_ui(self, msg, color, replace_last):
        hex_color = self.color_map.get(color, "#E0E0E0")
        self.console.configure(state="normal")
        if replace_last:
            self.console.delete("end-2l", "end-1c")
        self.console.insert("end", msg + "\n")
        end_idx = self.console.index("end-1c")
        start_idx = f"{float(end_idx)-1.0:.1f}"
        self.console.tag_config(color, foreground=hex_color)
        self.console.tag_add(color, start_idx, end_idx)
        self.console.see("end")
        self.console.configure(state="disabled")

    def post(self):
        if self.is_posting:
            return
        url = self.url_entry.get().strip()
        if not url:
            self.log("[-] No URL", "red")
            return
        cookie_file = os.path.join(os.getcwd(), "cookies.json")
        if not os.path.exists(cookie_file):
            self.log("[-] Missing cookies.json", "red")
            return

        custom_caption = None
        if self.use_custom_caption.get():
            custom_caption = self.caption_text.get("1.0", "end-1c").strip()

        self.is_posting = True
        self.post_btn.configure(state="disabled", text="Processing...", fg_color="#551122")
        self.url_entry.configure(state="disabled")
        self.caption_text.configure(state="disabled")
        self.custom_caption_cb.configure(state="disabled")
        
        TikTokUploader(
            self.log, 
            lambda: self.after(0, self._done_posting), 
            custom_caption
        ).start(url, cookie_file)

    def _done_posting(self):
        self.is_posting = False
        self.post_btn.configure(state="normal", text="Post Video", fg_color="#FE2C55")
        self.url_entry.configure(state="normal")
        self.custom_caption_cb.configure(state="normal")
        if self.use_custom_caption.get():
            self.caption_text.configure(state="normal")

if __name__ == "__main__":
    app = App()
    app.mainloop()