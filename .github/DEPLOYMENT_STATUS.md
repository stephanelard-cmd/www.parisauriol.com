# État de publication de parisauriol.com

Diagnostic actualisé le **28 août 2026 à 13:38 UTC** depuis GitHub Actions.

## GitHub Pages

- GitHub Pages : activé.
- Construction et publication depuis `main` : réussies.
- Nouvelle publication après propagation DNS : réussie.
- Le site public est servi par l’infrastructure GitHub Pages.

## DNS validés

- `parisauriol.com` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- `www.parisauriol.com` → `stephanelard-cmd.github.io.`
- La variante `www` se résout vers les mêmes adresses GitHub Pages.

## Réponses réseau observées

- `http://parisauriol.com/` : code 200, serveur GitHub.com, page d’accueil du site.
- `http://www.parisauriol.com/` : redirection 301 vers `http://parisauriol.com/`.
- `https://parisauriol.com/` : certificat personnalisé encore en cours d’émission ; GitHub présente provisoirement son certificat générique `*.github.io`.
- `https://www.parisauriol.com/` : même état provisoire.

## Conclusion

La configuration OVH est correcte, propagée et fonctionnelle. La publication GitHub Pages est réussie. Il ne reste que l’émission du certificat TLS par GitHub, puis l’activation de **Enforce HTTPS** dans `Settings → Pages`.
