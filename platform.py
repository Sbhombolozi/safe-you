"""Platform capability checks; native features remain explicit integration points."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformCapabilities:
    platform: str
    is_android: bool
    is_ios: bool
    is_windows: bool
    background_audio_bridge_required: bool
    launcher_identity_bridge_required: bool
    foreground_capture_only: bool


def detect_platform(platform_value: object) -> PlatformCapabilities:
    """Map Flet's page.platform value to capability flags."""
    platform_name = str(getattr(platform_value, "value", platform_value) or "unknown").lower()
    is_android = platform_name == "android"
    is_ios = platform_name == "ios"
    is_windows = platform_name == "windows"
    return PlatformCapabilities(
        platform=platform_name,
        is_android=is_android,
        is_ios=is_ios,
        is_windows=is_windows,
        background_audio_bridge_required=is_android,
        launcher_identity_bridge_required=is_android,
        foreground_capture_only=not is_android,
    )
