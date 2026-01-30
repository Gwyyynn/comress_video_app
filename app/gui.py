"""GUI application for video compression.

Provides a Tkinter interface for:
- Compressing videos with multiple presets (light, medium, strong)
- Supporting local files and video URLs (via download)
- Real-time compression progress logging
- Multi-threaded background processing
"""

import os
import threading
from queue import Queue
from tkinter import Tk, Entry, Button, Text, Scrollbar, StringVar, Label
from tkinter.filedialog import askopenfilename
from typing import Optional

from app.compressor import compress_video
from app.utils import output_filename
from app.downloader import download_video


class CompressorApp:
    """GUI application for video compression with threaded background processing."""
    
    def __init__(self) -> None:
        """Initialize the compression app."""
        self.task_queue: Queue = Queue()
        self.current_preset: str = "medium"
        
        # UI components
        self.root: Optional[Tk] = None
        self.status_var: Optional[StringVar] = None
        self.linkInput: Optional[Entry] = None
        self.targetEntry: Optional[Entry] = None
        self.log: Optional[Text] = None

    def worker(self) -> None:
        """Process video compression tasks from queue.
        
        Runs in background thread(s), continuously polling the task queue
        and executing compression jobs with logging and error handling.
        """
        while True:
            input_file, output_file, preset, target_mb = self.task_queue.get()
            try:
                self.set_status(f"Compressing ({preset})...")
                self.log_msg(f"🔧 Compressing {input_file} to {output_file} with preset '{preset}' and target {target_mb} MB")
                size_mb = compress_video(
                    input_file,
                    output_file,
                    preset,
                    target_mb
                )
                self.log_msg(f"✔ Готово: {output_file} ({size_mb:.2f} MB)")

            except Exception as e:
                self.set_status(f"Error: {str(e)}")
                self.log_msg(f"❌ Error compressing {input_file}: {str(e)}")
            finally:
                self.task_queue.task_done()
                if self.task_queue.empty():
                    self.set_status("Idle")

    def start_workers(self, count: int = 2) -> None:
        """Start background worker threads.
        
        Args:
            count: Number of worker threads (default: 2)
        """
        for _ in range(count):
            threading.Thread(target=self.worker, daemon=True).start()

    def process_video(self, url: str) -> None:
        """Download and queue video for compression.
        
        Args:
            url: Video URL to download from
        """
        input_file = download_video(url)

        base, ext = os.path.splitext(input_file)
        output_file = base + str(self.current_preset) + "_compressed.mp4"
        output_file = output_filename(output_file)

        target_mb = self.get_target_mb()
        self.log_msg(f"🎯 Target size: {target_mb or 'CRF mode'} MB")
        self.task_queue.put((input_file, output_file, self.current_preset, target_mb))

    def choose_file(self) -> None:
        """Open file picker and queue selected video for compression."""
        file_path = askopenfilename(
            title="Выбери файл",
            filetypes=[
                ("Видео файлы", "*.mp4;*.mkv;*.avi"),
                ("Все файлы", "*.*")
            ]
        )

        if not file_path:
            self.set_status("Error: No file selected")
            self.log_msg("❌ No file selected")
            return
        output_file = os.path.splitext(file_path)[0] + str(self.current_preset) + "_compressed.mp4"
        output_file = output_filename(output_file)

        target_mb = self.get_target_mb()
        self.log_msg(f"🎯 Target size: {target_mb or 'CRF mode'} MB")

        self.task_queue.put((file_path, output_file, self.current_preset, target_mb))

    def on_button_click(self) -> None:
        """Handle download button click."""
        url = self.linkInput.get().strip()

        if not url:
            self.set_status("Error: Enter a valid URL")
            return

        threading.Thread(
            target=self.process_video,
            args=(url,),
            daemon=True
        ).start()

    def set_preset(self, preset: str) -> None:
        """Set compression preset.
        
        Args:
            preset: Preset name ('light', 'medium', or 'strong')
        """
        self.current_preset = preset
        self.set_status(f"Preset: {preset}")

    def get_target_mb(self) -> Optional[int]:
        """Get target file size from input field.
        
        Returns:
            Target size in MB or None if in CRF mode
        """
        raw = self.targetEntry.get().strip()

        if raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            self.set_status("Error: Target MB must be a number")
            return None

    def set_status(self, text: str) -> None:
        """Update status label text (thread-safe).
        
        Args:
            text: Status message to display
        """
        if self.root and self.status_var:
            self.root.after(0, self.status_var.set, text)

    def log_msg(self, text: str) -> None:
        """Append message to log display (thread-safe).
        
        Args:
            text: Message to log
        """
        if not (self.root and self.log):
            return

        def write() -> None:
            self.log.config(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.config(state="disabled")

        self.root.after(0, write)

    def build_ui(self) -> None:
        """Build the Tkinter GUI."""
        self.root = Tk()
        self.root.title("Video Compressor")
        self.root.geometry("700x400")

        self.log = Text(self.root, height=8, state="disabled", wrap="word")
        self.log.pack(fill="both", padx=10, pady=5)

        scroll = Scrollbar(self.log, command=self.log.yview)
        scroll.pack(side="right", fill="y")
        self.log.config(yscrollcommand=scroll.set)

        self.status_var = StringVar(value="Ready to compress videos!")

        self.linkInput = Entry(self.root, width=40)
        self.linkInput.pack(pady=20)

        self.targetEntry = Entry(self.root, width=40)
        self.targetEntry.insert(0, "10")
        self.targetEntry.pack(pady=5)

        Button(
            self.root,
            text="Compress Video from Link",
            command=self.on_button_click
        ).pack()

        Button(
            self.root,
            text="Choose File",
            command=self.choose_file
        ).pack()

        Button(
            self.root,
            text="light",
            command=lambda: self.set_preset("light")
        ).pack()

        Button(
            self.root,
            text="medium",
            command=lambda: self.set_preset("medium")
        ).pack()

        Button(
            self.root,
            text="strong",
            command=lambda: self.set_preset("strong")
        ).pack()

        status_label = Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            relief="sunken"
        )
        status_label.pack(fill="x", side="bottom")

    def start(self) -> None:
        """Start the GUI application with worker threads."""
        self.build_ui()
        self.start_workers(2)
        self.root.mainloop()


