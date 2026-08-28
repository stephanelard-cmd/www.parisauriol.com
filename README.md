# Paris Auriol Austerlitz Arena

Site officiel de présentation du meublé situé au 18 boulevard Vincent Auriol, 75013 Paris.

## Publication GitHub Pages

Le site est statique et doit être publié directement depuis la branche `main` :

1. Ouvrir **Settings → Pages**.
2. Dans **Build and deployment**, choisir **Source: Deploy from a branch**.
3. Choisir **Branch: main** et **Folder: / (root)**.
4. Cliquer sur **Save**.
5. Dans **Custom domain**, saisir `parisauriol.com`, puis enregistrer.
6. Après validation du DNS et du certificat, activer **Enforce HTTPS**.

Le fichier `CNAME` et le fichier `.nojekyll` sont déjà présents. Toute modification de `main`, y compris la mise à jour automatique du calendrier, déclenchera la republication par GitHub Pages.

## DNS OVH

À configurer dans la zone DNS de `parisauriol.com` :

- `A` sur le domaine racine vers `185.199.108.153`
- `A` sur le domaine racine vers `185.199.109.153`
- `A` sur le domaine racine vers `185.199.110.153`
- `A` sur le domaine racine vers `185.199.111.153`
- `CNAME` pour `www` vers `stephanelard-cmd.github.io.`

Supprimer les anciens enregistrements `A`, `AAAA` ou `CNAME` incompatibles pour `@` et `www` avant de les remplacer.

## Synchronisation Airbnb + Booking.com

Le workflow `.github/workflows/sync-calendars.yml` s’exécute toutes les quinze minutes. Il exige deux secrets du dépôt :

- `AIRBNB_ICAL_URL`
- `BOOKING_ICAL_URL`

Les liens iCal restent secrets. Seules les périodes anonymisées occupé/disponible sont publiées dans `data/calendar.json`.

## Contenu

Accueil, logement, galerie, disponibilités, quartier et accès, guide local, agenda officiel du 13e, règles du séjour, mentions légales, confidentialité, SEO, sitemap et page 404.
