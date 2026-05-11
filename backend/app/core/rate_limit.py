from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by IP — swap get_remote_address for org-based key in production
limiter = Limiter(key_func=get_remote_address)