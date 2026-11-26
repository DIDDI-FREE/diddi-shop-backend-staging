# S23-B — Journal

- DiddiPay accepte `wave`, `mtn_momo`, `orange_money` et une `return_url`
  limitée à DiddiFree/localhost.
- La réponse paiement expose `payment_method` et `expires_at` lorsqu’ils sont
  disponibles.
- `GET /v1/orders` accepte `limit` et un curseur opaque.
- `OrderResponse` expose `delivered_at` et `status_history` horodaté.
