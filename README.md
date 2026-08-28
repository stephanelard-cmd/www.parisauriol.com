# Paris Auriol Austerlitz Arena

Site officiel de présentation du meublé situé au 18 boulevard Vincent Auriol, 75013 Paris.

## Publication

Le site est déployé par GitHub Actions avec le workflow `.github/workflows/deploy-pages.yml`.

Pour la première activation :

1. Ouvrir **Settings → Pages**.
2. Dans **Build and deployment**, choisir **Source: GitHub Actions**.
3. Dans **Custom domain**, saisir `parisauriol.com` puis enregistrer.
4. Après validation DNS, activer **Enforce HTTPS**.

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
