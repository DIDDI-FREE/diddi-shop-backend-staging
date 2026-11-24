SERVICE_SCOPES: dict[str, tuple[str, ...]] = {
    "diddipay": (
        "diddipay:payment-intents:read",
        "diddipay:payment-intents:write",
        "diddipay:payment-intents:refund",
        "diddipay:marketplace:release",
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
    "diddicomms": ("diddicomms:tasks:write", "diddicomms:context:read"),
    "diddisupport": ("diddisupport:cases:write", "diddisupport:context:read"),
    "diddiobserve": ("diddiobserve:telemetry:write",),
}


def required_scopes(service: str) -> tuple[str, ...]:
    return SERVICE_SCOPES.get(service, ())
