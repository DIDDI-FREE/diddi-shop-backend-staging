# Intégration DiddiFiles

DiddiShop ne stocke pas le binaire des photos produit. Il demande une session
d’upload, confirme le fichier et conserve une référence `file_id` avec le
purpose `diddishop_product_image`. Le contrat staging DiddiFiles utilise
`module_owner`, `purpose`, `filename`, `mime_type`, `size_bytes` et `metadata`.

## Parcours

```text
vendeur -> create upload session
        -> upload vers DiddiFiles/S3
        -> confirm upload
        -> enregistrer file_id + metadata
client  -> demander URL publique ou signée selon visibilité
```

Le vendeur utilise les routes DiddiShop suivantes :

1. `POST /v1/catalog/products/{product_id}/photos/upload-session` avec
   `filename`, `content_type` et `size_bytes` ; DiddiShop traduit vers le
   contrat DiddiFiles avec `module_owner=diddishop`,
   `purpose=diddishop_product_image` et `mime_type`.
2. Le client envoie le fichier par `PUT` à `upload.url` avec
   `upload.headers` et ne contacte pas DiddiFiles avec un credential S2S.
3. `POST /v1/catalog/products/{product_id}/photos` avec `file_id` demande la
   confirmation DiddiFiles puis attache la référence au produit.
4. Le frontend lit `GET /v1/catalog/products/{product_id}/photos` pour obtenir
 les URLs publiques ou signées retournées par DiddiFiles.

La réponse de session contient `file_id`, `status` et `upload` (`method`, `url`,
`expires_in_seconds`, `headers`). La réponse photos contient une enveloppe
`items` avec `file_id` et `url`.

Le frontend doit reprendre exactement `upload.method`, `upload.url` et chaque
entrée de `upload.headers` pour le `PUT`. Seule la signature d’upload a une
durée (`expires_in_seconds`) ; le contrat DiddiFiles actuellement vérifié ne
définit pas de suppression automatique d’un fichier `pending` jamais joint à
une réclamation. La confirmation et l’attachement restent donc obligatoires.

Les routes DiddiFiles upload-session, confirmation, metadata, download-url et
public-url restent derrière l’adaptateur S2S. La visibilité finale, la durée
des URLs signées et la lecture du purpose produit restent à confirmer avec
DiddiFiles en staging.
