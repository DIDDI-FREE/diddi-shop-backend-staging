SERVICE_SCOPES: dict[str, tuple[str, ...]] = {
    "diddipay": (
        "diddipay:payment-intents:read",
        "diddipay:payment-intents:write",
        "diddipay:payment-intents:refund",
    ),
    "diddisend": (
        "diddisend:deliveries:quote",
        "diddisend:deliveries:create",
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
    # The staging OpenAPI does not publish an S2S scope for this route yet.
    "diddicomms": (),
    "diddisupport": ("diddishop:support-context:read", "diddishop:support-case:write"),
    # DiddiObserve is authenticated with its dedicated OTLP Basic credential;
    # it does not use a DiddiFreeID business scope.
    "diddiobserve": (),
}


def required_scopes(service: str) -> tuple[str, ...]:
    return SERVICE_SCOPES.get(service, ())
