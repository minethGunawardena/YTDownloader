import json
import tkinter as tk
from tkinter import PhotoImage
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import os
import subprocess
import sys
import requests
from io import BytesIO
import yt_dlp as ytdlp
import time

#author
#@minethGunawardena


DEFAULT_THUMBNAIL = 'Pics/nnoVideo.png'  # Path to your default thumbnail
READ_ME_FILE = 'ReadMe.md'  # Path to your ReadMe file
#osPaths
home_directory = os.path.expanduser("~")
downloads_path = os.path.join(home_directory, "Downloads")
folder_name = "YTdownloader"
folder_path = os.path.join(downloads_path, folder_name)
DEFAULT_SAVE_PATH = folder_path

# App version
APP_VERSION = '1.0.1'

####Json stuff
filename ='app_data.json'
#json Default values
app_data ={
    "Attempt":0,
    "Path":str(folder_path),
}

# Global variables
info_dict = {}
is_playlist = False
#currentPath
currentPath = DEFAULT_SAVE_PATH

def ensure_directory_exists():
    global currentPath
    data =  json.load(open(filename, "r"))
    if data["Path"] == None:
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
                print(f"Folder '{folder_name}' created at: {folder_path}")
            except Exception as e:
                print(f"An error occurred while creating the folder: {e}")
        else:
            print(f"Folder '{folder_name}' already exists at: {folder_path}")
    else:
        currentPath = data["Path"]
        save_path_var.set(currentPath)
        print("Current Path is : "+currentPath)

def newPath(directory):
    global currentPath
    data = json.load(open(filename, "r"))
    newPath = directory
    data["Path"] = newPath
    json.dump(data, open(filename, "w"))
    print("Path : "+newPath+" is Updated")
    currentPath = newPath
    save_path_var.set(currentPath)
    update_file_list()




def browse_and_save():
    directory =filedialog.askdirectory(initialdir=currentPath)
    if directory:
        newPath(directory)
        update_file_list()


