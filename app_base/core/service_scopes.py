SERVICE_SCOPES: dict[str, tuple[str, ...]] = {
    "diddipay": (
        "diddipay:payment-intents:read",
        "diddipay:payment-intents:write",
        "diddipay:payment-intents:refund",
    ),
    "diddisend": (
        "diddisend:deliveries:quote",
        "diddisend:deliveries:write",
        "diddisend:deliveries:read",
        "diddisend:deliveries:cancel",
    ),
    "diddifiles": ("files:read", "files:write"),
    "diddirewards": (
        "diddirewards:benefits:quote",
        "diddirewards:benefits:reserve",
        "diddirewards:benefits:consume",
        "diddirewards:benefits:correct",
        "diddirewards:campaigns:read",
    ),
    "diddicomms": ("diddishop:comms-task:write", "diddishop:comms-task:read"),
    "diddisupport": ("diddishop:support-context:read", "diddishop:support-case:write"),
    "diddiobserve": ("diddiobserve:telemetry:write",),
}


def required_scopes(service: str) -> tuple[str, ...]:
    return SERVICE_SCOPES.get(service, ())
