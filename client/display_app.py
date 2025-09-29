# client/display_app.py
"""
Pi Zero Calendar Display Client - FIXED VERSION
Lightweight touchscreen calendar interface that connects to Pi 4 server
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import time
from pathlib import Path

from .utils.api_client import APIClient


class CalendarDisplayApp:
    """Main Pi Zero calendar display application"""

    def __init__(self, server_host: str = "192.168.1.100", server_port: int = 5000):
        """Initialize the display application

        Args:
            server_host: IP address of Pi 4 server
            server_port: Port of Pi 4 server
        """
        self.server_host = server_host
        self.server_port = server_port

        # Initialize API client
        self.api_client = APIClient(server_host, server_port)

        # Application state
        self.current_view = 'week'  # day, week, month
        self.current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.events = []
        self.accounts = {}
        self.config = {}

        # UI components
        self.root = None
        self.content_frame = None
        self.status_label = None
        self.date_label = None

        # Background update thread
        self.update_thread = None
        self.should_stop = False

        # Error tracking
        self.connection_errors = 0
        self.last_successful_sync = None

        # UI state
        self.is_fullscreen = True

    def start(self):
        """Start the display application"""
        print("Starting Pi Zero Calendar Display...")

        # Create main window
        self.root = tk.Tk()
        self.root.title("Pi Calendar")

        # Configure for touchscreen (fullscreen on Pi Zero)
        if self.is_fullscreen:
            self.root.attributes('-fullscreen', True)
        else:
            self.root.geometry("800x480")  # Common Pi display size

        self.root.configure(bg='black')

        # Bind escape key to exit fullscreen (for development)
        self.root.bind('<Escape>', lambda e: self._toggle_fullscreen())

        # Get screen dimensions
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        print(f"Display resolution: {screen_width}x{screen_height}")

        # Setup UI
        self._setup_ui()

        # Load initial configuration
        self._load_config()

        # Start background update thread
        self._start_background_updates()

        # Load initial data
        self._refresh_data()

        print("✓ Pi Zero display started")
        print(f"Connected to server: {self.server_host}:{self.server_port}")

        # Start main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the application"""
        print("Stopping Pi Zero Calendar Display...")

        self.should_stop = True

        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2)

        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass

        print("✓ Display stopped")

    def _toggle_fullscreen(self):
        """Toggle fullscreen mode (for development)"""
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)

    def _setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header with date and navigation
        header_frame = tk.Frame(main_frame, bg='black', height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Date display
        self.date_label = tk.Label(
            header_frame,
            text="Loading...",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='black'
        )
        self.date_label.pack(side=tk.LEFT)

        # View controls
        controls_frame = tk.Frame(header_frame, bg='black')
        controls_frame.pack(side=tk.RIGHT)

        # Navigation buttons
        nav_frame = tk.Frame(controls_frame, bg='black')
        nav_frame.pack(side=tk.TOP, pady=(0, 5))

        self.prev_button = tk.Button(
            nav_frame,
            text="◀",
            font=('Arial', 16, 'bold'),
            command=self._prev_period,
            bg='#333333',
            fg='white',
            relief=tk.FLAT,
            width=3
        )
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))

        self.next_button = tk.Button(
            nav_frame,
            text="▶",
            font=('Arial', 16, 'bold'),
            command=self._next_period,
            bg='#333333',
            fg='white',
            relief=tk.FLAT,
            width=3
        )
        self.next_button.pack(side=tk.LEFT)

        # View mode buttons
        view_frame = tk.Frame(controls_frame, bg='black')
        view_frame.pack(side=tk.BOTTOM)

        self.day_button = tk.Button(
            view_frame,
            text="Day",
            font=('Arial', 12),
            command=lambda: self._change_view('day'),
            bg='#333333',
            fg='white',
            relief=tk.FLAT,
            width=6
        )
        self.day_button.pack(side=tk.LEFT, padx=(0, 2))

        self.week_button = tk.Button(
            view_frame,
            text="Week",
            font=('Arial', 12),
            command=lambda: self._change_view('week'),
            bg='#4285f4',
            fg='white',
            relief=tk.FLAT,
            width=6
        )
        self.week_button.pack(side=tk.LEFT, padx=(0, 2))

        self.month_button = tk.Button(
            view_frame,
            text="Month",
            font=('Arial', 12),
            command=lambda: self._change_view('month'),
            bg='#333333',
            fg='white',
            relief=tk.FLAT,
            width=6
        )
        self.month_button.pack(side=tk.LEFT)

        # Status indicator
        self.status_label = tk.Label(
            header_frame,
            text="●",
            font=('Arial', 16),
            fg='yellow',  # Yellow = connecting
            bg='black'
        )
        self.status_label.place(relx=0.95, rely=0.1)

        # Calendar display area
        calendar_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=1)
        calendar_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable content area
        canvas = tk.Canvas(calendar_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(calendar_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg='white')

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.create_window((0, 0), window=self.content_frame, anchor='nw')

        # Update scroll region when content changes
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))

        self.content_frame.bind('<Configure>', configure_scroll_region)

        # Footer with sync status
        footer_frame = tk.Frame(main_frame, bg='black', height=30)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        footer_frame.pack_propagate(False)

        self.sync_label = tk.Label(
            footer_frame,
            text="Connecting to server...",
            font=('Arial', 10),
            fg='#cccccc',
            bg='black'
        )
        self.sync_label.pack(side=tk.LEFT)

        # Refresh button
        self.refresh_button = tk.Button(
            footer_frame,
            text="Refresh",
            font=('Arial', 10),
            command=self._refresh_data,
            bg='#333333',
            fg='white',
            relief=tk.FLAT
        )
        self.refresh_button.pack(side=tk.RIGHT)

        # Today button
        self.today_button = tk.Button(
            footer_frame,
            text="Today",
            font=('Arial', 10),
            command=self.goto_today,
            bg='#4285f4',
            fg='white',
            relief=tk.FLAT
        )
        self.today_button.pack(side=tk.RIGHT, padx=(0, 5))

    def _load_config(self):
        """Load configuration from server"""
        try:
            response = self.api_client.get_config()
            if response:
                self.config = response.get('config', {})
                self.accounts = response.get('accounts', {})
                print("✓ Configuration loaded from server")
            else:
                print("⚠ Could not load configuration from server")
                # Use defaults
                self.config = {
                    'timezone': 'UTC',
                    'date_format': '%Y-%m-%d',
                    'time_format': '%H:%M',
                    'default_view': 'week'
                }
        except Exception as e:
            print(f"Error loading config: {e}")
            # Use defaults
            self.config = {
                'timezone': 'UTC',
                'date_format': '%Y-%m-%d',
                'time_format': '%H:%M',
                'default_view': 'week'
            }

    def _start_background_updates(self):
        """Start background thread for periodic updates"""

        def update_worker():
            while not self.should_stop:
                try:
                    # Update every 5 minutes
                    for _ in range(300):  # 300 seconds = 5 minutes
                        if self.should_stop:
                            break
                        time.sleep(1)

                    if not self.should_stop:
                        self._refresh_data()

                except Exception as e:
                    print(f"Background update error: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

        self.update_thread = threading.Thread(target=update_worker, daemon=True)
        self.update_thread.start()

    def _refresh_data(self):
        """Refresh calendar data from server"""
        try:
            print("Refreshing calendar data...")

            # Calculate date range based on current view
            start_date, end_date = self._get_date_range()

            # Get events from server
            events_response = self.api_client.get_events(
                start_date=start_date,
                end_date=end_date,
                view=self.current_view
            )

            if events_response:
                self.events = events_response.get('events', [])

                # Update UI in main thread
                if self.root:
                    self.root.after(0, self._update_display)

                # Update status
                self._update_connection_status(True)
                self.last_successful_sync = datetime.now()
                self.connection_errors = 0

                print(f"✓ Loaded {len(self.events)} events")
            else:
                raise Exception("No response from server")

        except Exception as e:
            print(f"Error refreshing data: {e}")
            self._update_connection_status(False)
            self.connection_errors += 1

            # Show error message if too many failures
            if self.connection_errors >= 3:
                if self.root:
                    self.root.after(0, self._show_connection_error)

    def _update_display(self):
        """Update the calendar display with current data"""
        try:
            # Update date label
            if self.current_view == 'day':
                date_text = self.current_date.strftime('%A, %B %d, %Y')
            elif self.current_view == 'week':
                end_date = self.current_date + timedelta(days=6)
                date_text = f"Week of {self.current_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
            else:  # month
                date_text = self.current_date.strftime('%B %Y')

            if self.date_label:
                self.date_label.config(text=date_text)

            # Update view buttons
            self._update_view_buttons()

            # Update calendar content
            self._update_calendar_content()

            # Update sync status
            if self.last_successful_sync:
                sync_text = f"Last sync: {self.last_successful_sync.strftime('%H:%M')}"
            else:
                sync_text = "Connecting..."

            if self.sync_label:
                self.sync_label.config(text=sync_text)

        except Exception as e:
            print(f"Error updating display: {e}")

    def _update_view_buttons(self):
        """Update view button appearances"""
        try:
            # Reset all buttons
            for btn in [self.day_button, self.week_button, self.month_button]:
                if btn:
                    btn.config(bg='#333333')

            # Highlight current view
            if self.current_view == 'day' and self.day_button:
                self.day_button.config(bg='#4285f4')
            elif self.current_view == 'week' and self.week_button:
                self.week_button.config(bg='#4285f4')
            elif self.current_view == 'month' and self.month_button:
                self.month_button.config(bg='#4285f4')
        except Exception as e:
            print(f"Error updating view buttons: {e}")

    def _update_calendar_content(self):
        """Update the calendar content area"""
        try:
            # Clear previous content
            if self.content_frame:
                for widget in self.content_frame.winfo_children():
                    widget.destroy()

                if not self.events:
                    # No events message
                    no_events_label = tk.Label(
                        self.content_frame,
                        text=f"No events found for {self.current_view} view\n\nConfigure accounts on the server\nat http://{self.server_host}:{self.server_port}",
                        font=('Arial', 16),
                        fg='#666666',
                        bg='white',
                        justify=tk.CENTER
                    )
                    no_events_label.pack(expand=True, pady=50)
                else:
                    # Show events
                    self._render_events()
        except Exception as e:
            print(f"Error updating calendar content: {e}")

    def _render_events(self):
        """Render events in the content area"""
        try:
            # Group events by date
            events_by_date = {}
            for event in self.events:
                try:
                    # Parse event start time
                    start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    date_key = start_time.date()

                    if date_key not in events_by_date:
                        events_by_date[date_key] = []
                    events_by_date[date_key].append(event)
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue

            # Sort dates
            sorted_dates = sorted(events_by_date.keys())

            # Render each date group
            for date in sorted_dates:
                date_events = events_by_date[date]

                # Date header
                date_frame = tk.Frame(self.content_frame, bg='#f0f0f0', relief=tk.RAISED, bd=1)
                date_frame.pack(fill=tk.X, pady=(10, 0), padx=10)

                date_label = tk.Label(
                    date_frame,
                    text=date.strftime('%A, %B %d'),
                    font=('Arial', 14, 'bold'),
                    fg='#333333',
                    bg='#f0f0f0'
                )
                date_label.pack(pady=5)

                # Events for this date
                for event in sorted(date_events, key=lambda e: e['start_time']):
                    self._render_event(event)

        except Exception as e:
            print(f"Error rendering events: {e}")

    def _render_event(self, event):
        """Render a single event"""
        try:
            event_frame = tk.Frame(self.content_frame, bg='white', relief=tk.RAISED, bd=1)
            event_frame.pack(fill=tk.X, pady=2, padx=20)

            # Color bar
            color = event.get('color', '#4285f4')
            color_frame = tk.Frame(event_frame, bg=color, width=5)
            color_frame.pack(side=tk.LEFT, fill=tk.Y)

            # Event content
            content_frame = tk.Frame(event_frame, bg='white')
            content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Title
            title_label = tk.Label(
                content_frame,
                text=event['title'],
                font=('Arial', 12, 'bold'),
                fg='#333333',
                bg='white',
                anchor='w'
            )
            title_label.pack(fill=tk.X)

            # Time and location
            details = []
            if not event.get('all_day', False):
                try:
                    start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))

                    if start_time.date() == end_time.date():
                        time_str = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                    else:
                        time_str = f"{start_time.strftime('%H:%M')} +"

                    details.append(time_str)
                except Exception:
                    details.append("All day")
            else:
                details.append("All day")

            if event.get('location'):
                details.append(f"📍 {event['location']}")

            if details:
                details_label = tk.Label(
                    content_frame,
                    text=" • ".join(details),
                    font=('Arial', 10),
                    fg='#666666',
                    bg='white',
                    anchor='w'
                )
                details_label.pack(fill=tk.X)

            # Description (if available and not too long)
            if event.get('description') and len(event['description']) < 100:
                desc_label = tk.Label(
                    content_frame,
                    text=event['description'],
                    font=('Arial', 9),
                    fg='#888888',
                    bg='white',
                    anchor='w',
                    wraplength=400
                )
                desc_label.pack(fill=tk.X, pady=(2, 0))

        except Exception as e:
            print(f"Error rendering event: {e}")

    def _update_connection_status(self, connected: bool):
        """Update connection status indicator"""
        try:
            if self.status_label:
                if connected:
                    self.status_label.config(fg='green')  # Green = connected
                else:
                    self.status_label.config(fg='red')  # Red = disconnected
        except Exception as e:
            print(f"Error updating connection status: {e}")

    def _show_connection_error(self):
        """Show connection error dialog"""
        try:
            if self.root:
                messagebox.showerror(
                    "Connection Error",
                    f"Cannot connect to calendar server at {self.server_host}:{self.server_port}\n\n"
                    "Please check:\n"
                    "• Network connection\n"
                    "• Server is running\n"
                    "• Server IP address is correct"
                )
        except Exception as e:
            print(f"Error showing connection error: {e}")

    def _get_date_range(self) -> tuple:
        """Get start and end dates for current view"""
        if self.current_view == 'day':
            start_date = self.current_date
            end_date = start_date + timedelta(days=1)
        elif self.current_view == 'week':
            # Start from beginning of week (Monday)
            days_since_monday = self.current_date.weekday()
            start_date = self.current_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=7)
        else:  # month
            # Start from beginning of month
            start_date = self.current_date.replace(day=1)
            # End at beginning of next month
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)

        return start_date, end_date

    def _change_view(self, view: str):
        """Change the calendar view"""
        if view != self.current_view:
            self.current_view = view
            self._refresh_data()

    def _prev_period(self):
        """Navigate to previous period"""
        if self.current_view == 'day':
            self.current_date -= timedelta(days=1)
        elif self.current_view == 'week':
            self.current_date -= timedelta(weeks=1)
        else:  # month
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)

        self._refresh_data()

    def _next_period(self):
        """Navigate to next period"""
        if self.current_view == 'day':
            self.current_date += timedelta(days=1)
        elif self.current_view == 'week':
            self.current_date += timedelta(weeks=1)
        else:  # month
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)

        self._refresh_data()

    def goto_today(self):
        """Navigate to today (called by touch handler)"""
        self.current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self._refresh_data()

    def get_server_status(self) -> Dict[str, Any]:
        """Get server status information"""
        try:
            return self.api_client.get_status() or {}
        except Exception:
            return {}


