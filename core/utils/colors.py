class Colors:
    # --- Reset ---
    RESET = "\033[0m"

    # --- Standard Foreground Colors ---
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # --- Bright/Bold Foreground Colors (Often look better) ---
    BRIGHT_BLACK = "\033[90m"  # Dark Gray
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # --- Background Colors ---
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # --- Styles ---
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"      # Use sparingly!
    REVERSE = "\033[7m"    # Swaps FG and BG
    HIDDEN = "\033[8m"     # Useful for passwords
    
    @staticmethod
    def colorize(text: str, color_code: str) -> str:
        """Wraps text in a color code and resets it immediately after."""
        return f"{color_code}{text}\033[0m"