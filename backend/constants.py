"""
Application constants — activity types, icons, defaults
Single source of truth for backend data structures
"""

# Role hierarchy and minimum stats (0-100) required for the position
# Used for AI career recommendation
ROLE_REQUIREMENTS = {
    "Junior": {
        "productivity": 30,
        "quality": 40,
        "collaboration": 50,
        "reliability": 40,
        "initiative": 35,
        "expertise": 35,
    },
    "Mid": {
        "productivity": 50,
        "quality": 55,
        "collaboration": 55,
        "reliability": 55,
        "initiative": 50,
        "expertise": 50,
    },
    "Senior": {
        "productivity": 65,
        "quality": 70,
        "collaboration": 65,
        "reliability": 70,
        "initiative": 60,
        "expertise": 70,
    },
    "Staff": {
        "productivity": 75,
        "quality": 80,
        "collaboration": 75,
        "reliability": 80,
        "initiative": 70,
        "expertise": 80,
    },
    "Lead": {
        "productivity": 80,
        "quality": 85,
        "collaboration": 90,
        "reliability": 85,
        "initiative": 80,
        "expertise": 85,
    },
}

# Activity type → (icon, color) for feed display
ACTIVITY_ICONS = {
    "commit": ("commit", "emerald"),
    "review": ("rate_review", "blue"),
    "merge": ("merge_type", "amber"),
    "deploy": ("rocket_launch", "primary"),
    "fix": ("bug_report", "red"),
    "security": ("security", "red"),
}

# Default avatar URL template
AVATAR_URL = "https://ui-avatars.com/api/?name={name}&background=135bec&color=fff"
