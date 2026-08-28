# État de publication de parisauriol.com

Diagnostic actualisé le **28 août 2026 à 13:35 UTC** depuis GitHub Actions.

## GitHub Pages

- GitHub Pages : activé.
- Construction et publication depuis `main` : réussies.
- Le site public est désormais servi par l’infrastructure GitHub Pages.

## DNS validés

- `parisauriol.com` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- `www.parisauriol.com` → `stephanelard-cmd.github.io.`
- La variante `www` se résout vers les mêmes adresses GitHub Pages.

## Réponses réseau observées

- `http://parisauriol.com/` : code 200, serveur GitHub.com, page d’accueil du site.
- `http://www.parisauriol.com/` : redirection 301 vers `http://parisauriol.com/`.
- `https://parisauriol.com/` : le certificat personnalisé n’est pas encore émis ; GitHub présente provisoirement son certificat générique `*.github.io`.

## Conclusion

La configuration OVH est correcte et propagée. Une nouvelle publication Pages est déclenchée par ce commit afin que GitHub finalise la validation du domaine et l’émission du certificat TLS pour `parisauriol.com` et `www.parisauriol.com`.
