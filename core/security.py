import re

DANGEROUS_PATTERNS = [
    r"send_code",
    r"sign_in",
    r"get_me",
    r"\.session",
    r"delete_account",
    r"log_out",
    r"add_contact",
    r"import_contacts",
    r"get_contacts",
    r"join_chat",
    r"leave_chat",
    r"set_2fa",
    r"get_password",
    r"base64\.b64decode",
    r"exec\(",
    r"eval\(",
    r"requests\.get", # Potential data exfiltration
    r"httpx\.",
    r"aiohttp\.ClientSession"
]

OFFICIAL_SOURCES = [
    "github.com/faustyu1",
    "raw.githubusercontent.com/faustyu1",
    # Add other official repos here
]

def analyze_module(content: str) -> list[str]:
    """Analyze module content for dangerous patterns."""
    found = []
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            found.append(pattern)
    return found

def is_official(url: str) -> bool:
    """Check if the URL is from an official source."""
    return any(source in url for source in OFFICIAL_SOURCES)