def load_client_config() -> Dict[str, Any]:
    """Load client configuration from file"""
    config_file = Path.home() / '.pi_calendar_client' / 'config.json'

    default_config = {
        'server_host': '192.168.1.100',  # Default Pi 4 IP
        'server_port': 5000,
        'refresh_interval': 300,  # 5 minutes
        'connection_timeout': 10,
        'fullscreen': True,
        'development_mode': False
    }

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

    return default_config


def save_client_config(config: Dict[str, Any]):
    """Save client configuration to file"""
    config_dir = Path.home() / '.pi_calendar_client'
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / 'config.json'

    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")


def main():
    """Main entry point for Pi Zero display client"""
    import argparse

    parser = argparse.ArgumentParser(description='Pi Zero Calendar Display Client')
    parser.add_argument('--server', '-s', default=None, help='Server IP address')
    parser.add_argument('--port', '-p', type=int, default=None, help='Server port')
    parser.add_argument('--dev', action='store_true', help='Development mode (windowed)')

    args = parser.parse_args()

    # Load configuration
    config = load_client_config()

    # Override with command line arguments
    if args.server:
        config['server_host'] = args.server
    if args.port:
        config['server_port'] = args.port
    if args.dev:
        config['development_mode'] = True
        config['fullscreen'] = False

    print("Pi Zero Calendar Display Client")
    print(f"Server: {config['server_host']}:{config['server_port']}")

    # Create and start display application
    app = CalendarDisplayApp(
        server_host=config['server_host'],
        server_port=config['server_port']
    )

    # Set fullscreen mode
    app.is_fullscreen = config['fullscreen']

    try:
        app.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting display: {e}")
    finally:
        app.stop()


if __name__ == '__main__':
    main()
