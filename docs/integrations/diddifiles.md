# Intégration DiddiFiles

DiddiShop ne stocke pas le binaire des photos produit. Il demande une session
d’upload, confirme le fichier et conserve une référence `file_id` avec le
purpose `diddishop_product_image`.

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
   `filename`, `content_type` et `size_bytes` ; DiddiShop appelle DiddiFiles
   avec `purpose=diddishop_product_image`.
2. Le client envoie le fichier à l’URL retournée par DiddiFiles.
3. Après confirmation, `POST /v1/catalog/products/{product_id}/photos` avec
   `file_id` attache la référence au produit.
4. Le frontend lit `GET /v1/catalog/products/{product_id}/photos` pour obtenir
   les URLs publiques ou signées retournées par DiddiFiles.

Les routes DiddiFiles upload-session, confirmation, metadata, download-url et
public-url restent derrière l’adaptateur S2S. La visibilité finale, la durée
des URLs signées et la lecture du purpose produit restent à confirmer avec
DiddiFiles en staging.
