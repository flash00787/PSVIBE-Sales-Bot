"""PS VIBE Bot — Handlers package (Phase 6 refactor).
Domain-split modules for maintainability.

All handler functions are re-exported for backward compatibility.
"""
# ═══════ Domain handler modules ═══════

from .admin import *  # noqa: F401,F403
from .admin_bookings import *  # noqa: F401,F403
from .attendance import *  # noqa: F401,F403
from .booking import *  # noqa: F401,F403
from .booking_flow import *  # noqa: F401,F403
from .broadcast import *  # noqa: F401,F403
from .commands import *  # noqa: F401,F403
from .console import *  # noqa: F401,F403
from .console_mgmt import *  # noqa: F401,F403
from .discount import *  # noqa: F401,F403
from .finance import *  # noqa: F401,F403
from .games import *  # noqa: F401,F403
from .ginst import *  # noqa: F401,F403
from .help import *  # noqa: F401,F403
from .main_menu import *  # noqa: F401,F403
from .members import *  # noqa: F401,F403
from .notify import *  # noqa: F401,F403
from .payroll import *  # noqa: F401,F403
from .referral import *  # noqa: F401,F403
from .reports import *  # noqa: F401,F403
from .salary_adv import *  # noqa: F401,F403
from .sales import *  # noqa: F401,F403
from .ssd_disc import *  # noqa: F401,F403
from .stock import *  # noqa: F401,F403
from .stock_in import *  # noqa: F401,F403
from .waitlist import *  # noqa: F401,F403