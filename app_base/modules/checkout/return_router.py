from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["checkout"])


@router.get("/payments/return", response_class=HTMLResponse)
async def payment_browser_return() -> HTMLResponse:
    """Browser landing only. Query parameters never confirm a payment."""
    return HTMLResponse(
        """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Retour vers DiddiShop</title></head><body><main>
<h1>Retour vers DiddiShop</h1>
<p>Vous pouvez fermer cette page et revenir dans l’application DiddiShop
pour consulter l’état de votre paiement.</p>
<p>Cette page ne confirme pas le paiement. Seul le statut affiché dans
l’application fait foi après vérification auprès du service de paiement.</p>
</main></body></html>""",
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )
