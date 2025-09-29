# client/ui/theme.py
"""
Modern theme configuration for calendar UI
Centralizes colors, fonts, and styling constants
"""


class ModernTheme:
    """Modern calendar theme with clean design"""

    # Color palette
    COLORS = {
        'background': '#ffffff',
        'surface': '#f8f9fa',
        'grid_line': '#e9ecef',
        'today': '#e3f2fd',
        'today_accent': '#2196f3',
        'event_default': '#2196f3',
        'event_text': '#ffffff',
        'text_primary': '#212529',
        'text_secondary': '#6c757d',
        'text_tertiary': '#adb5bd',
        'header_bg': '#ffffff',
        'shadow': '#00000008',
        'border': '#dee2e6'
    }

    # Layout constants
    LAYOUT = {
        'margin': 20,
        'small_margin': 15,
        'padding': 15,
        'small_padding': 8,
        'card_radius': 12,
        'compact_radius': 8,
        'dot_size': 6,
        'dot_spacing': 8,
        'circle_radius_large': 30,
        'circle_radius_medium': 18,
        'circle_radius_small': 16,
        'card_height': 85,
        'compact_height': 40,
        'cell_height': 90,
        'header_height': 70
    }

    @staticmethod
    def get_fonts(screen_width: int):
        """Get font definitions based on screen size

        Args:
            screen_width: Screen width in pixels

        Returns:
            Dictionary of font configurations
        """
        return {
            'header': ('Helvetica Neue', max(16, screen_width // 70), 'bold'),
            'subheader': ('Helvetica Neue', max(12, screen_width // 90)),
            'event_title': ('Helvetica Neue', max(11, screen_width // 95), 'bold'),
            'event_time': ('Helvetica Neue', max(9, screen_width // 110)),
            'event_location': ('Helvetica Neue', max(8, screen_width // 120)),
            'day_number': ('Helvetica Neue', max(20, screen_width // 50), 'bold'),
            'day_name': ('Helvetica Neue', max(10, screen_width // 100), 'bold'),
            'time_label': ('Helvetica Neue', max(9, screen_width // 110)),
            'compact_time': ('Helvetica Neue', 8),
            'event_more': ('Helvetica Neue', 7)
        }