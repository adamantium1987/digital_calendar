# client/ui/touch_handler.py
"""
Touch gesture handler for Pi Zero touchscreen interface
Detects and processes touch gestures: tap, swipe, long-press, double-tap
"""

import tkinter as tk
from datetime import datetime, timedelta
from typing import Callable, Optional, Tuple, Dict, Any
import time


class TouchHandler:
    """Handles touch gestures on the Pi Zero touchscreen display"""

    # Gesture thresholds
    SWIPE_THRESHOLD = 50  # Minimum pixels for a swipe
    LONG_PRESS_DURATION = 0.8  # Seconds for long press
    DOUBLE_TAP_WINDOW = 0.3  # Seconds between taps for double-tap
    TAP_MOVE_TOLERANCE = 10  # Max pixel movement for a tap
    EDGE_THRESHOLD = 60  # Pixels from edge for edge detection

    def __init__(self, canvas: tk.Canvas, screen_width: int, screen_height: int):
        """Initialize touch handler

        Args:
            canvas: Tkinter canvas to bind events to
            screen_width: Width of the display in pixels
            screen_height: Height of the display in pixels
        """
        self.canvas = canvas
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Touch tracking state
        self.touch_start_pos: Optional[Tuple[int, int]] = None
        self.touch_start_time: Optional[float] = None
        self.last_tap_time: Optional[float] = None
        self.last_tap_pos: Optional[Tuple[int, int]] = None
        self.is_touching = False
        self.long_press_triggered = False

        # Gesture callbacks
        self.on_tap: Optional[Callable[[int, int], None]] = None
        self.on_double_tap: Optional[Callable[[int, int], None]] = None
        self.on_long_press: Optional[Callable[[int, int], None]] = None
        self.on_swipe_left: Optional[Callable[[], None]] = None
        self.on_swipe_right: Optional[Callable[[], None]] = None
        self.on_swipe_up: Optional[Callable[[], None]] = None
        self.on_swipe_down: Optional[Callable[[], None]] = None
        self.on_edge_tap: Optional[Callable[[str], None]] = None

        # Long press timer
        self.long_press_timer = None

        # Bind touch/mouse events
        self._bind_events()

    def _bind_events(self):
        """Bind touch and mouse events to the canvas"""
        self.canvas.bind('<Button-1>', self._on_touch_start)
        self.canvas.bind('<B1-Motion>', self._on_touch_move)
        self.canvas.bind('<ButtonRelease-1>', self._on_touch_end)

    def _on_touch_start(self, event):
        """Handle touch/click start event"""
        self.touch_start_pos = (event.x, event.y)
        self.touch_start_time = time.time()
        self.is_touching = True
        self.long_press_triggered = False
        self._start_long_press_timer()

    def _on_touch_move(self, event):
        """Handle touch/drag movement"""
        if not self.is_touching or not self.touch_start_pos:
            return

        dx = event.x - self.touch_start_pos[0]
        dy = event.y - self.touch_start_pos[1]
        distance = (dx**2 + dy**2) ** 0.5

        if distance > self.TAP_MOVE_TOLERANCE:
            self._cancel_long_press_timer()

    def _on_touch_end(self, event):
        """Handle touch/click release event"""
        if not self.is_touching or not self.touch_start_pos or not self.touch_start_time:
            return

        self._cancel_long_press_timer()

        touch_end_pos = (event.x, event.y)
        dx = touch_end_pos[0] - self.touch_start_pos[0]
        dy = touch_end_pos[1] - self.touch_start_pos[1]
        distance = (dx**2 + dy**2) ** 0.5

        self.is_touching = False

        if self.long_press_triggered:
            return

        if distance < self.TAP_MOVE_TOLERANCE:
            self._handle_tap(touch_end_pos[0], touch_end_pos[1])
        elif distance >= self.SWIPE_THRESHOLD:
            self._handle_swipe(dx, dy)

    def _handle_tap(self, x: int, y: int):
        """Handle tap gesture"""
        current_time = time.time()

        edge = self._detect_edge_tap(x, y)
        if edge and self.on_edge_tap:
            self.on_edge_tap(edge)
            return

        if (self.last_tap_time and self.last_tap_pos and
            (current_time - self.last_tap_time) < self.DOUBLE_TAP_WINDOW):
            
            last_x, last_y = self.last_tap_pos
            tap_distance = ((x - last_x)**2 + (y - last_y)**2) ** 0.5
            
            if tap_distance < self.TAP_MOVE_TOLERANCE * 2:
                if self.on_double_tap:
                    self.on_double_tap(x, y)
                self.last_tap_time = None
                self.last_tap_pos = None
                return

        if self.on_tap:
            self.on_tap(x, y)

        self.last_tap_time = current_time
        self.last_tap_pos = (x, y)

    def _handle_swipe(self, dx: int, dy: int):
        """Handle swipe gesture"""
        if abs(dx) > abs(dy):
            if dx > 0:
                if self.on_swipe_right:
                    self.on_swipe_right()
            else:
                if self.on_swipe_left:
                    self.on_swipe_left()
        else:
            if dy > 0:
                if self.on_swipe_down:
                    self.on_swipe_down()
            else:
                if self.on_swipe_up:
                    self.on_swipe_up()

    def _detect_edge_tap(self, x: int, y: int) -> Optional[str]:
        """Detect if tap is near screen edge"""
        if x < self.EDGE_THRESHOLD:
            return 'left'
        elif x > self.screen_width - self.EDGE_THRESHOLD:
            return 'right'
        elif y < self.EDGE_THRESHOLD:
            return 'top'
        elif y > self.screen_height - self.EDGE_THRESHOLD:
            return 'bottom'
        return None

    def _start_long_press_timer(self):
        """Start timer for long press detection"""
        self._cancel_long_press_timer()
        self.long_press_timer = self.canvas.after(
            int(self.LONG_PRESS_DURATION * 1000),
            self._trigger_long_press
        )

    def _cancel_long_press_timer(self):
        """Cancel long press timer"""
        if self.long_press_timer:
            self.canvas.after_cancel(self.long_press_timer)
            self.long_press_timer = None

    def _trigger_long_press(self):
        """Trigger long press callback"""
        if self.is_touching and self.touch_start_pos and self.on_long_press:
            self.long_press_triggered = True
            x, y = self.touch_start_pos
            self.on_long_press(x, y)

    def set_tap_callback(self, callback: Callable[[int, int], None]):
        """Set callback for single tap gesture"""
        self.on_tap = callback

    def set_double_tap_callback(self, callback: Callable[[int, int], None]):
        """Set callback for double tap gesture"""
        self.on_double_tap = callback

    def set_long_press_callback(self, callback: Callable[[int, int], None]):
        """Set callback for long press gesture"""
        self.on_long_press = callback

    def set_swipe_left_callback(self, callback: Callable[[], None]):
        """Set callback for swipe left gesture"""
        self.on_swipe_left = callback

    def set_swipe_right_callback(self, callback: Callable[[], None]):
        """Set callback for swipe right gesture"""
        self.on_swipe_right = callback

    def set_swipe_up_callback(self, callback: Callable[[], None]):
        """Set callback for swipe up gesture"""
        self.on_swipe_up = callback

    def set_swipe_down_callback(self, callback: Callable[[], None]):
        """Set callback for swipe down gesture"""
        self.on_swipe_down = callback

    def set_edge_tap_callback(self, callback: Callable[[str], None]):
        """Set callback for edge tap gesture"""
        self.on_edge_tap = callback

    def reset_state(self):
        """Reset all touch state"""
        self._cancel_long_press_timer()
        self.touch_start_pos = None
        self.touch_start_time = None
        self.last_tap_time = None
        self.last_tap_pos = None
        self.is_touching = False
        self.long_press_triggered = False


