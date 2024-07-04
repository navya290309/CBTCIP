import tkinter as tk
from tkinter import messagebox, Toplevel, Listbox, Entry
from PIL import Image, ImageTk, ImageSequence
import pyaudio
import wave
import threading
import time
import os
import numpy as np

class VoiceRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Recorder")
        self.root.configure(bg='#050f28')
        self.root.geometry("500x500")

        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        self.filename_base = "recorded_audio"
        self.counter = 1
        self.frames = []

        self.is_recording = False
        self.is_paused = False
        self.is_gif_running = True
        self.elapsed_time = 0
        self.pause_start_time = 0

        self.p = pyaudio.PyAudio()

        self.create_widgets()

    def create_widgets(self):
        self.info_label = tk.Label(self.root, text="Press the button to start recording:", bg='#050f28', fg='white', font=("Helvetica", 16))
        self.info_label.pack(pady=20)

        self.mic_button = tk.Button(self.root, text="Start", command=self.start_recording, bg='#8DECB4', fg='black', font=("Helvetica", 16), width=12, height=2, borderwidth=0)
        self.mic_button.pack(pady=20)
        self.mic_button.config(relief="groove", borderwidth=2)

        self.status_label = tk.Label(self.root, text="", bg='#050f28', fg='white', font=("Helvetica", 14))
        self.status_label.pack(pady=20)

        self.show_recordings_button = tk.Button(self.root, text="Show Recordings", command=self.show_recordings, bg='orange', font=("Helvetica", 14))
        self.show_recordings_button.pack(pady=20)

    def start_recording(self):
        self.is_recording = True
        self.is_paused = False
        self.is_gif_running = True
        self.mic_button.config(bg='#15F5BA', text="Recording", state=tk.DISABLED)
        self.status_label.config(text="Recording...")

        self.start_time = time.time()
        self.elapsed_time = 0
        self.frames = []
        threading.Thread(target=self.record_audio).start()

        self.control_window = Toplevel(self.root)
        self.control_window.title("Recording Controls")
        self.control_window.geometry("400x300")
        self.control_window.configure(bg='#050f28')

        self.pause_resume_button = tk.Button(self.control_window, text="Pause Recording", command=self.toggle_pause_resume, bg='#37B7C3', font=("Helvetica", 14))
        self.pause_resume_button.pack(pady=20)

        self.stop_button = tk.Button(self.control_window, text="Stop Recording", command=self.stop_recording, bg='red', font=("Helvetica", 14))
        self.stop_button.pack(pady=20)

        self.timer_label = tk.Label(self.control_window, text="Timer: 0 seconds", bg='#050f28', fg='white', font=("Helvetica", 16))
        self.timer_label.pack(pady=20)

        self.update_timer()

        # Load and display the GIF
        self.display_gif()

    def display_gif(self):
        gif_path = "gif.gif"
        self.gif_image = Image.open(gif_path)
        self.gif_frames = [ImageTk.PhotoImage(img) for img in ImageSequence.Iterator(self.gif_image)]

        self.gif_label = tk.Label(self.control_window, bg='#050f28')
        self.gif_label.pack(pady=10)
        self.update_gif(0)

    def update_gif(self, frame_index):
        if self.is_gif_running:
            frame = self.gif_frames[frame_index]
            self.gif_label.config(image=frame)
            frame_index = (frame_index + 1) % len(self.gif_frames)
        self.control_window.after(100, self.update_gif, frame_index)

    def stop_recording(self):
        self.is_recording = False
        self.is_paused = False
        self.mic_button.config(bg='#8DECB4', text="Start", state=tk.NORMAL)
        self.status_label.config(text="Recording finished.")
        self.control_window.destroy()
        self.show_save_edit_window()

    def toggle_pause_resume(self):
        if self.is_paused:
            self.resume_recording()
        else:
            self.pause_recording()

    def pause_recording(self):
        self.is_paused = True
        self.is_gif_running = False
        self.status_label.config(text="Recording paused.")
        self.pause_resume_button.config(text="Resume Recording", bg='#06D001')
        self.pause_start_time = time.time()

    def resume_recording(self):
        self.is_paused = False
        self.is_gif_running = True
        self.status_label.config(text="Recording...")
        self.pause_resume_button.config(text="Pause Recording", bg='#37B7C3')
        pause_duration = time.time() - self.pause_start_time
        self.start_time += pause_duration

    def update_timer(self):
        if self.is_recording:
            if not self.is_paused:
                self.elapsed_time = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Timer: {self.elapsed_time} seconds")
            self.control_window.after(1000, self.update_timer)

    def record_audio(self):
        try:
            stream = self.p.open(format=self.format,
                                 channels=self.channels,
                                 rate=self.rate,
                                 input=True,
                                 frames_per_buffer=self.chunk)

            print("Recording...")
            while self.is_recording:
                if not self.is_paused:
                    data = stream.read(self.chunk)
                    self.frames.append(data)
            print("Recording finished")

            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"Error during recording: {e}")
            messagebox.showerror("Recording Error", f"An error occurred during recording: {e}")
            self.stop_recording()

    def show_save_edit_window(self):
        self.save_edit_window = Toplevel(self.root)
        self.save_edit_window.title("Save or Edit Recording")
        self.save_edit_window.geometry("400x300")
        self.save_edit_window.configure(bg='#050f28')

        filename_label = tk.Label(self.save_edit_window, text=f"File: {self.filename_base}{self.counter}.wav", bg='#050f28', fg='white', font=("Helvetica", 14))
        filename_label.pack(pady=20)

        save_button = tk.Button(self.save_edit_window, text="Save Recording", command=self.save_recording, bg='#8DECB4', font=("Helvetica", 14))
        save_button.pack(pady=20)

        edit_button = tk.Button(self.save_edit_window, text="Edit Recording", command=self.edit_recording, bg='orange', font=("Helvetica", 14))
        edit_button.pack(pady=20)

    def save_recording(self):
        if not os.path.exists("recordings"):
            os.makedirs("recordings")
        
        filename = os.path.join("recordings", f"{self.filename_base}{self.counter}.wav")
        self.save_audio(filename)
        messagebox.showinfo("Voice Recorder", f"Recording saved as {filename}")
        self.counter += 1
        self.save_edit_window.destroy()

    def edit_recording(self):
        self.edit_window = Toplevel(self.save_edit_window)
        self.edit_window.title("Edit Recording Name")
        self.edit_window.geometry("400x250")
        self.edit_window.configure(bg='#050f28')

        name_label = tk.Label(self.edit_window, text="Enter new name:", bg='#050f28', fg='white', font=("Helvetica", 14))
        name_label.pack(pady=20)

        self.new_name_entry = Entry(self.edit_window, font=("Helvetica", 14))
        self.new_name_entry.insert(0, f"{self.filename_base}{self.counter}")
        self.new_name_entry.pack(pady=20)

        save_button = tk.Button(self.edit_window, text="Save", command=self.save_edited_name, bg='#8DECB4', font=("Helvetica", 14))
        save_button.pack(pady=20)

    def save_edited_name(self):
        new_name = self.new_name_entry.get()
        if new_name:
            if not os.path.exists("recordings"):
                os.makedirs("recordings")
            
            filename = os.path.join("recordings", f"{new_name}.wav")
            self.save_audio(filename)
            messagebox.showinfo("Voice Recorder", f"Recording saved as {filename}")
            self.counter += 1
            self.edit_window.destroy()
            self.save_edit_window.destroy()
        else:
            messagebox.showerror("Error", "Please enter a valid name.")

    def save_audio(self, filename):
        if self.frames:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()

    def show_recordings(self):
        self.recordings_window = Toplevel(self.root)
        self.recordings_window.title("Recordings")
        self.recordings_window.geometry("500x500")
        self.recordings_window.configure(bg='#050f28')

        self.recordings_listbox = Listbox(self.recordings_window, bg='#e6e6e6', font=("Helvetica", 14), width=40, height=15)
        self.recordings_listbox.pack(pady=20)

        self.play_button = tk.Button(self.recordings_window, text="Play Audio", command=self.play_audio, bg='green', font=("Helvetica", 14))
        self.play_button.pack(pady=10)

        self.delete_button = tk.Button(self.recordings_window, text="Delete Recording", command=self.delete_recording, bg='orange', font=("Helvetica", 14))
        self.delete_button.pack(pady=10)

        self.load_recordings()

    def load_recordings(self):
        if os.path.exists("recordings"):
            recordings = [f for f in os.listdir("recordings") if f.endswith('.wav')]
            for recording in recordings:
                self.recordings_listbox.insert(tk.END, recording)

    def play_audio(self):
        selected_recording = self.recordings_listbox.curselection()
        if selected_recording:
            filename = self.recordings_listbox.get(selected_recording)
            full_path = os.path.join("recordings", filename)
            if os.path.exists(full_path):
                threading.Thread(target=self.play_audio_file, args=(full_path,)).start()
            else:
                messagebox.showerror("Error", f"File {filename} not found.")
        else:
            messagebox.showerror("Error", "No recording selected.")

    def play_audio_file(self, filepath):
        wf = wave.open(filepath, 'rb')
        stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                             channels=wf.getnchannels(),
                             rate=wf.getframerate(),
                             output=True)

        data = wf.readframes(self.chunk)
        while data:
            stream.write(data)
            data = wf.readframes(self.chunk)

        stream.stop_stream()
        stream.close()
        wf.close()

    def delete_recording(self):
        selected_recording = self.recordings_listbox.curselection()
        if selected_recording:
            filename = self.recordings_listbox.get(selected_recording)
            full_path = os.path.join("recordings", filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                self.recordings_listbox.delete(selected_recording)
                messagebox.showinfo("Voice Recorder", f"Recording {filename} deleted.")
            else:
                messagebox.showerror("Error", f"File {filename} not found.")
        else:
            messagebox.showerror("Error", "No recording selected.")

    def __del__(self):
        self.p.terminate()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceRecorderApp(root)
    root.mainloop()
