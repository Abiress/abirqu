"""Deprecation utilities for AbirQu API stability."""

import functools
import warnings
from typing import Callable, Optional


def deprecated(
    msg: str,
    since: Optional[str] = None,
    removal: Optional[str] = None,
) -> Callable:
    """Decorator that marks a function/class as deprecated.

    Emits a DeprecationWarning when the decorated callable is used.

    Args:
        msg: Explanation of the deprecation and what to use instead.
        since: Version when the API was deprecated (e.g. "1.1.0").
        removal: Planned removal version (e.g. "1.3.0").

    Example:
        @deprecated("Use new_func() instead.", since="1.1.0", removal="1.3.0")
        def old_func():
            ...
    """
    reason = msg
    if since:
        reason = f"Deprecated since {since}. {reason}"
    if removal:
        reason = f"{reason} Removal in {removal}."

    def decorator(obj):
        if isinstance(obj, type):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(
                    f"Class {obj.__name__} is deprecated. {reason}",
                    DeprecationWarning,
                    stacklevel=2,
                )
                return original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            obj._deprecation_msg = reason
            return obj

        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"Function {obj.__name__} is deprecated. {reason}",
                DeprecationWarning,
                stacklevel=2,
            )
            return obj(*args, **kwargs)

        wrapper._deprecation_msg = reason
        return wrapper

    return decorator


def deprecated_alias(old_name: str, new_func: Callable) -> Callable:
    """Create a deprecated alias for a renamed function.

    The alias emits a DeprecationWarning directing users to the new name,
    then delegates to ``new_func``.

    Args:
        old_name: The legacy name (used in the warning).
        new_func: The current function to delegate to.

    Example:
        def new_func():
            ...

        old_func = deprecated_alias("old_func", new_func)
    """

    @functools.wraps(new_func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{old_name} is deprecated. Use {new_func.__name__} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return new_func(*args, **kwargs)

    wrapper._deprecation_msg = f"Renamed to {new_func.__name__}"
    return wrapper


def experimental(msg: str = "") -> Callable:
    """Decorator that marks a function/class as experimental.

    Experimental APIs may change or be removed without following the
    normal deprecation timeline.

    Args:
        msg: Optional description of the experimental status.

    Example:
        @experimental("This API is unstable and may change.")
        def new_feature():
            ...
    """

    def decorator(obj):
        tag = f"[EXPERIMENTAL] {msg}" if msg else "[EXPERIMENTAL]"

        if isinstance(obj, type):
            original_init = obj.__init__

            @functools.wraps(original_init)
            def new_init(self, *args, **kwargs):
                warnings.warn(
                    f"Class {obj.__name__} is experimental. {tag}",
                    UserWarning,
                    stacklevel=2,
                )
                return original_init(self, *args, **kwargs)

            obj.__init__ = new_init
            obj._experimental = True
            obj._experimental_msg = tag
            return obj

        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"Function {obj.__name__} is experimental. {tag}",
                UserWarning,
                stacklevel=2,
            )
            return obj(*args, **kwargs)

        wrapper._experimental = True
        wrapper._experimental_msg = tag
        return wrapper

    return decorator