class TouchGestureHelper:
    """Helper class with common gesture patterns for calendar navigation"""

    @staticmethod
    def setup_calendar_gestures(touch_handler: TouchHandler, 
                                calendar_view,
                                navigate_callback: Callable[[str], None]):
        """Set up standard calendar navigation gestures"""
        touch_handler.set_swipe_left_callback(lambda: navigate_callback('next'))
        touch_handler.set_swipe_right_callback(lambda: navigate_callback('prev'))
        touch_handler.set_swipe_up_callback(lambda: navigate_callback('cycle_view'))
        touch_handler.set_swipe_down_callback(lambda: navigate_callback('cycle_view'))
        touch_handler.set_long_press_callback(lambda x, y: navigate_callback('today'))
        touch_handler.set_double_tap_callback(lambda x, y: navigate_callback('today'))
        
        def handle_edge_tap(edge):
            if edge == 'left':
                navigate_callback('prev')
            elif edge == 'right':
                navigate_callback('next')
            elif edge == 'top':
                navigate_callback('cycle_view')
        
        touch_handler.set_edge_tap_callback(handle_edge_tap)
        touch_handler.set_tap_callback(lambda x, y: calendar_view.handle_tap(x, y))


if __name__ == '__main__':
    print("Touch Handler Test - Run from main app")
