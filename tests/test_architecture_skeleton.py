from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_required_module_boundaries_exist():
    modules = {
        "shops", "catalog", "cart", "checkout", "orders", "claims",
        "rewards", "campaigns", "comms", "support", "observability", "audit", "admin",
    }
    existing = {path.name for path in (ROOT / "app_base" / "modules").iterdir() if path.is_dir()}
    assert modules <= existing


def test_external_adapters_are_isolated():
    integrations = ROOT / "app_base" / "integrations"
    for name in ("diddipay.py", "diddisend.py", "diddifiles.py", "diddirewards.py", "diddicomms.py", "diddisupport.py", "diddiobserve.py"):
        assert (integrations / name).exists()
