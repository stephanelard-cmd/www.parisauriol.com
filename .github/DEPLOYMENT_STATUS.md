# État de publication de parisauriol.com

Diagnostic exécuté le **28 août 2026 à 13:20 UTC** depuis un runner GitHub Actions.

## GitHub Pages

- GitHub Pages : activé.
- Construction et déploiement depuis `main` : réussis.
- Domaine personnalisé déclaré par GitHub : `http://parisauriol.com/`.

## DNS observés

- `parisauriol.com` → `213.186.33.5`
- `www.parisauriol.com` → `213.186.33.5`
- `stephanelard-cmd.github.io` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`

## Réponses réseau observées

- `http://parisauriol.com/` : redirection OVH vers `http://www.parisauriol.com`.
- `http://www.parisauriol.com/` : page servie par OVH/OpenResty, pas le site GitHub Pages.
- `https://parisauriol.com/` : connexion impossible sur le port 443.
- `https://www.parisauriol.com/` : connexion impossible sur le port 443.
- L’adresse GitHub Pages du dépôt redirige correctement vers le domaine personnalisé.

## Conclusion

Le site est publié chez GitHub, mais la zone DNS OVH pointe encore vers l’adresse de redirection/parking OVH `213.186.33.5`. Les enregistrements DNS doivent être remplacés par ceux de GitHub Pages avant l’activation du certificat HTTPS.
