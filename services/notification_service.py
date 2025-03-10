from plyer import notification
import os

class NotificationServices:
    @staticmethod
    def send_notification(title, message):
        """Displays a desktop notification with a custom icon. """
        icon_path = "./OS.ico"
        if icon_path and not os.path.exists(icon_path):
            print(f"Warning: Icon file '{icon_path}' not found. Using default icon.")
            icon_path = None  # Fallback to default

        try:
            notification.notify(
                title=title,
                message=message,
                app_name="AutoDownloader",
                app_icon=icon_path,
                timeout=10,
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
