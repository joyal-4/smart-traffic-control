import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import threading
import time
from PIL import Image, ImageTk
import os
from vehicle_detector import VehicleDetector
from traffic_lane_manager import TrafficLaneManager
from traffic_signal_controller import TrafficSignalController

class TrafficGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Traffic Light Control System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Initialize components
        self.vehicle_detector = VehicleDetector()
        self.lane_manager = None
        self.signal_controller = None
        
        # Video variables
        self.video_path = None
        self.cap = None
        self.current_frame = None
        self.frame_width = 640
        self.frame_height = 480
        
        # Control variables
        self.is_running = False
        self.is_paused = False
        self.analysis_thread = None
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Create GUI
        self.create_widgets()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # Middle content area
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left side - Video display
        self.create_video_panel(content_frame)
        
        # Right side - Traffic signal panel
        self.create_signal_panel(content_frame)
        
        # Bottom status panel
        self.create_status_panel(main_frame)
    
    def create_control_panel(self, parent):
        """Create control panel with file upload and control buttons"""
        control_frame = ttk.LabelFrame(parent, text="Control Panel", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # File upload section
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(file_frame, text="Traffic Video:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.file_label = ttk.Label(file_frame, text="No file selected", 
                                   foreground="gray", width=40)
        self.file_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.browse_button = ttk.Button(file_frame, text="Browse", 
                                      command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT)
        
        self.start_button = ttk.Button(button_frame, text="Start", 
                                      command=self.start_analysis,
                                      state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                     command=self.stop_analysis,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reset_button = ttk.Button(button_frame, text="Reset", 
                                      command=self.reset_analysis)
        self.reset_button.pack(side=tk.LEFT)
    
    def create_video_panel(self, parent):
        """Create video display panel"""
        video_frame = ttk.LabelFrame(parent, text="Traffic Video Analysis", padding=10)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Video canvas
        self.video_canvas = tk.Canvas(video_frame, width=self.frame_width, 
                                    height=self.frame_height, bg='black')
        self.video_canvas.pack()
        
        # Video info labels
        info_frame = ttk.Frame(video_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.fps_label = ttk.Label(info_frame, text="FPS: 0.0")
        self.fps_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.total_vehicles_label = ttk.Label(info_frame, text="Total Vehicles: 0")
        self.total_vehicles_label.pack(side=tk.LEFT)
    
    def create_signal_panel(self, parent):
        """Create traffic signal simulation panel"""
        signal_frame = ttk.LabelFrame(parent, text="Traffic Signal Control", padding=10)
        signal_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Traffic lights canvas
        self.signal_canvas = tk.Canvas(signal_frame, width=400, height=300, bg='#2c2c2c')
        self.signal_canvas.pack(pady=(0, 10))
        
        # Lane vehicle counts
        counts_frame = ttk.LabelFrame(signal_frame, text="Lane Vehicle Counts", padding=10)
        counts_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.lane_labels = {}
        lanes = ['North', 'East', 'South', 'West']
        colors = ['#ff4444', '#44ff44', '#4444ff', '#ffff44']
        
        for i, (lane, color) in enumerate(zip(lanes, colors)):
            frame = ttk.Frame(counts_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{lane}:", width=8).pack(side=tk.LEFT)
            
            count_label = ttk.Label(frame, text="0 vehicles", foreground=color, 
                                   font=('Arial', 10, 'bold'))
            count_label.pack(side=tk.LEFT, padx=(10, 0))
            
            self.lane_labels[lane] = count_label
        
        # Countdown timer
        timer_frame = ttk.LabelFrame(signal_frame, text="Signal Timer", padding=10)
        timer_frame.pack(fill=tk.X)
        
        self.timer_label = ttk.Label(timer_frame, text="00:00", 
                                   font=('Arial', 24, 'bold'), 
                                   foreground='#00ff00')
        self.timer_label.pack()
        
        self.active_lane_label = ttk.Label(timer_frame, text="Active: None", 
                                          font=('Arial', 12))
        self.active_lane_label.pack(pady=(5, 0))
    
    def create_status_panel(self, parent):
        """Create status panel"""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding=5)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready", 
                                     foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        self.most_congested_label = ttk.Label(status_frame, text="Most Congested: None")
        self.most_congested_label.pack(side=tk.RIGHT)
    
    def browse_file(self):
        """Browse and select video file"""
        file_path = filedialog.askopenfilename(
            title="Select Traffic Video",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.video_path = file_path
            self.file_label.config(text=os.path.basename(file_path), foreground="black")
            self.start_button.config(state=tk.NORMAL)
            self.status_label.config(text="Video loaded", foreground="blue")
    
    def start_analysis(self):
        """Start traffic analysis"""
        if not self.video_path:
            messagebox.showerror("Error", "Please select a video file first")
            return
        
        try:
            # Initialize video capture
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video dimensions
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Resize video canvas
            self.video_canvas.config(width=self.frame_width, height=self.frame_height)
            
            # Initialize lane manager and signal controller
            self.lane_manager = TrafficLaneManager(self.frame_width, self.frame_height)
            self.signal_controller = TrafficSignalController()
            self.signal_controller.start()
            
            # Reset metrics
            self.frame_count = 0
            self.start_time = time.time()
            
            # Start analysis
            self.is_running = True
            self.is_paused = False
            self.analysis_thread = threading.Thread(target=self.analysis_loop, daemon=True)
            self.analysis_thread.start()
            
            # Update UI
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.browse_button.config(state=tk.DISABLED)
            self.status_label.config(text="Analyzing...", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start analysis: {str(e)}")
    
    def stop_analysis(self):
        """Stop traffic analysis"""
        self.is_running = False
        self.is_paused = False
        
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2)
        
        if self.signal_controller:
            self.signal_controller.stop()
        
        if self.cap:
            self.cap.release()
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL)
        self.status_label.config(text="Stopped", foreground="red")
    
    def reset_analysis(self):
        """Reset the analysis"""
        self.stop_analysis()
        
        # Clear displays
        self.video_canvas.delete("all")
        self.signal_canvas.delete("all")
        
        # Reset labels
        self.file_label.config(text="No file selected", foreground="gray")
        self.fps_label.config(text="FPS: 0.0")
        self.total_vehicles_label.config(text="Total Vehicles: 0")
        self.timer_label.config(text="00:00")
        self.active_lane_label.config(text="Active: None")
        self.status_label.config(text="Ready", foreground="green")
        
        for label in self.lane_labels.values():
            label.config(text="0 vehicles")
        
        self.most_congested_label.config(text="Most Congested: None")
        
        # Clear video path
        self.video_path = None
    
    def analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            if not self.is_paused and self.cap:
                ret, frame = self.cap.read()
                if not ret:
                    self.is_running = False
                    self.root.after(0, lambda: self.status_label.config(
                        text="Analysis complete", foreground="blue"))
                    break
                
                # Process frame
                self.process_frame(frame)
                
                # Update FPS
                self.frame_count += 1
                elapsed = time.time() - self.start_time
                if elapsed > 0:
                    self.fps = self.frame_count / elapsed
            
            time.sleep(0.03)  # ~30 FPS
    
    def process_frame(self, frame):
        """Process a single frame"""
        # Detect vehicles
        detections = self.vehicle_detector.detect_vehicles(frame)
        
        # Update lane manager
        self.lane_manager.update_vehicle_counts(detections)
        
        # Update signal controller
        vehicle_counts = self.lane_manager.get_all_counts()
        self.signal_controller.update_vehicle_counts(vehicle_counts)
        
        # Draw everything on frame
        frame = self.vehicle_detector.draw_detections(frame, detections)
        frame = self.lane_manager.draw_lanes(frame)
        frame = self.signal_controller.draw_signals(frame, self.lane_manager)
        
        # Update displays in main thread
        self.root.after(0, lambda: self.update_displays(frame, detections))
    
    def update_displays(self, frame, detections):
        """Update all GUI displays"""
        try:
            # Convert frame for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            # Update video canvas
            self.video_canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.video_canvas.image = imgtk
            
            # Update traffic signals
            self.draw_traffic_signals()
            
            # Update labels
            self.fps_label.config(text=f"FPS: {self.fps:.1f}")
            self.total_vehicles_label.config(text=f"Total Vehicles: {len(detections)}")
            
            # Update lane counts
            counts = self.lane_manager.get_all_counts()
            lane_names = ['North', 'East', 'South', 'West']
            for i, lane_name in enumerate(lane_names):
                self.lane_labels[lane_name].config(
                    text=f"{counts[i]} vehicles"
                )
            
            # Update timer
            minutes = self.signal_controller.countdown // 60
            seconds = self.signal_controller.countdown % 60
            self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            
            # Update active lane
            active_lane_name = self.lane_manager.lanes[
                self.signal_controller.current_lane]['name']
            self.active_lane_label.config(text=f"Active: {active_lane_name}")
            
            # Update most congested lane
            congested_lanes = self.lane_manager.get_congested_lanes()
            if congested_lanes and congested_lanes[0][1] > 0:
                most_congested_id = congested_lanes[0][0]
                most_congested_name = self.lane_manager.lanes[most_congested_id]['name']
                self.most_congested_label.config(text=f"Most Congested: {most_congested_name}")
            
        except Exception as e:
            print(f"Display update error: {e}")
    
    def draw_traffic_signals(self):
        """Draw traffic signal visualization"""
        self.signal_canvas.delete("all")
        
        # Draw four traffic lights
        positions = [
            (100, 75, "North"),   # Top
            (300, 150, "East"),   # Right
            (200, 225, "South"),  # Bottom
            (50, 150, "West")     # Left
        ]
        
        signal_colors = self.signal_controller.get_signal_colors()
        
        for i, (x, y, name) in enumerate(positions):
            # Draw signal box
            self.signal_canvas.create_rectangle(x-30, y-40, x+30, y+40, 
                                               fill='#1a1a1a', outline='white')
            
            # Draw three lights
            colors = ['#ff0000', '#ffff00', '#00ff00']  # Red, Yellow, Green
            for j, color in enumerate(colors):
                light_y = y - 20 + j * 20
                
                # Determine if this light should be lit
                if signal_colors[i] == (0, 0, 255) and j == 0:  # Red
                    fill_color = colors[j]
                elif signal_colors[i] == (0, 255, 255) and j == 1:  # Yellow
                    fill_color = colors[j]
                elif signal_colors[i] == (0, 255, 0) and j == 2:  # Green
                    fill_color = colors[j]
                else:
                    fill_color = '#333333'
                
                self.signal_canvas.create_oval(x-10, light_y-8, x+10, light_y+8,
                                              fill=fill_color, outline='white')
            
            # Draw lane name
            self.signal_canvas.create_text(x, y+55, text=name, 
                                          fill='white', font=('Arial', 10, 'bold'))
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_analysis()
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # Configure ttk styles for dark theme
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure dark theme colors
    style.configure('Dark.TFrame', background='#2c2c2c')
    style.configure('Dark.TLabel', background='#2c2c2c', foreground='white')
    style.configure('Dark.TLabelFrame', background='#2c2c2c', foreground='white')
    style.configure('Dark.TLabelFrame.Label', background='#2c2c2c', foreground='white')
    
    app = TrafficGUIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