def read_me_pop():
    global currentPath
    try:
        if os.path.exists(filename):
            data = json.load(open(filename,'r'))
            if data['Attempt'] > 0:
                print("Ok..!:Not the First time.")
                data['Attempt'] += 1
                json.dump(data, open(filename, 'w'))
                print("Json Updated..!")
            else:
                print("First App Run..")
                data['Attempt'] += 1
                json.dump(data, open(filename, 'w'))
                root.after(1000, show_readme)
        else:
            print("No Json File Found")
            check_for_Json()
            root.after(1000, show_readme)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. The file might be corrupted or improperly formatted.")
    except IOError as e:
        print(f"Error: An IOError occurred. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def update_quality_combobox(event=None):
    global info_dict, is_playlist
    url = url_entry.get().strip()
    if url:
        # Show loading indicator
        loading_label.grid(column=2, row=1, padx=10, pady=10, sticky='ew')
        root.update_idletasks()

        # Hide thumbnail, quality options, and file size initially
        thumbnail_label.config(image='')
        quality_combobox['values'] = []
        file_size_value_label.config(text='--')
        playlist_label.config(text='')

        def fetch_info():
            global info_dict, is_playlist
            try:
                ydl_opts = {'format': 'bestaudio/best'}
                with ytdlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    is_playlist = 'entries' in info_dict
                    if is_playlist:
                        playlist_label.config(text='This is a Playlist')
                        quality_combobox['values'] = []
                        quality_combobox.set('')
                    else:
                        playlist_label.config(text='This is a Single Video')
                        formats = info_dict.get('formats', [])

                        # Dictionary to keep track of best format for each resolution
                        best_formats = {}

                        for f in formats:
                            format_note = f.get('format_note')
                            resolution = format_note if format_note in ['144p', '360p', '480p', '720p',
                                                                        '1080p'] else None
                            if f.get('acodec') and resolution:
                                if resolution not in best_formats or f['height'] > best_formats[resolution]['height']:
                                    best_formats[resolution] = f

                        # Generate quality options from the best formats
                        quality_options = [f"{f['format']} - {f['format_note']}" for f in best_formats.values()]
                        quality_combobox['values'] = quality_options
                        if quality_options:
                            quality_combobox.set(quality_options[0])
                            update_file_size(info_dict, quality_combobox.get())
                    update_thumbnail(info_dict)
            except Exception as e:
                status_label.config(text='Error fetching info: ' + str(e))
            finally:
                # Hide loading indicator
                loading_label.grid_forget()

        threading.Thread(target=fetch_info).start()

def update_thumbnail(info_dict):
    try:
        thumbnail_url = info_dict.get('thumbnail', '')
        if thumbnail_url:
            response = requests.get(thumbnail_url)
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img = img.resize((200, 100))  # Resize to 200x100 pixels
            img_tk = ImageTk.PhotoImage(img)

            thumbnail_label.config(image=img_tk)
            thumbnail_label.image = img_tk
        else:
            default_img = Image.open(DEFAULT_THUMBNAIL)
            default_img = default_img.resize((200, 100))
            default_img_tk = ImageTk.PhotoImage(default_img)
            thumbnail_label.config(image=default_img_tk)
            thumbnail_label.image = default_img_tk
    except Exception as e:
        status_label.config(text='Error loading thumbnail: ' + str(e))

def update_file_size(info_dict, selected_quality):
    try:
        formats = info_dict.get('formats', [])
        selected_format = None
        for f in formats:
            if f['format'] in selected_quality:
                selected_format = f
                break
        if selected_format:
            file_size = selected_format.get('filesize', 'Unknown')
            if file_size:
                file_size_str = f"{file_size / (1024 * 1024):.2f} MB"  # Convert bytes to MB
            else:
                file_size_str = "Unknown"
            file_size_value_label.config(text=file_size_str)
        else:
            file_size_value_label.config(text='--')
    except Exception as e:
        file_size_value_label.config(text='Error')

def get_unique_filename(save_path, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(save_path, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def open_file(filepath):
    try:
        if sys.platform == 'win32':
            os.startfile(filepath)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', filepath])
        else:  # Linux
            subprocess.call(['xdg-open', filepath])
    except Exception as e:
        status_label.config(text='Error opening file: ' + str(e))

def open_file_and_refresh(filepath):
    time.sleep(2)
    print("opening File : " +filepath)
    root.after(1500, lambda: open_file(filepath))  # Schedule to open the file after 5000 milliseconds
    root.after(1500, update_file_list)  # Schedule to refresh the file list after 5000 milliseconds


def update_file_list():
    save_path = save_path_var.get().strip()

    # Check if the path exists
    if not os.path.exists(save_path):
        status_label.config(text='Error: Save Path does not exist!')
        return

    # List files in the save path
    file_list.delete(0, tk.END)  # Clear existing entries
    try:
        for filename in os.listdir(save_path):
            # Insert each file into the listbox
            file_list.insert(tk.END, filename)
            print(filename + "is Added To list")
    except Exception as e:
        status_label.config(text='Error loading file list: ' + str(e))

def download_video():
    url = url_entry.get().strip()
    ensure_directory_exists()
    save_path = currentPath
    print("Save Path Selected : " + save_path)
    quality = quality_combobox.get()

    if not url or not save_path:
        status_label.config(text='Error: URL or Save Path cannot be empty!')
        return

    def download_with_progress():
        global info_dict, is_playlist
        try:
            if is_playlist:
                # It's a playlist
                playlist_title = info_dict.get('title', 'Playlist')
                playlist_folder = os.path.join(save_path, playlist_title)
                ensure_directory_exists()

                ydl_opts = {
                    'outtmpl': f'{playlist_folder}/%(title)s.%(ext)s',
                    'format': 'bestaudio/best',
                    'progress_hooks': [progress_hook],
                    'merge_output_format': 'mp4',  # Ensure merging of audio and video
                }

                with ytdlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    status_label.config(text=f'Playlist "{playlist_title}" Downloaded Successfully!')
            else:
                # It's a single video
                ydl_opts = {
                    'outtmpl': f'{save_path}/%(title)s.%(ext)s',
                    'format': 'bestvideo+bestaudio/best',  # Download best video and audio
                    'progress_hooks': [progress_hook],
                    'merge_output_format': 'mp4',  # Merge audio and video into MP4
                    'verbose': True
                }

                with ytdlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    time.sleep(2)  # Give some time for the download to complete
                    title = info_dict.get('title', 'Unknown Title')
                    filename = get_unique_filename(save_path, f"{title}.mp4")
                    os.rename(os.path.join(save_path, f"{title}.mp4"), os.path.join(save_path, filename))
                    open_file_and_refresh(
                        os.path.join(save_path, filename))  # Open the file and refresh list after a delay
                    status_label.config(text=f'Video "{title}" Downloaded Successfully!')
                    update_file_list()
        except Exception as e:
            print('Error: Download Failed! : ' + str(e))

    def progress_hook(d):
        if d['status'] == 'downloading':
            status_label.config(text=f'Downloading..!')
            total_size = d.get('total_bytes', 0)
            downloaded_size = d.get('downloaded_bytes', 0)
            progress_percent = (downloaded_size / total_size) * 100 if total_size > 0 else 0
            download_progress['value'] = progress_percent
            download_speed = d.get('speed', 0) / 1024  # Speed in KB/s
            download_speed_label.config(text=f'{download_speed:.2f} KB/s')
            root.update_idletasks()

    download_thread = threading.Thread(target=download_with_progress)
    download_thread.start()

def on_listbox_double_click(event):
    selected_index = file_list.curselection()
    if selected_index:
        filename = file_list.get(selected_index)
        filepath = os.path.join(save_path_var.get(), filename)
        if os.path.exists(filepath):
            open_file(filepath)
        else:
            status_label.config(text='Error: File does not exist.')

def show_readme():
    if os.path.exists(READ_ME_FILE):
        with open(READ_ME_FILE, 'r') as file:
            readme_content = file.read()
        messagebox.showinfo("ReadMe", readme_content)
    else:
        messagebox.showwarning("ReadMe", "ReadMe file not found!")

def check_for_Json():
    if not os.path.exists(filename):
        # Write the data to the JSON file if it does not exist
        with open(filename, 'w') as file:
            json.dump(app_data, file, indent=4)
        print(f"{filename} created with initial data.")
    else:
        print(f"{filename} already exists.")




def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')


root = tk.Tk()
root.title('YouTube Downloader('+APP_VERSION+')')
#root.geometry('900x740')  # Adjust window size as needed
center_window(root,900,720)
img = PhotoImage(file='icon.png')
root.iconphoto(False,img)


# Ensure the default save path exists
#ensure_directory_exists(DEFAULT_SAVE_PATH)

# Frame for URL and Thumbnail
top_frame = ttk.Frame(root)
top_frame.grid(column=0, row=0, padx=10, pady=10, sticky='nsew')
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Thumbnail
thumbnail_label = tk.Label(top_frame, text='No Video Selected..!', relief='sunken')
thumbnail_label.grid(column=0, row=0, padx=10, pady=10, rowspan=2, sticky='nsew')
top_frame.grid_rowconfigure(0, weight=1)
top_frame.grid_columnconfigure(0, weight=1)

# URL input
url_label = ttk.Label(top_frame, text='Enter YouTube URL:')
url_label.grid(column=1, row=0, padx=10, pady=10, sticky='w')

url_entry = ttk.Entry(top_frame, width=50)
url_entry.grid(column=2, row=0, padx=10, pady=10, columnspan=2, sticky='ew')

# Loading indicator
loading_label = ttk.Label(root, text='Getting Video Info...', foreground='blue')

# Bind the URL entry to the update_quality_combobox function
url_entry.bind('<KeyRelease>', update_quality_combobox)

# Frame for Save Path and Quality
middle_frame = ttk.Frame(root)
middle_frame.grid(column=0, row=1, padx=10, pady=10, sticky='nsew')
root.grid_rowconfigure(1, weight=1)

# Save Path
save_path_label = ttk.Label(middle_frame, text='Save to:')
save_path_label.grid(column=0, row=0, padx=10, pady=10, sticky='w')

save_path_var = tk.StringVar(value=currentPath)
save_path_entry = ttk.Entry(middle_frame, textvariable=save_path_var, width=40)
save_path_entry.grid(column=1, row=0, padx=10, pady=10, sticky='ew')

browse_btn = ttk.Button(middle_frame, text='Browse',
                        command=browse_and_save)
browse_btn.grid(column=2, row=0, padx=10, pady=10)

# Quality
quality_label = ttk.Label(middle_frame, text='Quality:')
quality_label.grid(column=0, row=1, padx=10, pady=10, sticky='w')

quality_combobox = ttk.Combobox(middle_frame, width=40)
quality_combobox.grid(column=1, row=1, padx=10, pady=10, columnspan=2, sticky='ew')

# File Size
file_size_label = ttk.Label(middle_frame, text='File Size:')
file_size_label.grid(column=0, row=2, padx=10, pady=10, sticky='w')

file_size_value_label = ttk.Label(middle_frame, text='--')
file_size_value_label.grid(column=1, row=2, padx=10, pady=10, columnspan=2, sticky='ew')

# Playlist Label
playlist_label = ttk.Label(middle_frame, text='')
playlist_label.grid(column=0, row=3, padx=10, pady=10, columnspan=3, sticky='w')

# Bind quality_combobox selection change to update_file_size
quality_combobox.bind('<<ComboboxSelected>>', lambda event: update_file_size(info_dict, quality_combobox.get()))

# Download Button
download_btn = ttk.Button(root, text='Download', command=download_video)
download_btn.grid(column=0, row=2, columnspan=3, padx=10, pady=10, sticky='ew')

# Progress Bar
download_progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, mode='determinate')
download_progress.grid(column=0, row=3, columnspan=3, padx=10, pady=10, sticky='ew')

# Download Speed
download_speed_label = ttk.Label(root, text='0 KB/s')
download_speed_label.grid(column=0, row=4, columnspan=3, padx=10, pady=5)

# Status Label
status_label = ttk.Label(root, text='', foreground='red')
status_label.grid(column=0, row=5, columnspan=3, padx=10, pady=5)

# File List
file_list_frame = ttk.Frame(root)
file_list_frame.grid(column=0, row=6, padx=10, pady=10, sticky='nsew')

file_list_label = ttk.Label(file_list_frame, text='Downloaded Files:')
file_list_label.grid(column=0, row=0, padx=10, pady=5, sticky='w')

file_list = tk.Listbox(file_list_frame, width=80, height=10)
file_list.grid(column=0, row=1, padx=10, pady=5, sticky='nsew')
file_list_frame.grid_rowconfigure(1, weight=1)
file_list_frame.grid_columnconfigure(0, weight=1)

# Bind double-click event to the listbox
file_list.bind('<Double-1>', on_listbox_double_click)


# Bottom Panel
bottom_frame = ttk.Frame(root)
bottom_frame.grid(column=0, row=7, padx=10, pady=10, sticky='ew')
bottom_frame.grid_columnconfigure(0, weight=1)
bottom_frame.grid_columnconfigure(1, weight=1)

# App Version
version_label = ttk.Label(bottom_frame, text=f'App Version: {APP_VERSION}', anchor='w')
version_label.grid(column=0, row=0, padx=10, pady=5, sticky='w')

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(7, weight=1)
read_me_pop()
####gui End#############
def main():
    check_for_Json()
    ensure_directory_exists()
    update_file_list()
    root.mainloop()



if __name__ == "__main__":
    main()


