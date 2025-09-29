# client/ui/calendar_view.py
"""
Calendar view component for Pi Zero display
Modern, clean design with rounded corners, shadows, and better typography
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Dict, Any
import calendar
import textwrap

from .theme import ModernTheme


class CalendarView:
    """Modern calendar view component with multiple display modes"""

    def __init__(self, parent, screen_width: int, screen_height: int):
        """Initialize calendar view

        Args:
            parent: Parent tkinter widget
            screen_width: Display width in pixels
            screen_height: Display height in pixels
        """
        self.parent = parent
        self.screen_width = screen_width
        self.screen_height = screen_height

        # View state
        self.current_view = 'week'
        self.current_date = datetime.now()
        self.events = []

        # UI components
        self.container = None
        self.canvas = None
        self.scrollbar = None

        # Load theme
        self.colors = ModernTheme.COLORS
        self.layout = ModernTheme.LAYOUT
        self.fonts = ModernTheme.get_fonts(screen_width)

    def setup(self, container_frame):
        """Setup the calendar view UI

        Args:
            container_frame: Frame to contain the calendar view
        """
        self.container = container_frame

        # Create scrollable canvas
        canvas_frame = tk.Frame(self.container, bg=self.colors['background'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg=self.colors['background'],
            highlightthickness=0,
            bd=0
        )

        # Modern scrollbar styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Modern.Vertical.TScrollbar',
            background=self.colors['surface'],
            troughcolor=self.colors['background'],
            borderwidth=0,
            arrowsize=12
        )

        self.scrollbar = ttk.Scrollbar(
            canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            style='Modern.Vertical.TScrollbar'
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel for scrolling
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.canvas.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        # Make canvas focusable for keyboard events
        self.canvas.focus_set()

    def display_events(self, events: List[Dict[str, Any]], view_mode: str, base_date: datetime):
        """Display calendar events in specified view

        Args:
            events: List of event dictionaries
            view_mode: 'day', 'week', or 'month'
            base_date: Base date for the view
        """
        self.events = events
        self.current_view = view_mode
        self.current_date = base_date

        # Clear previous content
        self.canvas.delete('all')

        # Parse events
        parsed_events = self._parse_events(events)

        # Render based on view mode
        if view_mode == 'day':
            self._render_day_view(parsed_events, base_date)
        elif view_mode == 'week':
            self._render_week_view(parsed_events, base_date)
        elif view_mode == 'month':
            self._render_month_view(parsed_events, base_date)

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _parse_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse event data and add computed fields

        Args:
            events: Raw event data from server

        Returns:
            Parsed events with additional fields
        """
        parsed = []

        for event in events:
            try:
                # Parse datetime strings
                start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(event['end_time'].replace('Z', '+00:00'))

                # Convert to local time (simplified - assumes server time is local)
                start_time = start_time.replace(tzinfo=None)
                end_time = end_time.replace(tzinfo=None)

                parsed_event = {
                    'id': event['id'],
                    'title': event['title'],
                    'description': event.get('description', ''),
                    'start_time': start_time,
                    'end_time': end_time,
                    'all_day': event.get('all_day', False),
                    'location': event.get('location', ''),
                    'color': event.get('color', self.colors['event_default']),
                    'account_id': event.get('account_id', ''),

                    # Computed fields
                    'date': start_time.date(),
                    'duration_minutes': int((end_time - start_time).total_seconds() / 60),
                    'display_time': self._format_event_time(start_time, end_time, event.get('all_day', False))
                }

                parsed.append(parsed_event)

            except Exception as e:
                print(f"Error parsing event {event.get('id', 'unknown')}: {e}")

        # Sort by start time
        parsed.sort(key=lambda e: e['start_time'])

        return parsed

    def _format_event_time(self, start: datetime, end: datetime, all_day: bool) -> str:
        """Format event time for display

        Args:
            start: Start datetime
            end: End datetime
            all_day: Whether event is all-day

        Returns:
            Formatted time string
        """
        if all_day:
            return "All day"

        start_str = start.strftime('%I:%M %p').lstrip('0')

        # If same day, show time range
        if start.date() == end.date():
            end_str = end.strftime('%I:%M %p').lstrip('0')
            return f"{start_str} - {end_str}"
        else:
            # Multi-day event
            return f"{start_str}+"

    def _draw_rounded_rect(self, x, y, width, height, radius, **kwargs):
        """Draw a rounded rectangle

        Args:
            x, y: Top-left position
            width, height: Dimensions
            radius: Corner radius
            **kwargs: Canvas.create_polygon options
        """
        points = [
            x + radius, y,
            x + width - radius, y,
            x + width, y,
            x + width, y + radius,
            x + width, y + height - radius,
            x + width, y + height,
            x + width - radius, y + height,
            x + radius, y + height,
            x, y + height,
            x, y + height - radius,
            x, y + radius,
            x, y
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _render_day_view(self, events: List[Dict[str, Any]], date: datetime):
        """Render modern day view

        Args:
            events: Parsed events
            date: Date to display
        """
        canvas_width = self.canvas.winfo_width() or self.screen_width - 50
        margin = self.layout['margin']

        # Filter events for this day
        day_events = [e for e in events if e['date'] == date.date()]

        y_pos = margin

        # Modern day header
        day_name = date.strftime('%A')
        day_number = date.strftime('%d')
        month_year = date.strftime('%B %Y')

        # Day number with circle (if today)
        is_today = date.date() == datetime.now().date()

        if is_today:
            circle_radius = self.layout['circle_radius_large']
            circle_x = margin + 40
            circle_y = y_pos + 25

            self.canvas.create_oval(
                circle_x - circle_radius, circle_y - circle_radius,
                circle_x + circle_radius, circle_y + circle_radius,
                fill=self.colors['today_accent'],
                outline='',
                width=0
            )

            self.canvas.create_text(
                circle_x, circle_y,
                text=day_number,
                font=self.fonts['day_number'],
                fill='white',
                anchor='center'
            )

            text_x = circle_x + circle_radius + 15
        else:
            self.canvas.create_text(
                margin, y_pos + 10,
                text=day_number,
                font=self.fonts['day_number'],
                fill=self.colors['text_primary'],
                anchor='nw'
            )
            text_x = margin + 50

        self.canvas.create_text(
            text_x, y_pos + 5,
            text=day_name,
            font=self.fonts['day_name'],
            fill=self.colors['text_primary'],
            anchor='nw'
        )

        self.canvas.create_text(
            text_x, y_pos + 28,
            text=month_year,
            font=self.fonts['event_time'],
            fill=self.colors['text_secondary'],
            anchor='nw'
        )

        y_pos += 70

        # Divider line
        self.canvas.create_line(
            margin, y_pos,
            canvas_width - margin, y_pos,
            fill=self.colors['grid_line'],
            width=1
        )

        y_pos += 20

        if not day_events:
            # No events message with modern styling
            self.canvas.create_text(
                canvas_width // 2, y_pos + 80,
                text="No events today",
                font=self.fonts['subheader'],
                fill=self.colors['text_tertiary'],
                anchor='n'
            )
        else:
            # Render events with modern cards
            for event in day_events:
                y_pos = self._draw_event_card(event, margin, y_pos, canvas_width - (margin * 2))
                y_pos += 15  # Spacing between events

    def _render_week_view(self, events: List[Dict[str, Any]], base_date: datetime):
        """Render modern week view

        Args:
            events: Parsed events
            base_date: Start date of week
        """
        canvas_width = self.canvas.winfo_width() or self.screen_width - 50
        margin = self.layout['small_margin']

        # Calculate week start (Monday)
        days_since_monday = base_date.weekday()
        week_start = base_date - timedelta(days=days_since_monday)

        # Day column width
        day_width = (canvas_width - (margin * 2)) // 7
        header_height = self.layout['header_height']

        y_pos = 20

        # Week header
        week_end = week_start + timedelta(days=6)
        month_start = week_start.strftime('%B')
        month_end = week_end.strftime('%B')

        if month_start == month_end:
            week_header = f"{month_start} {week_start.day}-{week_end.day}, {week_end.year}"
        else:
            week_header = f"{month_start} {week_start.day} - {month_end} {week_end.day}, {week_end.year}"

        self.canvas.create_text(
            canvas_width // 2, y_pos,
            text=week_header,
            font=self.fonts['header'],
            fill=self.colors['text_primary'],
            anchor='n'
        )

        y_pos += 40

        # Day headers with modern styling
        for i in range(7):
            day = week_start + timedelta(days=i)
            x_pos = margin + (i * day_width) + (day_width // 2)
            is_today = day.date() == datetime.now().date()

            # Day name
            day_name = day.strftime('%a').upper()
            self.canvas.create_text(
                x_pos, y_pos,
                text=day_name,
                font=self.fonts['event_time'],
                fill=self.colors['text_secondary'],
                anchor='n'
            )

            # Day number with modern highlight for today
            day_num = day.strftime('%d').lstrip('0')

            if is_today:
                # Circle background for today
                circle_radius = self.layout['circle_radius_medium']
                self.canvas.create_oval(
                    x_pos - circle_radius, y_pos + 20 - circle_radius,
                    x_pos + circle_radius, y_pos + 20 + circle_radius,
                    fill=self.colors['today_accent'],
                    outline='',
                    width=0
                )
                text_color = 'white'
            else:
                text_color = self.colors['text_primary']

            self.canvas.create_text(
                x_pos, y_pos + 20,
                text=day_num,
                font=self.fonts['day_name'],
                fill=text_color,
                anchor='n'
            )

        y_pos += header_height

        # Draw subtle day columns
        for i in range(8):
            x_pos = margin + (i * day_width)
            self.canvas.create_line(
                x_pos, y_pos,
                x_pos, y_pos + 500,
                fill=self.colors['grid_line'],
                width=1
            )

        # Draw events in columns
        for i in range(7):
            day = week_start + timedelta(days=i)
            x_pos = margin + (i * day_width)

            # Highlight today column
            is_today = day.date() == datetime.now().date()
            if is_today:
                self.canvas.create_rectangle(
                    x_pos + 1, y_pos,
                    x_pos + day_width - 1, y_pos + 500,
                    fill=self.colors['today'],
                    outline='',
                    width=0
                )

            # Get events for this day
            day_events = [e for e in events if e['date'] == day.date()]

            # Draw events in this column
            event_y = y_pos + 10
            for event in day_events:
                event_height = self._draw_event_compact(
                    event, x_pos + 5, event_y, day_width - 10
                )
                event_y += event_height + 8

    def _render_month_view(self, events: List[Dict[str, Any]], base_date: datetime):
        """Render modern month view

        Args:
            events: Parsed events
            base_date: Date within the month to display
        """
        canvas_width = self.canvas.winfo_width() or self.screen_width - 50
        margin = self.layout['small_margin']

        # Get first day of month
        first_day = base_date.replace(day=1)

        # Get calendar matrix
        cal = calendar.monthcalendar(first_day.year, first_day.month)

        # Calculate cell dimensions
        cell_width = (canvas_width - (margin * 2)) // 7
        cell_height = self.layout['cell_height']

        y_pos = 20

        # Month header
        month_header = first_day.strftime('%B %Y')
        self.canvas.create_text(
            canvas_width // 2, y_pos,
            text=month_header,
            font=self.fonts['header'],
            fill=self.colors['text_primary'],
            anchor='n'
        )

        y_pos += 45

        # Day of week headers
        day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        for i, day_name in enumerate(day_names):
            x_pos = margin + (i * cell_width) + (cell_width // 2)
            self.canvas.create_text(
                x_pos, y_pos,
                text=day_name,
                font=self.fonts['event_time'],
                fill=self.colors['text_secondary'],
                anchor='n'
            )

        y_pos += 30

        # Draw calendar grid with modern styling
        for week_num, week in enumerate(cal):
            week_y = y_pos + (week_num * cell_height)

            for day_num, day in enumerate(week):
                if day == 0:  # Empty cell
                    continue

                cell_x = margin + (day_num * cell_width)
                cell_y = week_y

                # Cell background
                try:
                    cell_date = datetime(first_day.year, first_day.month, day).date()
                    is_today = cell_date == datetime.now().date()

                    # Draw cell
                    self.canvas.create_rectangle(
                        cell_x, cell_y,
                        cell_x + cell_width, cell_y + cell_height,
                        fill=self.colors['today'] if is_today else 'white',
                        outline=self.colors['grid_line'],
                        width=1
                    )

                    # Day number with modern styling
                    if is_today:
                        # Circle for today
                        circle_radius = self.layout['circle_radius_small']
                        circle_x = cell_x + cell_width - 25
                        circle_y = cell_y + 20

                        self.canvas.create_oval(
                            circle_x - circle_radius, circle_y - circle_radius,
                            circle_x + circle_radius, circle_y + circle_radius,
                            fill=self.colors['today_accent'],
                            outline='',
                            width=0
                        )

                        self.canvas.create_text(
                            circle_x, circle_y,
                            text=str(day),
                            font=self.fonts['day_name'],
                            fill='white',
                            anchor='center'
                        )
                    else:
                        self.canvas.create_text(
                            cell_x + cell_width - 10, cell_y + 10,
                            text=str(day),
                            font=self.fonts['day_name'],
                            fill=self.colors['text_primary'],
                            anchor='ne'
                        )

                    # Event indicators with modern dots
                    day_events = [e for e in events if e['date'] == cell_date]
                    if day_events:
                        self._draw_month_event_dots(
                            day_events, cell_x, cell_y, cell_width, cell_height
                        )

                except ValueError:
                    pass

    def _draw_event_card(self, event: Dict[str, Any], x: int, y: int, width: int) -> int:
        """Draw a modern event card with shadow and rounded corners

        Args:
            event: Event data
            x: X position
            y: Y position
            width: Card width

        Returns:
            Height of drawn card
        """
        height = self.layout['card_height']
        radius = self.layout['card_radius']
        padding = self.layout['padding']

        # Draw shadow
        self._draw_rounded_rect(
            x + 3, y + 3, width, height, radius,
            fill=self.colors['shadow'],
            outline=''
        )

        # Draw card background
        self._draw_rounded_rect(
            x, y, width, height, radius,
            fill=event['color'],
            outline=''
        )

        # Event title (truncated if needed)
        title_text = event['title']
        if len(title_text) > 35:
            title_text = textwrap.fill(title_text, width=35)

        self.canvas.create_text(
            x + padding, y + padding,
            text=title_text,
            font=self.fonts['event_title'],
            fill=self.colors['event_text'],
            anchor='nw',
            width=width - (padding * 2)
        )

        # Event time
        self.canvas.create_text(
            x + padding, y + height - padding - 25,
            text=event['display_time'],
            font=self.fonts['event_time'],
            fill=self.colors['event_text'],
            anchor='nw'
        )

        # Location (if available)
        if event['location']:
            location_text = event['location']
            if len(location_text) > 30:
                location_text = location_text[:27] + "..."

            self.canvas.create_text(
                x + padding, y + height - padding - 10,
                text=location_text,
                font=self.fonts['event_location'],
                fill=self.colors['event_text'],
                anchor='nw'
            )

        return height

    def _draw_event_compact(self, event: Dict[str, Any], x: int, y: int, width: int) -> int:
        """Draw a compact event card for week view

        Args:
            event: Event data
            x: X position
            y: Y position
            width: Card width

        Returns:
            Height of drawn card
        """
        height = self.layout['compact_height']
        radius = self.layout['compact_radius']
        padding = self.layout['small_padding']

        # Draw card with shadow
        self._draw_rounded_rect(
            x + 2, y + 2, width, height, radius,
            fill=self.colors['shadow'],
            outline=''
        )

        self._draw_rounded_rect(
            x, y, width, height, radius,
            fill=event['color'],
            outline=''
        )

        # Event title (truncated)
        title = event['title']
        max_chars = max(12, width // 8)
        if len(title) > max_chars:
            title = title[:max_chars - 3] + "..."

        self.canvas.create_text(
            x + padding, y + padding,
            text=title,
            font=self.fonts['event_time'],
            fill=self.colors['event_text'],
            anchor='nw'
        )

        # Event time (if not all-day)
        if not event['all_day']:
            time_text = event['start_time'].strftime('%I:%M').lstrip('0')
            self.canvas.create_text(
                x + padding, y + height - padding - 10,
                text=time_text,
                font=self.fonts['compact_time'],
                fill=self.colors['event_text'],
                anchor='nw'
            )

        return height

    def _draw_month_event_dots(self, events: List[Dict[str, Any]],
                               cell_x: int, cell_y: int,
                               cell_width: int, cell_height: int):
        """Draw modern event indicator dots in month view

        Args:
            events: Events for this day
            cell_x: Cell X position
            cell_y: Cell Y position
            cell_width: Cell width
            cell_height: Cell height
        """
        dot_size = self.layout['dot_size']
        dot_spacing = self.layout['dot_spacing']
        max_dots = min(len(events), 4)  # Show max 4 dots

        start_x = cell_x + 8
        start_y = cell_y + cell_height - 15

        for i in range(max_dots):
            dot_x = start_x + (i * dot_spacing)

            self.canvas.create_oval(
                dot_x, start_y,
                dot_x + dot_size, start_y + dot_size,
                fill=events[i]['color'],
                outline='',
                width=0
            )

        # Show "+X more" if more events
        if len(events) > max_dots:
            self.canvas.create_text(
                start_x + (max_dots * dot_spacing) + 5, start_y + 3,
                text=f"+{len(events) - max_dots}",
                font=self.fonts['event_more'],
                fill=self.colors['text_secondary'],
                anchor='w'
            )

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if self.current_view == 'month':
            # Handle different platforms
            if event.num == 4:  # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                self.canvas.yview_scroll(1, "units")
            else:  # Windows/Mac
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def get_event_at_position(self, x: int, y: int) -> Dict[str, Any]:
        """Get event at screen position (for touch interaction)

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Event data if found, None otherwise
        """
        canvas_x = self.canvas.canvasx(x)
        canvas_y = self.canvas.canvasy(y)

        items = self.canvas.find_overlapping(canvas_x, canvas_y, canvas_x, canvas_y)

        # This is simplified - in production, you'd maintain a mapping
        # of canvas items to events for accurate lookup
        if items and self.events:
            return self.events[0]

        return None