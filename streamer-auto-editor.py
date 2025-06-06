import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import json
import os
import subprocess
from datetime import datetime, timedelta
import threading
from moviepy.editor import VideoFileClip, concatenate_videoclips
from pathlib import Path

# build commands to produce an .exe:  
    #  cd /whereever/you/cloned/the/repo
    #  python -m venv venv
    #  venv\Scripts\activate
    #  pip install -r requirements.txt
    #  pyinstaller --onefile --console streamer-auto-editor.py


class ClipExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Population One Stream Auto Editor")
        self.root.geometry("900x900")
        self.root.configure(bg="#1e1e1e")

        self.video_path = None
        self.log_path = None
        self.intro_path = None
        self.outro_path = None

        self.events = []
        self.clip_checks = []
        self.clip_paths = []
        self.event_metadata = []
        self.player_filters = {}
        self.unique_players = set()

        os.makedirs("clips", exist_ok=True)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('.', background='#1e1e1e', foreground='white', fieldbackground='#2e2e2e')
        style.configure('TButton', background='#3a3a3a', foreground='white')
        style.configure('TLabel', background='#1e1e1e', foreground='white')
        style.configure('TScale', background='#1e1e1e')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TCheckbutton', background='#1e1e1e', foreground='white')
        style.configure('TEntry', fieldbackground='#2e2e2e', foreground='white')

        title = ttk.Label(root, text="Created by: f(x,y,z)", font=("Segoe UI", 16, "italic", "bold"))
        title.pack(pady=10)
        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=10)
        top_frame = ttk.Frame(root)
        top_frame.pack(pady=5, fill="x", padx=10)

        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)
        top_frame.grid_columnconfigure(2, weight=1)

        input_frame = ttk.LabelFrame(top_frame, text="Input Files", padding=10)
        input_frame.grid(row=0, column=0, padx=10)

        ttk.Label(input_frame, text="Video File (MP4/MKV):").pack()
        self.video_btn = ttk.Button(input_frame, text="Select Video", command=self.load_video)
        self.video_btn.pack(pady=5)

        ttk.Label(input_frame, text="Log File:").pack()
        self.log_btn = ttk.Button(input_frame, text="Select Log", command=self.load_log)
        self.log_btn.pack(pady=5)

        self.fp_options_frame = ttk.LabelFrame(input_frame, text="First Person Video Options", padding=10)
        self.fp_options_frame.pack(pady=5, fill="x", padx=10)
        self.fp_options_frame.pack_forget()  # Hide initially

        ttk.Label(self.fp_options_frame, text="First Person Video File (MP4/MKV):").pack()
        self.fp_video_btn = ttk.Button(self.fp_options_frame, text="Select First Person Video", command=self.load_fp_video)
        self.fp_video_btn.pack(pady=5)

        ttk.Label(self.fp_options_frame, text="Time of First Kill in FP Video (hh:mm:ss):").pack()
        self.fp_start_time_entry = ttk.Entry(self.fp_options_frame, width=20)
        self.fp_start_time_entry.pack(pady=5)

        addon_frame = ttk.LabelFrame(top_frame, text="Optional Addon Videos", padding=10)
        addon_frame.grid(row=0, column=1, padx=10)

        ttk.Label(addon_frame, text="Intro Video (Optional):").pack()
        self.intro_btn = ttk.Button(addon_frame, text="Select Intro Video", command=self.load_intro)
        self.intro_btn.pack(pady=5)

        ttk.Label(addon_frame, text="Outro Video (Optional):").pack()
        self.outro_btn = ttk.Button(addon_frame, text="Select Outro Video", command=self.load_outro)
        self.outro_btn.pack(pady=5)

        ttk.Label(root, text="Time of First Kill (hh:mm:ss):").pack()
        ttk.Label(root, text="This needs to be accurate to the second, find the time when 'first blood' is said").pack()
        ttk.Label(root, text="ALL the time calculations depend on this value.").pack()
        self.start_time_entry = ttk.Entry(root, width=20)
        self.start_time_entry.pack(pady=5)

        settings_frame = ttk.LabelFrame(top_frame, text="Edit Settings", padding=10)
        settings_frame.grid(row=0, column=2, padx=10)

        self.distance_threshold = tk.DoubleVar(value=50.0)
        self.time_before = tk.IntVar(value=5)
        self.time_after = tk.IntVar(value=3)

        self.distance_label = ttk.Label(settings_frame, text=f"Camera Distance Threshold: {self.distance_threshold.get():.1f}")
        self.distance_label.pack()
        distance_slider = ttk.Scale(settings_frame, from_=0, to=200, orient=tk.HORIZONTAL,
                  variable=self.distance_threshold, length=200, command=self.update_distance_label)
        distance_slider.pack()

        self.before_label = ttk.Label(settings_frame, text=f"Time Before Kill (seconds): {self.time_before.get()}")
        self.before_label.pack()
        before_slider = ttk.Scale(settings_frame, from_=0, to=10, orient=tk.HORIZONTAL,
                  variable=self.time_before, length=200, command=self.update_before_label)
        before_slider.pack()

        self.after_label = ttk.Label(settings_frame, text=f"Time After Kill (seconds): {self.time_after.get()}")
        self.after_label.pack()
        after_slider = ttk.Scale(settings_frame, from_=0, to=10, orient=tk.HORIZONTAL,
                  variable=self.time_after, length=200, command=self.update_after_label)
        after_slider.pack()

        # Move the combine_fp_var and checkbox into settings_frame
        self.combine_fp_var = tk.BooleanVar(value=False)
        self.combine_fp_chk = ttk.Checkbutton(
            settings_frame,
            text="Combine with first person video",
            variable=self.combine_fp_var,
            command=self.toggle_fp_options
        )
        self.combine_fp_chk.pack(pady=5)


        self.fp_video_path = None

        self.visible_to_caster_var = tk.BooleanVar(value=True)
        self.visible_to_caster_chk = ttk.Checkbutton(
            settings_frame,
            text="kills visible to caster",
            variable=self.visible_to_caster_var
        )
        self.visible_to_caster_chk.pack(pady=5)

        self.filter_frame = ttk.LabelFrame(top_frame, text="Filter by Player", padding=10)
        self.filter_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew")

        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=10)

        self.process_btn = ttk.Button(button_frame, text="Generate Clip Previews", command=self.run_processing_thread)
        self.process_btn.grid(row=0, column=0, padx=10)

        self.final_btn = ttk.Button(button_frame, text="Create Final Edited Video", command=self.run_final_thread, state="disabled")
        self.final_btn.grid(row=0, column=1, padx=10)

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=5)

        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=10)

        ttk.Label(root, text="Console Output:").pack()
        self.console_output = tk.Text(root, height=8, width=100, bg="#2e2e2e", fg="white", insertbackground="white")
        self.console_output.pack(pady=5)

        self.thumbnail_frame = tk.Frame(root, bg="#1e1e1e")
        self.thumbnail_frame.pack(fill='x', expand=True)

        self.canvas = tk.Canvas(self.thumbnail_frame, bg="#1e1e1e", height=150)
        self.scrollbar = ttk.Scrollbar(self.thumbnail_frame, orient="horizontal", command=self.canvas.xview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(xscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="x", expand=True)
        self.scrollbar.pack(side="bottom", fill="x")

    def update_distance_label(self, e):
        self.distance_label.config(text=f"Camera Distance Threshold: {self.distance_threshold.get():.1f}")

    def update_before_label(self, e):
        self.before_label.config(text=f"Time Before Kill (seconds): {int(self.time_before.get())}")

    def update_after_label(self, e):
        self.after_label.config(text=f"Time After Kill (seconds): {int(self.time_after.get())}")

    def log(self, message):
        self.console_output.insert(tk.END, message + "\n")
        self.console_output.see(tk.END)
        self.root.update()

    def load_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv")])
        if self.video_path:
            self.video_btn.config(text=os.path.basename(self.video_path))
            self.log(f"Stream recording selected: {self.video_path}")
    
    def load_log(self):
        self.log_path = filedialog.askopenfilename(filetypes=[("Log files", "*.log")])
        if self.log_path:
            self.log_btn.config(text=os.path.basename(self.log_path))
            self.log(f"Log file selected: {self.log_path}")

            with open(self.log_path, "r", encoding="utf-8") as f:
                self.events = [json.loads(line) for line in f if line.strip()]

            # Extract unique players
            self.unique_players.clear()
            for event in self.events:
                if "Killer" in event:
                    self.unique_players.add(event["Killer"])
                if "Killed" in event:
                    self.unique_players.add(event["Killed"])

            for widget in self.filter_frame.winfo_children():
                widget.destroy()
            self.filter_vars = {}

            num_columns = 5
            row_num = 0
            col_num = 0

            sorted_players = sorted(self.unique_players)
            for i, player in enumerate(sorted_players):
                var = tk.BooleanVar(value=True)
                chk = ttk.Checkbutton(self.filter_frame, text=player, variable=var)
                chk.grid(row=row_num, column=col_num, sticky="w", padx=5, pady=2)
                self.filter_vars[player] = var

                col_num += 1
                if col_num >= num_columns:
                    col_num = 0
                    row_num += 1

            self.filter_frame.grid_columnconfigure(list(range(num_columns)), weight=0)

    def load_intro(self):
        self.intro_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv")])
        if self.intro_path:
            self.intro_btn.config(text=os.path.basename(self.intro_path))
            self.log(f"Intro file selected: {self.intro_path}")

    def load_outro(self):
        self.outro_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv")])
        if self.outro_path:
            self.outro_btn.config(text=os.path.basename(self.outro_path))
            self.log(f"Outro file selected: {self.outro_path}")

    def toggle_fp_options(self):
        if self.combine_fp_var.get():
            self.fp_options_frame.pack(pady=5, fill="x", padx=10)
        else:
            self.fp_options_frame.pack_forget()

    def load_fp_video(self):
        self.fp_video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv")])
        if self.fp_video_path:
            self.fp_video_btn.config(text=os.path.basename(self.fp_video_path))
            self.log(f"First person video selected: {self.fp_video_path}")

    def parse_log(self):
        with open(self.log_path, "r", encoding="utf-8") as f:
            self.events = [json.loads(line) for line in f if line.strip()]

    def run_processing_thread(self):
        self.process_btn.config(state="disabled")
        self.final_btn.config(state="disabled")
        thread = threading.Thread(target=self.process)
        thread.start()

    def run_final_thread(self):
        self.process_btn.config(state="disabled")
        self.final_btn.config(state="disabled")

        selected_paths = [
            path for chk_var, path, killer, killed, frame in self.clip_checks if chk_var
        ]
        if not selected_paths:
            messagebox.showwarning("No Clips Selected", "Please select at least one clip.")
            self.process_btn.config(state="normal")
            self.final_btn.config(state="normal")
            return
        print(str(selected_paths))
        thread = threading.Thread(
            target=self.create_final_video,
            args=(selected_paths,)
        )
        thread.start()

    def create_side_by_side_clip(self, stream_path, fp_path, stream_start, duration, fp_start):
        """
        Returns a moviepy VideoClip with stream and first-person video side by side, both with audio.
        """
        stream_clip = VideoFileClip(stream_path).subclip(stream_start, stream_start + duration)
        fp_clip = VideoFileClip(fp_path).subclip(fp_start, fp_start + duration)

        # Resize to same height
        min_height = min(stream_clip.h, fp_clip.h)
        stream_clip = stream_clip.resize(height=min_height)
        fp_clip = fp_clip.resize(height=min_height)

        # Compose side by side
        from moviepy.editor import clips_array, CompositeAudioClip

        # Combine audio (both tracks)
        combined_audio = CompositeAudioClip([stream_clip.audio, fp_clip.audio])

        side_by_side = clips_array([[stream_clip, fp_clip]])
        side_by_side = side_by_side.set_audio(combined_audio)

        return side_by_side

    def generate_thumbnail(self, clip_path, thumb_path):
        cmd = [
            "ffmpeg", "-y", "-i", clip_path, "-ss", "00:00:01.000", "-vframes", "1", thumb_path
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            self.log(f"Failed to generate thumbnail for {clip_path}")
            self.log(proc.stderr.decode())
            return False
        return True

    def preview_clip(self, clip_path):
        subprocess.Popen(["ffplay", "-autoexit", clip_path])

    def process(self):
        self.console_output.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.clip_checks.clear()
        self.clip_paths.clear()

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.video_path or not self.log_path:
            messagebox.showerror("Error", "Please select both a video and a log file.")
            self.process_btn.config(state="normal")
            return

        self.log("Parsing log file...")
        self.parse_log()

        start_time_str = self.start_time_entry.get()
        try:
            start_time = datetime.strptime(start_time_str, "%H:%M:%S")
        except ValueError:
            messagebox.showerror("Error", "Invalid time format. Use hh:mm:ss.")
            self.process_btn.config(state="normal")
            return

        if not self.events:
            messagebox.showerror("Error", "No events found in log file.")
            self.process_btn.config(state="normal")
            return

        first_kill_event = next((e for e in self.events), None)
        if not first_kill_event:
            messagebox.showerror("Error", "No valid kill events found in log file.")
            self.process_btn.config(state="normal")
            return

        first_kill_time_log = datetime.fromisoformat(first_kill_event["TimeStamp"].replace("Z", "+00:00"))

        self.log("Filtering events...")
        filtered_events = []
        selected_players = [player for player, var in self.filter_vars.items() if var.get()]
        for event in self.events:
            visible_ok = True
            if self.visible_to_caster_var.get():
                visible_ok = event.get("KillerInView") and event.get("InView")
            if (
                visible_ok and
                event.get("CameraDistance", 9999) <= self.distance_threshold.get()
            ):
                killer = event.get("Killer", "Unknown")
                killed = event.get("Killed", "Unknown")
                event_time_log = datetime.fromisoformat(event["TimeStamp"].replace("Z", "+00:00"))
                delta = event_time_log - first_kill_time_log
                actual_time = start_time + delta

                start_clip = actual_time - timedelta(seconds=self.time_before.get())
                if start_clip < datetime.strptime("00:00:00", "%H:%M:%S"):
                    start_clip = datetime.strptime("00:00:00", "%H:%M:%S")
                end_clip = actual_time + timedelta(seconds=self.time_after.get())

                if killer in selected_players:
                    filtered_events.append({
                        "start": start_clip,
                        "end": end_clip,
                        "killer": killer,
                        "killed": killed
                    })


        if not filtered_events:
            self.log("No events matched the filtering criteria.")
            self.process_btn.config(state="normal")
            return

        # Sort and merge clips
        filtered_events.sort(key=lambda c: c["start"])
        merged_clips = []
        current = filtered_events[0].copy()
        current["killers"] = [current.pop("killer")]
        current["killed_list"] = [current.pop("killed")]

        for clip in filtered_events[1:]:
            if clip["start"] <= current["end"]:
                current["end"] = max(current["end"], clip["end"])
                current["killers"].append(clip["killer"])
                current["killed_list"].append(clip["killed"])
            else:
                merged_clips.append(current)
                current = clip.copy()
                current["killers"] = [current.pop("killer")]
                current["killed_list"] = [current.pop("killed")]
        merged_clips.append(current)

        self.log(f"Total {len(merged_clips)} clips to generate...")
        
        self.clip_times = [(clip["start"], clip["end"]) for clip in merged_clips]
        
        for i, clip in enumerate(merged_clips):
            start = clip["start"]
            end = clip["end"]
            killers = ", ".join(clip["killers"])
            killed = ", ".join(clip["killed_list"])

            clip_filename = f"clips/clip_{i+1}.mp4"
            start_str = start.strftime("%H:%M:%S")
            duration = (end - start).total_seconds()
            if duration <= 0:
                self.log(f"Skipping clip {i+1} with non-positive duration.")
                continue

            # --- New logic for side-by-side preview ---
            combine_fp = self.combine_fp_var.get() and self.fp_video_path and self.fp_start_time_entry.get()
            if combine_fp:
                try:
                    fp_first_kill_dt = datetime.strptime(self.fp_start_time_entry.get(), "%H:%M:%S")
                    stream_start_dt = datetime.strptime(self.start_time_entry.get(), "%H:%M:%S")
                    # Calculate offset from stream first kill
                    stream_delta = (start - stream_start_dt).total_seconds()
                    fp_clip_start = (fp_first_kill_dt + timedelta(seconds=stream_delta)).strftime("%H:%M:%S")
                    # Convert to seconds for subclip
                    h, m, s = map(int, start_str.split(":"))
                    stream_sec = h * 3600 + m * 60 + s
                    h, m, s = map(int, fp_clip_start.split(":"))
                    fp_sec = h * 3600 + m * 60 + s

                    # Create side-by-side preview and write to file
                    side_by_side_clip = self.create_side_by_side_clip(
                        self.video_path, self.fp_video_path, stream_sec, duration, fp_sec
                    )
                    side_by_side_clip.write_videofile(clip_filename, codec="libx264", audio_codec="aac", threads=2, preset="ultrafast", verbose=False, logger=None)
                    side_by_side_clip.close()
                except Exception as e:
                    self.log(f"Failed to create side-by-side preview for clip {i+1}: {e}")
                    continue
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-ss", start_str, "-i", self.video_path,
                    "-t", str(duration), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", clip_filename
                ]
                self.log(f"Extracting clip {i+1}: {start_str} +{duration:.2f}s {killers} → {killed} ")
                proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if proc.returncode != 0:
                    self.log(f"Failed to extract clip {i+1}")
                    self.log(proc.stderr.decode())
                    continue

            self.clip_paths.append(clip_filename)

            thumb_path = f"clips/thumb_{i+1}.png"
            if self.generate_thumbnail(clip_filename, thumb_path):
                img = Image.open(thumb_path)
                img.thumbnail((160, 90))
                img_tk = ImageTk.PhotoImage(img)
                chk_var = tk.BooleanVar(value=True)

                clip_frame = ttk.Frame(self.scrollable_frame)
                clip_frame.pack(side="left", padx=5)

                ttk.Label(clip_frame, text=f"{killers} → {killed}").pack()
                thumb_label = ttk.Label(clip_frame, image=img_tk)
                thumb_label.image = img_tk
                thumb_label.pack()
                thumb_label.bind("<Button-1>", lambda e, path=clip_filename: self.preview_clip(path))
                cb = ttk.Checkbutton(clip_frame, variable=chk_var)
                cb.pack()

                self.clip_checks.append((chk_var, clip_filename, clip["killers"], clip["killed_list"], clip_frame))
            else:
                self.log(f"Failed to generate thumbnail for clip {i+1}")

            self.progress['value'] = (i + 1) / len(merged_clips) * 100
            self.root.update_idletasks()


        if self.clip_paths:
            self.final_btn.config(state="normal")
        else:
            self.final_btn.config(state="disabled")

        self.process_btn.config(state="normal")
        self.log("Clip preview generation complete.")


    def create_final_video(self, selected_clip_paths, output_path="final_output.mp4"):
        final_clips = []

        # Optional intro
        if self.intro_path and Path(self.intro_path).exists():
            final_clips.append(VideoFileClip(self.intro_path))

        combine_fp = self.combine_fp_var.get() and self.fp_video_path and self.fp_start_time_entry.get()
        fp_video_path = self.fp_video_path
        fp_first_kill_time = self.fp_start_time_entry.get()

        if combine_fp:
            # Parse first kill time in FP video
            try:
                fp_first_kill_dt = datetime.strptime(fp_first_kill_time, "%H:%M:%S")
            except Exception:
                self.log("Invalid first kill time for FP video. Use hh:mm:ss.")
                self.final_btn.config(state="normal")
                self.process_btn.config(state="normal")
                return

            # Find first kill event time in stream
            if not self.events:
                self.log("No events loaded for synchronization.")
                return
            first_kill_event = next((e for e in self.events), None)
            if not first_kill_event:
                self.log("No valid kill events found in log file.")
                return
            stream_first_kill_dt = datetime.fromisoformat(first_kill_event["TimeStamp"].replace("Z", "+00:00"))
            stream_start_time = self.start_time_entry.get()
            try:
                stream_start_dt = datetime.strptime(stream_start_time, "%H:%M:%S")
            except Exception:
                self.log("Invalid stream start time. Use hh:mm:ss.")
                return

            # Calculate offset between stream and FP video
            # For each clip, calculate the start time in both videos
            for chk_var, path, killers, killed_list, frame in self.clip_checks:
                if not chk_var.get():
                    continue
                # Extract start time from filename or metadata
                # We'll need to store start/end times in self.clip_checks or elsewhere
                # For now, let's assume you have a parallel list self.clip_times = [(start, end), ...]
                # If not, you should store start/end with each clip in self.clip_checks

                # Let's assume you have self.clip_times = [(start, end), ...] in the same order as self.clip_checks
                # If not, you need to adjust this logic to get the correct start/end for each clip

                # For demonstration, let's use the clip filename index to get times
                idx = int(os.path.splitext(os.path.basename(path))[0].split("_")[-1]) - 1
                start, end = self.clip_times[idx]
                duration = (end - start).total_seconds()
                stream_clip_start = start.strftime("%H:%M:%S")

                # Calculate offset from stream first kill
                stream_delta = (start - stream_start_dt).total_seconds()
                fp_clip_start = (fp_first_kill_dt + timedelta(seconds=stream_delta)).strftime("%H:%M:%S")

                # Convert to seconds for subclip
                h, m, s = map(int, stream_clip_start.split(":"))
                stream_sec = h * 3600 + m * 60 + s
                h, m, s = map(int, fp_clip_start.split(":"))
                fp_sec = h * 3600 + m * 60 + s

                try:
                    side_by_side_clip = self.create_side_by_side_clip(
                        self.video_path, fp_video_path, stream_sec, duration, fp_sec
                    )
                    final_clips.append(side_by_side_clip)
                except Exception as e:
                    self.log(f"Failed to create side-by-side clip: {e}")

        else:
            # Main selected clips (original behavior)
            for path in selected_clip_paths:
                if Path(path).exists():
                    final_clips.append(VideoFileClip(path))

        # Optional outro
        if self.outro_path and Path(self.outro_path).exists():
            final_clips.append(VideoFileClip(self.outro_path))

        # Concatenate all
        if not final_clips:
            self.log("No valid clips to concatenate.")
            return

        self.log(f"Generating final video: stitching {len(final_clips)} clips together.")

        final_video = concatenate_videoclips(final_clips, method="compose")

        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="ultrafast",
        )

        # Cleanup
        final_video.close()
        for clip in final_clips:
            clip.close()

        self.final_btn.config(state="normal")
        self.process_btn.config(state="normal")
        self.log(f"Edited video generation complete: {output_path}")
    def apply_filters(self):
        active_players = {p for p, v in self.filter_vars.items() if v.get()}

        for chk_var, path, killer, killed, frame in self.clip_checks:
            visible = killer in active_players or killed in active_players
            if visible:
                frame.pack(side="left", padx=5)
            else:
                frame.pack_forget()

def main():
    root = tk.Tk()
    ClipExtractorApp(root)
    root.mainloop()

main()