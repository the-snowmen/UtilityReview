from win10toast import ToastNotifier

# Instantiate a single notifier for reuse
toaster = ToastNotifier()

def safe_toast(title: str, msg: str, duration: int = 3) -> None:
    """
    Show a Windows desktop notification via ToastNotifier, swallowing any errors.

    Args:
      title: Notification title text.
      msg:   Notification body text.
      duration: Seconds to display the toast.
    """
    try:
        toaster.show_toast(title, msg, duration=duration, threaded=True)
    except Exception:
        # If notifications fail (e.g. missing Windows APIs), ignore.
        pass
