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

Les routes upload-session, confirmation, metadata, download-url et public-url
sont couvertes par l’adaptateur et les tests de câblage. La visibilité finale,
la durée des URLs signées et la lecture du purpose produit restent à confirmer
avec DiddiFiles en staging.
