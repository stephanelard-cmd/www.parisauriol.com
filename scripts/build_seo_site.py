#!/usr/bin/env python3
from __future__ import annotations

import copy
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://parisauriol.com"
TODAY = date.today().isoformat()
TRANSLATIONS_FILE = ROOT / "assets" / "translations.json"
PHOTO_MANIFEST = ROOT / "assets" / "photos" / "manifest.json"
REPORT_FILE = ROOT / "data" / "seo-translation-report.json"
SEO_MANIFEST_FILE = ROOT / "data" / "seo-manifest.json"

LANGUAGES: dict[str, dict[str, str]] = {
    "fr": {"locale": "fr_FR", "ietf": "fr-FR", "name": "Français", "prefix": ""},
    "en": {"locale": "en_GB", "ietf": "en-GB", "name": "English", "prefix": "en"},
    "de": {"locale": "de_DE", "ietf": "de-DE", "name": "Deutsch", "prefix": "de"},
    "es": {"locale": "es_ES", "ietf": "es-ES", "name": "Español", "prefix": "es"},
}

PAGES: dict[str, dict[str, Any]] = {
    "index.html": {
        "index": True,
        "priority": "1.0",
        "changefreq": "weekly",
        "label": {"fr": "Accueil", "en": "Home", "de": "Startseite", "es": "Inicio"},
        "title": {
            "fr": "Appartement Paris 13 près Accor Arena et Austerlitz | Paris Auriol",
            "en": "Paris 13 Apartment near Accor Arena & Austerlitz | Paris Auriol",
            "de": "Wohnung Paris 13 nahe Accor Arena & Austerlitz | Paris Auriol",
            "es": "Apartamento París 13 cerca de Accor Arena y Austerlitz | Paris Auriol",
        },
        "description": {
            "fr": "Appartement rénové pour 3 voyageurs au 18 boulevard Vincent Auriol, à 50 m du métro Quai de la Gare, près d’Austerlitz, de la Seine et de l’Accor Arena.",
            "en": "Renovated apartment for 3 guests at 18 Boulevard Vincent Auriol, 50 m from Quai de la Gare metro, near Austerlitz, the Seine and Accor Arena.",
            "de": "Renovierte Wohnung für 3 Gäste am Boulevard Vincent Auriol 18, 50 m von der Metro Quai de la Gare, nahe Austerlitz, Seine und Accor Arena.",
            "es": "Apartamento renovado para 3 huéspedes en 18 Boulevard Vincent Auriol, a 50 m del metro Quai de la Gare, cerca de Austerlitz, el Sena y Accor Arena.",
        },
        "related": ["logement.html", "quartier.html", "faq.html"],
    },
    "logement.html": {
        "index": True,
        "priority": "0.9",
        "changefreq": "monthly",
        "label": {"fr": "Le logement", "en": "The apartment", "de": "Die Unterkunft", "es": "El alojamiento"},
        "title": {
            "fr": "Appartement meublé Paris 13 pour 3 personnes | Paris Auriol",
            "en": "Furnished Apartment in Paris 13 for 3 Guests | Paris Auriol",
            "de": "Möblierte Wohnung Paris 13 für 3 Gäste | Paris Auriol",
            "es": "Apartamento amueblado en París 13 para 3 huéspedes | Paris Auriol",
        },
        "description": {
            "fr": "Découvrez cet appartement entier rénové à Paris 13 : 1 chambre, 2 lits, cuisine équipée, Wi-Fi, ascenseur, arrivée autonome et animaux acceptés.",
            "en": "Discover this renovated entire apartment in Paris 13: 1 bedroom, 2 beds, equipped kitchen, Wi-Fi, lift, self check-in and pets allowed.",
            "de": "Renovierte ganze Wohnung in Paris 13: 1 Schlafzimmer, 2 Betten, ausgestattete Küche, WLAN, Aufzug, eigenständiger Check-in und Haustiere erlaubt.",
            "es": "Apartamento entero renovado en París 13: 1 dormitorio, 2 camas, cocina equipada, Wi-Fi, ascensor, llegada autónoma y mascotas admitidas.",
        },
        "related": ["photos.html", "disponibilites.html", "sejour.html"],
    },
    "photos.html": {
        "index": True,
        "priority": "0.8",
        "changefreq": "monthly",
        "label": {"fr": "Photos", "en": "Photos", "de": "Fotos", "es": "Fotos"},
        "title": {
            "fr": "Photos de l’appartement Paris 13 | Paris Auriol",
            "en": "Photos of the Paris 13 Apartment | Paris Auriol",
            "de": "Fotos der Wohnung in Paris 13 | Paris Auriol",
            "es": "Fotos del apartamento en París 13 | Paris Auriol",
        },
        "description": {
            "fr": "Consultez les photos réelles du salon, de la chambre, de la cuisine, de la salle de bains, de l’immeuble et de la vue de l’appartement Paris Auriol.",
            "en": "View genuine photos of the living room, bedroom, kitchen, bathroom, building and city view of the Paris Auriol apartment.",
            "de": "Originalfotos von Wohnzimmer, Schlafzimmer, Küche, Bad, Gebäude und Aussicht der Wohnung Paris Auriol.",
            "es": "Vea fotografías reales del salón, dormitorio, cocina, baño, edificio y vistas del apartamento Paris Auriol.",
        },
        "related": ["logement.html", "disponibilites.html", "quartier.html"],
    },
    "disponibilites.html": {
        "index": True,
        "priority": "0.9",
        "changefreq": "daily",
        "label": {"fr": "Disponibilités", "en": "Availability", "de": "Verfügbarkeit", "es": "Disponibilidad"},
        "title": {
            "fr": "Disponibilités appartement Paris 13 | Paris Auriol",
            "en": "Paris 13 Apartment Availability | Paris Auriol",
            "de": "Verfügbarkeit Wohnung Paris 13 | Paris Auriol",
            "es": "Disponibilidad apartamento París 13 | Paris Auriol",
        },
        "description": {
            "fr": "Consultez le calendrier consolidé Airbnb et Booking de l’appartement Paris Auriol, puis réservez selon les tarifs et conditions de la plateforme choisie.",
            "en": "Check the combined Airbnb and Booking calendar for the Paris Auriol apartment, then book with the rates and conditions shown by your chosen platform.",
            "de": "Prüfen Sie den zusammengeführten Airbnb- und Booking-Kalender der Wohnung Paris Auriol und buchen Sie zu den Bedingungen der gewählten Plattform.",
            "es": "Consulte el calendario combinado de Airbnb y Booking del apartamento Paris Auriol y reserve con las condiciones de la plataforma elegida.",
        },
        "related": ["logement.html", "sejour.html", "faq.html"],
    },
    "quartier.html": {
        "index": True,
        "priority": "0.9",
        "changefreq": "monthly",
        "label": {"fr": "Quartier et accès", "en": "Area and access", "de": "Umgebung und Anreise", "es": "Barrio y acceso"},
        "title": {
            "fr": "Appartement près Accor Arena, Austerlitz et BnF | Accès",
            "en": "Apartment near Accor Arena, Austerlitz and BnF | Access",
            "de": "Wohnung nahe Accor Arena, Austerlitz und BnF | Anreise",
            "es": "Apartamento cerca de Accor Arena, Austerlitz y BnF | Acceso",
        },
        "description": {
            "fr": "Accès au 18 boulevard Vincent Auriol : métro Quai de la Gare à 50 m, gare d’Austerlitz, Accor Arena, BnF, Bercy et quais de Seine à proximité.",
            "en": "Access to 18 Boulevard Vincent Auriol: Quai de la Gare metro 50 m away, with Austerlitz station, Accor Arena, BnF, Bercy and the Seine nearby.",
            "de": "Anreise zum Boulevard Vincent Auriol 18: Metro Quai de la Gare 50 m entfernt; Austerlitz, Accor Arena, BnF, Bercy und Seine in der Nähe.",
            "es": "Acceso a 18 Boulevard Vincent Auriol: metro Quai de la Gare a 50 m y cerca de Austerlitz, Accor Arena, BnF, Bercy y el Sena.",
        },
        "related": ["decouvrir.html", "agenda.html", "disponibilites.html"],
    },
    "decouvrir.html": {
        "index": True,
        "priority": "0.8",
        "changefreq": "monthly",
        "label": {"fr": "Guide local", "en": "Local guide", "de": "Reiseführer", "es": "Guía local"},
        "title": {
            "fr": "Que faire autour d’Austerlitz et Bercy | Guide Paris 13",
            "en": "Things to Do around Austerlitz and Bercy | Paris 13 Guide",
            "de": "Aktivitäten rund um Austerlitz und Bercy | Paris-13-Guide",
            "es": "Qué hacer cerca de Austerlitz y Bercy | Guía París 13",
        },
        "description": {
            "fr": "Guide pratique autour de Paris Auriol : Jardin des Plantes, BnF, Accor Arena, quais de Seine, street art du 13e, cinéma, restaurants et promenades.",
            "en": "Practical guide around Paris Auriol: Jardin des Plantes, BnF, Accor Arena, Seine walks, 13th-arrondissement street art, cinema and restaurants.",
            "de": "Praktischer Guide rund um Paris Auriol: Jardin des Plantes, BnF, Accor Arena, Seine-Ufer, Street Art, Kino, Restaurants und Spaziergänge.",
            "es": "Guía práctica cerca de Paris Auriol: Jardin des Plantes, BnF, Accor Arena, paseos por el Sena, arte urbano, cine y restaurantes.",
        },
        "related": ["quartier.html", "agenda.html", "faq.html"],
    },
    "agenda.html": {
        "index": True,
        "priority": "0.7",
        "changefreq": "daily",
        "label": {"fr": "Agenda", "en": "Events", "de": "Veranstaltungen", "es": "Agenda"},
        "title": {
            "fr": "Agenda Paris 13 et Accor Arena | Événements à proximité",
            "en": "Paris 13 and Accor Arena Events | What’s On Nearby",
            "de": "Veranstaltungen Paris 13 und Accor Arena | In der Nähe",
            "es": "Agenda París 13 y Accor Arena | Eventos cercanos",
        },
        "description": {
            "fr": "Retrouvez les événements, expositions, concerts et activités à venir dans le 13e arrondissement et autour de l’Accor Arena, via l’Open Data de Paris.",
            "en": "Discover upcoming events, exhibitions, concerts and activities in Paris’s 13th arrondissement and around Accor Arena, from official Paris Open Data.",
            "de": "Kommende Veranstaltungen, Ausstellungen, Konzerte und Aktivitäten im 13. Arrondissement und rund um die Accor Arena aus offiziellen Pariser Open Data.",
            "es": "Descubra próximos eventos, exposiciones, conciertos y actividades en el distrito 13 y alrededor de Accor Arena, con datos oficiales de París.",
        },
        "related": ["decouvrir.html", "quartier.html", "disponibilites.html"],
    },
    "sejour.html": {
        "index": True,
        "priority": "0.7",
        "changefreq": "monthly",
        "label": {"fr": "Règles du séjour", "en": "House rules", "de": "Hausregeln", "es": "Normas de la estancia"},
        "title": {
            "fr": "Règles et informations séjour | Appartement Paris 13",
            "en": "House Rules and Stay Information | Paris 13 Apartment",
            "de": "Hausregeln und Aufenthaltsinfos | Wohnung Paris 13",
            "es": "Normas e información de estancia | Apartamento París 13",
        },
        "description": {
            "fr": "Horaires d’arrivée et de départ, calme, tabac, fêtes, animaux, capacité et conditions de réservation de l’appartement Paris Auriol à Paris 13.",
            "en": "Check-in and check-out times, quiet hours, smoking, parties, pets, occupancy and booking conditions for the Paris Auriol apartment.",
            "de": "Check-in, Check-out, Ruhezeiten, Rauchen, Partys, Haustiere, Belegung und Buchungsbedingungen der Wohnung Paris Auriol.",
            "es": "Horarios de llegada y salida, silencio, tabaco, fiestas, mascotas, ocupación y condiciones de reserva del apartamento Paris Auriol.",
        },
        "related": ["faq.html", "disponibilites.html", "logement.html"],
    },
    "faq.html": {
        "index": True,
        "priority": "0.8",
        "changefreq": "monthly",
        "label": {"fr": "Questions fréquentes", "en": "Frequently asked questions", "de": "Häufige Fragen", "es": "Preguntas frecuentes"},
        "title": {
            "fr": "FAQ appartement Paris 13 près Accor Arena | Paris Auriol",
            "en": "Paris 13 Apartment FAQ near Accor Arena | Paris Auriol",
            "de": "FAQ Wohnung Paris 13 nahe Accor Arena | Paris Auriol",
            "es": "FAQ apartamento París 13 cerca de Accor Arena | Paris Auriol",
        },
        "description": {
            "fr": "Réponses sur l’emplacement, le métro, l’Accor Arena, la capacité, l’arrivée autonome, les horaires, le Wi-Fi, les animaux et la réservation.",
            "en": "Answers about the location, metro, Accor Arena, occupancy, self check-in, times, Wi-Fi, pets and booking the Paris Auriol apartment.",
            "de": "Antworten zu Lage, Metro, Accor Arena, Belegung, eigenständigem Check-in, Zeiten, WLAN, Haustieren und Buchung der Wohnung Paris Auriol.",
            "es": "Respuestas sobre ubicación, metro, Accor Arena, capacidad, llegada autónoma, horarios, Wi-Fi, mascotas y reserva del apartamento Paris Auriol.",
        },
        "related": ["logement.html", "quartier.html", "disponibilites.html"],
    },
    "mentions-legales.html": {
        "index": False,
        "priority": "0.2",
        "changefreq": "yearly",
        "label": {"fr": "Mentions légales", "en": "Legal notice", "de": "Impressum", "es": "Aviso legal"},
        "title": {"fr": "Mentions légales | Paris Auriol", "en": "Legal Notice | Paris Auriol", "de": "Impressum | Paris Auriol", "es": "Aviso legal | Paris Auriol"},
        "description": {"fr": "Mentions légales du site Paris Auriol.", "en": "Legal notice for the Paris Auriol website.", "de": "Impressum der Website Paris Auriol.", "es": "Aviso legal del sitio Paris Auriol."},
        "related": [],
    },
    "confidentialite.html": {
        "index": False,
        "priority": "0.2",
        "changefreq": "yearly",
        "label": {"fr": "Confidentialité", "en": "Privacy", "de": "Datenschutz", "es": "Privacidad"},
        "title": {"fr": "Confidentialité | Paris Auriol", "en": "Privacy | Paris Auriol", "de": "Datenschutz | Paris Auriol", "es": "Privacidad | Paris Auriol"},
        "description": {"fr": "Politique de confidentialité du site Paris Auriol.", "en": "Privacy policy for the Paris Auriol website.", "de": "Datenschutzrichtlinie der Website Paris Auriol.", "es": "Política de privacidad del sitio Paris Auriol."},
        "related": [],
    },
    "404.html": {
        "index": False,
        "priority": "0.0",
        "changefreq": "yearly",
        "label": {"fr": "Page introuvable", "en": "Page not found", "de": "Seite nicht gefunden", "es": "Página no encontrada"},
        "title": {"fr": "Page introuvable | Paris Auriol", "en": "Page Not Found | Paris Auriol", "de": "Seite nicht gefunden | Paris Auriol", "es": "Página no encontrada | Paris Auriol"},
        "description": {"fr": "Page introuvable.", "en": "Page not found.", "de": "Seite nicht gefunden.", "es": "Página no encontrada."},
        "related": [],
    },
}

RELATED_HEADING = {
    "fr": "Poursuivre la visite",
    "en": "Continue exploring",
    "de": "Weiter entdecken",
    "es": "Seguir explorando",
}

BREADCRUMB_LABEL = {
    "fr": "Fil d’Ariane",
    "en": "Breadcrumb",
    "de": "Brotkrümelnavigation",
    "es": "Migas de pan",
}

FAQ_INTRO = {
    "fr": ("Questions fréquentes", "Préparer votre séjour à Paris Auriol", "Les réponses essentielles sur l’appartement, son emplacement, les équipements et la réservation."),
    "en": ("Frequently asked questions", "Plan your stay at Paris Auriol", "Essential answers about the apartment, its location, facilities and booking."),
    "de": ("Häufige Fragen", "Planen Sie Ihren Aufenthalt bei Paris Auriol", "Die wichtigsten Antworten zu Wohnung, Lage, Ausstattung und Buchung."),
    "es": ("Preguntas frecuentes", "Prepare su estancia en Paris Auriol", "Respuestas esenciales sobre el apartamento, su ubicación, equipamientos y reserva."),
}

FAQ_DATA: dict[str, list[tuple[str, str]]] = {
    "fr": [
        ("Où se situe l’appartement ?", "L’appartement se trouve au 18 boulevard Vincent Auriol, 75013 Paris, entre la gare d’Austerlitz, la Seine, Bercy et la Bibliothèque nationale de France."),
        ("Le métro est-il proche ?", "Oui. La station Quai de la Gare, sur la ligne 6, se trouve à environ 50 mètres de l’adresse."),
        ("L’appartement est-il proche de l’Accor Arena ?", "Oui. L’Accor Arena se situe à environ 500 mètres, de l’autre côté de la Seine, et se rejoint facilement à pied."),
        ("Combien de voyageurs peuvent séjourner dans le logement ?", "Le logement accueille au maximum trois voyageurs. Il comprend une chambre, deux lits et une salle de bain."),
        ("Quels sont les horaires d’arrivée et de départ ?", "L’arrivée est prévue à partir de 15 h et le départ avant 11 h, sauf accord particulier indiqué sur la plateforme de réservation."),
        ("L’arrivée est-elle autonome ?", "Oui. L’accès est sécurisé et l’arrivée autonome. Les instructions détaillées sont transmises avant le séjour."),
        ("Le logement dispose-t-il du Wi-Fi et d’un espace de travail ?", "Oui. Le logement propose une connexion Wi-Fi, une télévision et un espace de travail dédié."),
        ("Les animaux sont-ils acceptés ?", "Oui. Les animaux sont admis ; un supplément peut s’appliquer selon les conditions affichées lors de la réservation."),
        ("Peut-on fumer ou organiser une fête ?", "Non. Le logement est non-fumeur, les fêtes et événements sont interdits et le calme est demandé entre 22 h et 9 h."),
        ("Comment vérifier les disponibilités et réserver ?", "Consultez le calendrier consolidé du site, puis confirmez le tarif, les conditions et la réservation sur Airbnb ou Booking.com."),
    ],
    "en": [
        ("Where is the apartment located?", "The apartment is at 18 Boulevard Vincent Auriol, 75013 Paris, between Austerlitz station, the Seine, Bercy and the National Library of France."),
        ("Is the metro nearby?", "Yes. Quai de la Gare station on line 6 is about 50 metres from the address."),
        ("Is the apartment close to Accor Arena?", "Yes. Accor Arena is about 500 metres away, across the Seine, and is easy to reach on foot."),
        ("How many guests can stay?", "The apartment accommodates a maximum of three guests. It has one bedroom, two beds and one bathroom."),
        ("What are the check-in and check-out times?", "Check-in is from 3 pm and check-out is before 11 am, unless a different arrangement is shown on the booking platform."),
        ("Is self check-in available?", "Yes. Access is secure and self check-in is available. Detailed instructions are sent before the stay."),
        ("Is Wi-Fi and a workspace available?", "Yes. The apartment provides Wi-Fi, a television and a dedicated workspace."),
        ("Are pets allowed?", "Yes. Pets are allowed; an extra charge may apply according to the conditions shown when booking."),
        ("Is smoking or holding a party allowed?", "No. The apartment is non-smoking, parties and events are prohibited, and quiet hours run from 10 pm to 9 am."),
        ("How do I check availability and book?", "Check the combined calendar on the website, then confirm the rate, conditions and booking on Airbnb or Booking.com."),
    ],
    "de": [
        ("Wo befindet sich die Wohnung?", "Die Wohnung liegt am Boulevard Vincent Auriol 18, 75013 Paris, zwischen dem Bahnhof Austerlitz, der Seine, Bercy und der Französischen Nationalbibliothek."),
        ("Ist die Metro in der Nähe?", "Ja. Die Station Quai de la Gare der Linie 6 liegt etwa 50 Meter von der Adresse entfernt."),
        ("Liegt die Wohnung nahe der Accor Arena?", "Ja. Die Accor Arena liegt etwa 500 Meter entfernt auf der anderen Seite der Seine und ist bequem zu Fuß erreichbar."),
        ("Wie viele Gäste können übernachten?", "Die Wohnung bietet Platz für maximal drei Gäste. Sie verfügt über ein Schlafzimmer, zwei Betten und ein Bad."),
        ("Welche Check-in- und Check-out-Zeiten gelten?", "Der Check-in ist ab 15 Uhr möglich, der Check-out erfolgt vor 11 Uhr, sofern auf der Buchungsplattform nichts anderes vereinbart ist."),
        ("Ist ein eigenständiger Check-in möglich?", "Ja. Der Zugang ist gesichert und der Check-in erfolgt eigenständig. Detaillierte Anweisungen werden vor dem Aufenthalt übermittelt."),
        ("Gibt es WLAN und einen Arbeitsplatz?", "Ja. Die Wohnung bietet WLAN, einen Fernseher und einen eigenen Arbeitsplatz."),
        ("Sind Haustiere erlaubt?", "Ja. Haustiere sind erlaubt; je nach den bei der Buchung angezeigten Bedingungen kann ein Aufpreis anfallen."),
        ("Darf man rauchen oder eine Party veranstalten?", "Nein. Die Wohnung ist eine Nichtraucherunterkunft, Partys und Veranstaltungen sind untersagt und von 22 bis 9 Uhr gilt Ruhezeit."),
        ("Wie prüfe ich die Verfügbarkeit und buche?", "Prüfen Sie den zusammengeführten Kalender auf der Website und bestätigen Sie anschließend Preis, Bedingungen und Buchung bei Airbnb oder Booking.com."),
    ],
    "es": [
        ("¿Dónde está situado el apartamento?", "El apartamento se encuentra en 18 Boulevard Vincent Auriol, 75013 París, entre la estación de Austerlitz, el Sena, Bercy y la Biblioteca Nacional de Francia."),
        ("¿Está cerca el metro?", "Sí. La estación Quai de la Gare de la línea 6 está a unos 50 metros de la dirección."),
        ("¿Está el apartamento cerca de Accor Arena?", "Sí. Accor Arena está a unos 500 metros, al otro lado del Sena, y se llega fácilmente a pie."),
        ("¿Cuántos huéspedes pueden alojarse?", "El apartamento admite un máximo de tres huéspedes. Dispone de un dormitorio, dos camas y un baño."),
        ("¿Cuáles son los horarios de llegada y salida?", "La llegada es a partir de las 15:00 y la salida antes de las 11:00, salvo que la plataforma de reserva indique otro acuerdo."),
        ("¿La llegada es autónoma?", "Sí. El acceso es seguro y la llegada es autónoma. Las instrucciones detalladas se envían antes de la estancia."),
        ("¿Hay Wi-Fi y zona de trabajo?", "Sí. El apartamento ofrece Wi-Fi, televisión y una zona de trabajo dedicada."),
        ("¿Se admiten mascotas?", "Sí. Se admiten mascotas; puede aplicarse un suplemento según las condiciones mostradas al reservar."),
        ("¿Se puede fumar u organizar una fiesta?", "No. El apartamento es para no fumadores, las fiestas y eventos están prohibidos y se exige silencio de 22:00 a 9:00."),
        ("¿Cómo consulto la disponibilidad y reservo?", "Consulte el calendario combinado del sitio y confirme después la tarifa, las condiciones y la reserva en Airbnb o Booking.com."),
    ],
}

HOME_SEO: dict[str, dict[str, Any]] = {
    "fr": {
        "eyebrow": "Séjour à Paris 13",
        "title": "Un emplacement pratique entre Austerlitz, Bercy et la BnF",
        "text": "Paris Auriol constitue un pied-à-terre central pour un concert à l’Accor Arena, un déplacement près de la gare d’Austerlitz, une visite de la BnF ou un séjour au bord de la Seine. Le métro Quai de la Gare facilite les déplacements dans Paris.",
        "facts": [("Métro à proximité", "Quai de la Gare, ligne 6, à environ 50 mètres."), ("Accor Arena", "À environ 500 mètres, de l’autre côté de la Seine."), ("Paris Rive Gauche", "Austerlitz, BnF, quais et Jardin des Plantes facilement accessibles.")],
    },
    "en": {
        "eyebrow": "Stay in Paris 13",
        "title": "A practical location between Austerlitz, Bercy and the BnF",
        "text": "Paris Auriol is a convenient base for a concert at Accor Arena, a trip near Austerlitz station, a visit to the BnF or a stay by the Seine. Quai de la Gare metro makes travelling around Paris easy.",
        "facts": [("Metro nearby", "Quai de la Gare, line 6, about 50 metres away."), ("Accor Arena", "About 500 metres away, across the Seine."), ("Paris Rive Gauche", "Easy access to Austerlitz, the BnF, the quays and Jardin des Plantes.")],
    },
    "de": {
        "eyebrow": "Aufenthalt in Paris 13",
        "title": "Praktische Lage zwischen Austerlitz, Bercy und der BnF",
        "text": "Paris Auriol ist ein guter Ausgangspunkt für ein Konzert in der Accor Arena, einen Termin am Bahnhof Austerlitz, einen Besuch der BnF oder einen Aufenthalt an der Seine. Die Metro Quai de la Gare erleichtert Wege durch Paris.",
        "facts": [("Metro in der Nähe", "Quai de la Gare, Linie 6, etwa 50 Meter entfernt."), ("Accor Arena", "Etwa 500 Meter entfernt, auf der anderen Seite der Seine."), ("Paris Rive Gauche", "Austerlitz, BnF, Uferwege und Jardin des Plantes gut erreichbar.")],
    },
    "es": {
        "eyebrow": "Estancia en París 13",
        "title": "Una ubicación práctica entre Austerlitz, Bercy y la BnF",
        "text": "Paris Auriol es una base cómoda para un concierto en Accor Arena, un desplazamiento cerca de la estación de Austerlitz, una visita a la BnF o una estancia junto al Sena. El metro Quai de la Gare facilita los trayectos por París.",
        "facts": [("Metro cercano", "Quai de la Gare, línea 6, a unos 50 metros."), ("Accor Arena", "A unos 500 metros, al otro lado del Sena."), ("Paris Rive Gauche", "Austerlitz, BnF, muelles y Jardin des Plantes fácilmente accesibles.")],
    },
}

PROPER_OR_LANGUAGE_NEUTRAL = {
    "PARIS AURIOL", "AUSTERLITZ · ARENA", "Paris Auriol Austerlitz Arena", "Paris Auriol",
    "Airbnb", "Booking.com", "Wi‑Fi", "Accor Arena", "BnF François‑Mitterrand", "MK2 Bibliothèque",
    "Jardin des Plantes", "Plat/form", "Le Quai", "Fior di Latte", "Google Maps", "OpenStreetMap",
    "18 boulevard Vincent Auriol · 75013 Paris", "Paris Rive Gauche · Austerlitz · Seine",
}


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def preserve_whitespace(source: str, replacement: str) -> str:
    leading = re.match(r"^\s*", source).group(0)
    trailing = re.search(r"\s*$", source).group(0)
    return f"{leading}{replacement}{trailing}"


def localized_url(page: str, language: str) -> str:
    filename = "" if page == "index.html" else page
    prefix = LANGUAGES[language]["prefix"]
    if prefix:
        return f"{BASE}/{prefix}/{filename}"
    return f"{BASE}/{filename}"


def localized_path(page: str, language: str) -> str:
    filename = "" if page == "index.html" else page
    prefix = LANGUAGES[language]["prefix"]
    if prefix:
        return f"/{prefix}/{filename}"
    return f"/{filename}"


def load_catalogue() -> dict[str, Any]:
    return json.loads(TRANSLATIONS_FILE.read_text(encoding="utf-8"))


def load_photos() -> list[dict[str, Any]]:
    manifest = json.loads(PHOTO_MANIFEST.read_text(encoding="utf-8"))
    photos = manifest.get("photos", [])
    if len(photos) < 8:
        raise RuntimeError("Le balisage VacationRental exige au moins huit photographies.")
    return photos[:8]


def clean_soup(soup: BeautifulSoup) -> None:
    for selector in (".breadcrumbs", "#seo-location", "#related-pages"):
        for node in soup.select(selector):
            node.decompose()
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        script.decompose()
    for link in soup.find_all("link", rel=lambda value: value and "alternate" in value):
        if link.get("hreflang"):
            link.decompose()
    for link in soup.find_all("link", rel=lambda value: value and "canonical" in value):
        link.decompose()
    for meta in soup.find_all("meta", attrs={"property": "og:locale:alternate"}):
        meta.decompose()
    for link in soup.find_all("link", href="/assets/seo.css"):
        link.decompose()


def translate_soup(
    soup: BeautifulSoup,
    language: str,
    catalogue: dict[str, Any],
    missing: set[str],
) -> None:
    if language == "fr":
        return
    messages = catalogue.get("messages", {})
    skip_tags = {"script", "style", "noscript", "textarea", "code"}
    for node in list(soup.find_all(string=True)):
        if not isinstance(node, NavigableString) or not node.parent or node.parent.name in skip_tags:
            continue
        source = str(node)
        key = normalize(source)
        if not key:
            continue
        translated = messages.get(key, {}).get(language)
        if translated:
            node.replace_with(preserve_whitespace(source, translated))
        elif key not in PROPER_OR_LANGUAGE_NEUTRAL and re.search(r"[A-Za-zÀ-ÿ]", key):
            if not re.fullmatch(r"[\d\s.,:/+€%·–—-]+", key):
                missing.add(key)

    for element in soup.find_all(True):
        for attribute in ("aria-label", "title", "placeholder"):
            source = element.get(attribute)
            if not source:
                continue
            key = normalize(source)
            translated = messages.get(key, {}).get(language)
            if translated:
                element[attribute] = translated

    for item in soup.select("[data-lightbox]"):
        caption = item.get(f"data-caption-{language}") or item.get("data-caption-fr")
        if caption:
            image = item.find("img")
            visible = item.select_one(".gallery-caption")
            if image:
                image["alt"] = caption
            if visible:
                visible.string = caption


def set_meta(soup: BeautifulSoup, key: str, value: str, content: str) -> Tag:
    tag = soup.head.find("meta", attrs={key: value})
    if not tag:
        tag = soup.new_tag("meta")
        tag[key] = value
        soup.head.append(tag)
    tag["content"] = content
    return tag


def add_head_link(soup: BeautifulSoup, rel: str, href: str, **attributes: str) -> Tag:
    tag = soup.new_tag("link", rel=rel, href=href)
    for key, value in attributes.items():
        tag[key.replace("_", "-")] = value
    soup.head.append(tag)
    return tag


def update_head(soup: BeautifulSoup, page: str, language: str, photos: list[dict[str, Any]]) -> None:
    config = PAGES[page]
    title = config["title"][language]
    description = config["description"][language]
    canonical = localized_url(page, language)
    image_url = f"{BASE}/{photos[0]['original']}"
    image_caption = photos[0].get("captions", {}).get(language) or photos[0].get("captions", {}).get("fr") or "Paris Auriol"

    if soup.title:
        soup.title.string = title
    else:
        title_tag = soup.new_tag("title")
        title_tag.string = title
        soup.head.append(title_tag)

    set_meta(soup, "name", "description", description)
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if config["index"] else "noindex,follow,max-image-preview:large"
    set_meta(soup, "name", "robots", robots)
    set_meta(soup, "name", "googlebot", robots)
    set_meta(soup, "property", "og:type", "website")
    set_meta(soup, "property", "og:locale", LANGUAGES[language]["locale"])
    set_meta(soup, "property", "og:site_name", "Paris Auriol")
    set_meta(soup, "property", "og:title", title)
    set_meta(soup, "property", "og:description", description)
    set_meta(soup, "property", "og:url", canonical)
    set_meta(soup, "property", "og:image", image_url)
    set_meta(soup, "property", "og:image:secure_url", image_url)
    set_meta(soup, "property", "og:image:width", "1280")
    set_meta(soup, "property", "og:image:height", "576")
    set_meta(soup, "property", "og:image:alt", image_caption)
    set_meta(soup, "name", "twitter:card", "summary_large_image")
    set_meta(soup, "name", "twitter:title", title)
    set_meta(soup, "name", "twitter:description", description)
    set_meta(soup, "name", "twitter:image", image_url)
    set_meta(soup, "name", "twitter:image:alt", image_caption)

    add_head_link(soup, "canonical", canonical)
    for code in LANGUAGES:
        add_head_link(soup, "alternate", localized_url(page, code), hreflang=code)
    add_head_link(soup, "alternate", localized_url(page, "fr"), hreflang="x-default")
    for code, language_config in LANGUAGES.items():
        if code != language:
            set_meta(soup, "property", "og:locale:alternate", language_config["locale"])

    style_link = soup.head.find("link", href=lambda value: value and value.endswith("assets/style.css"))
    seo_link = soup.new_tag("link", rel="stylesheet", href="/assets/seo.css")
    if style_link:
        style_link.insert_after(seo_link)
    else:
        soup.head.append(seo_link)


def build_faq_main(language: str) -> BeautifulSoup:
    eyebrow, heading, lead = FAQ_INTRO[language]
    items = []
    for question, answer in FAQ_DATA[language]:
        items.append(
            f'<article class="faq-item"><h2>{html.escape(question)}</h2><p>{html.escape(answer)}</p></article>'
        )
    markup = f"""
    <main>
      <section class="page-hero"><div class="container"><div class="eyebrow">{html.escape(eyebrow)}</div><h1>{html.escape(heading)}</h1><p class="lead">{html.escape(lead)}</p></div></section>
      <section class="section"><div class="container"><div class="faq-list">{''.join(items)}</div></div></section>
    </main>
    """
    return BeautifulSoup(markup, "html.parser")


def set_current_navigation(soup: BeautifulSoup, page: str) -> None:
    for link in soup.select("#main-menu a[aria-current]"):
        del link["aria-current"]
    target = "index.html" if page == "index.html" else page
    for link in soup.select("#main-menu a[href]"):
        href = urlsplit(link.get("href", "")).path
        if Path(href).name == target:
            link["aria-current"] = "page"


def add_faq_footer_link(soup: BeautifulSoup, language: str) -> None:
    footer = soup.find("footer")
    if not footer:
        return
    for existing in footer.find_all("a"):
        if Path(urlsplit(existing.get("href", "")).path).name == "faq.html":
            existing.decompose()
    stay_link = None
    for link in footer.find_all("a"):
        if Path(urlsplit(link.get("href", "")).path).name == "sejour.html":
            stay_link = link
            break
    if stay_link:
        faq_link = soup.new_tag("a", href=localized_path("faq.html", language))
        faq_link.string = PAGES["faq.html"]["label"][language]
        stay_link.insert_after(faq_link)


def add_breadcrumbs(soup: BeautifulSoup, page: str, language: str) -> None:
    if page == "index.html" or not soup.main:
        return
    home = PAGES["index.html"]["label"][language]
    current = PAGES[page]["label"][language]
    markup = f"""
    <nav class="breadcrumbs" aria-label="{html.escape(BREADCRUMB_LABEL[language])}">
      <div class="container"><ol>
        <li><a href="{localized_path('index.html', language)}">{html.escape(home)}</a></li>
        <li><span aria-current="page">{html.escape(current)}</span></li>
      </ol></div>
    </nav>
    """
    fragment = BeautifulSoup(markup, "html.parser").nav
    soup.main.insert(0, fragment)


def add_home_seo_section(soup: BeautifulSoup, language: str) -> None:
    if not soup.main:
        return
    content = HOME_SEO[language]
    facts = "".join(
        f'<article class="seo-fact"><b>{html.escape(title)}</b><p>{html.escape(text)}</p></article>'
        for title, text in content["facts"]
    )
    markup = f"""
    <section id="seo-location" class="section seo-location">
      <div class="container seo-summary">
        <div class="eyebrow">{html.escape(content['eyebrow'])}</div>
        <h2>{html.escape(content['title'])}</h2>
        <p class="lead">{html.escape(content['text'])}</p>
        <div class="seo-facts">{facts}</div>
      </div>
    </section>
    """
    section = BeautifulSoup(markup, "html.parser").section
    sections = soup.main.find_all("section", recursive=False)
    if sections:
        sections[-1].insert_before(section)
    else:
        soup.main.append(section)


def add_related_links(soup: BeautifulSoup, page: str, language: str) -> None:
    related = PAGES[page].get("related", [])
    if not related or not soup.main:
        return
    cards = []
    for related_page in related:
        label = PAGES[related_page]["label"][language]
        description = PAGES[related_page]["description"][language]
        cards.append(
            f'<a class="related-card" href="{localized_path(related_page, language)}"><b>{html.escape(label)}</b><span>{html.escape(description)}</span></a>'
        )
    markup = f"""
    <section id="related-pages" class="section seo-related alt"><div class="container">
      <div class="eyebrow">Paris Auriol</div><h2>{html.escape(RELATED_HEADING[language])}</h2>
      <div class="related-grid">{''.join(cards)}</div>
    </div></section>
    """
    soup.main.append(BeautifulSoup(markup, "html.parser").section)


def resource_to_root(value: str) -> str:
    if not value or value.startswith(("http://", "https://", "//", "data:", "mailto:", "tel:", "javascript:", "#")):
        return value
    clean = value.lstrip("./")
    if clean.startswith(("assets/", "data/", "site.webmanifest", "sitemap.xml", "robots.txt")):
        return "/" + clean
    return value


def rewrite_urls(soup: BeautifulSoup, language: str) -> None:
    for tag in soup.find_all(True):
        if tag.has_attr("src"):
            tag["src"] = resource_to_root(tag["src"])
        if tag.has_attr("poster"):
            tag["poster"] = resource_to_root(tag["poster"])
        if tag.has_attr("srcset"):
            entries = []
            for entry in tag["srcset"].split(","):
                parts = entry.strip().split()
                if parts:
                    parts[0] = resource_to_root(parts[0])
                    entries.append(" ".join(parts))
            tag["srcset"] = ", ".join(entries)
        if tag.has_attr("style"):
            tag["style"] = re.sub(r"url\((['\"]?)(?:\.\.?/)?assets/", r"url(\1/assets/", tag["style"])

    for link in soup.find_all(href=True):
        href = link.get("href", "")
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        parsed = urlsplit(href)
        if parsed.scheme and parsed.netloc and parsed.netloc != "parisauriol.com":
            continue
        path = parsed.path
        basename = Path(path).name
        if basename in PAGES:
            new_path = localized_path(basename, language)
        elif path in ("", "/") and not parsed.scheme:
            new_path = localized_path("index.html", language)
        else:
            new_path = resource_to_root(path)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.pop("lang", None)
        link["href"] = urlunsplit(("", "", new_path, urlencode(query), parsed.fragment))


def vacation_rental_node(language: str, photos: list[dict[str, Any]]) -> dict[str, Any]:
    image_urls = [f"{BASE}/{photo['original']}" for photo in photos]
    return {
        "@type": "VacationRental",
        "@id": f"{BASE}/#vacation-rental",
        "additionalType": "Apartment",
        "identifier": "7511306769833",
        "name": "Paris Auriol Austerlitz Arena",
        "url": localized_url("index.html", language),
        "description": PAGES["index.html"]["description"][language],
        "image": image_urls,
        "latitude": 48.83720,
        "longitude": 2.37220,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "18 boulevard Vincent Auriol",
            "postalCode": "75013",
            "addressLocality": "Paris",
            "addressRegion": "Île-de-France",
            "addressCountry": "FR",
        },
        "containsPlace": {
            "@type": "Accommodation",
            "additionalType": "EntirePlace",
            "occupancy": {"@type": "QuantitativeValue", "value": 3},
            "numberOfBedrooms": 1,
            "numberOfBathroomsTotal": 1,
            "numberOfRooms": 2,
            "petsAllowed": True,
            "smokingAllowed": False,
            "amenityFeature": [
                {"@type": "LocationFeatureSpecification", "name": "childFriendly", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "elevator", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "kitchen", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "petsAllowed", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "selfCheckinCheckout", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "smokingAllowed", "value": False},
                {"@type": "LocationFeatureSpecification", "name": "tv", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "wifi", "value": True},
                {"@type": "LocationFeatureSpecification", "name": "internetType", "value": "Free"},
                {"@type": "LocationFeatureSpecification", "name": "licenseNum", "value": "Paris: 7511306769833"},
            ],
        },
        "checkinTime": "15:00:00",
        "checkoutTime": "11:00:00",
        "sameAs": [
            "https://www.airbnb.fr/rooms/926532409861049580",
            "https://www.booking.com/hotel/fr/paris-auriol.fr.html",
        ],
    }


def structured_data(page: str, language: str, photos: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = localized_url(page, language)
    graph: list[dict[str, Any]] = []
    website_id = f"{BASE}/#website"
    page_id = f"{canonical}#webpage"
    rental_id = f"{BASE}/#vacation-rental"

    if page == "index.html" and language == "fr":
        graph.append({
            "@type": "WebSite",
            "@id": website_id,
            "url": f"{BASE}/",
            "name": "Paris Auriol",
            "alternateName": ["Paris Auriol Austerlitz Arena", "parisauriol.com"],
            "inLanguage": ["fr-FR", "en-GB", "de-DE", "es-ES"],
        })

    page_type: str | list[str] = "WebPage"
    if page in {"photos.html", "decouvrir.html", "agenda.html"}:
        page_type = "CollectionPage"
    if page == "faq.html":
        page_type = "FAQPage"

    webpage: dict[str, Any] = {
        "@type": page_type,
        "@id": page_id,
        "url": canonical,
        "name": PAGES[page]["title"][language],
        "description": PAGES[page]["description"][language],
        "inLanguage": LANGUAGES[language]["ietf"],
        "dateModified": TODAY,
        "isPartOf": {"@id": website_id},
        "about": {"@id": rental_id},
        "primaryImageOfPage": {
            "@type": "ImageObject",
            "url": f"{BASE}/{photos[0]['original']}",
            "caption": photos[0].get("captions", {}).get(language) or photos[0].get("captions", {}).get("fr"),
        },
    }

    if page != "index.html":
        breadcrumb_id = f"{canonical}#breadcrumb"
        webpage["breadcrumb"] = {"@id": breadcrumb_id}
        graph.append({
            "@type": "BreadcrumbList",
            "@id": breadcrumb_id,
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": PAGES["index.html"]["label"][language], "item": localized_url("index.html", language)},
                {"@type": "ListItem", "position": 2, "name": PAGES[page]["label"][language], "item": canonical},
            ],
        })

    if page == "faq.html":
        webpage["mainEntity"] = [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in FAQ_DATA[language]
        ]

    if page == "index.html":
        webpage["mainEntity"] = {"@id": rental_id}

    graph.insert(0, webpage)
    if page == "index.html":
        graph.append(vacation_rental_node(language, photos))
    return {"@context": "https://schema.org", "@graph": graph}


def add_structured_data(soup: BeautifulSoup, page: str, language: str, photos: list[dict[str, Any]]) -> None:
    script = soup.new_tag("script", type="application/ld+json")
    script.string = json.dumps(structured_data(page, language, photos), ensure_ascii=False, separators=(",", ":"))
    soup.head.append(script)


def output_path(page: str, language: str) -> Path:
    if language == "fr":
        return ROOT / page
    folder = ROOT / language
    folder.mkdir(parents=True, exist_ok=True)
    return folder / page


def process_page(
    source_html: str,
    page: str,
    language: str,
    catalogue: dict[str, Any],
    photos: list[dict[str, Any]],
    missing: set[str],
) -> str:
    soup = BeautifulSoup(source_html, "html.parser")
    clean_soup(soup)
    if page == "faq.html":
        faq_fragment = build_faq_main(language)
        if soup.main:
            soup.main.replace_with(faq_fragment.main)
        else:
            soup.body.append(faq_fragment.main)
    else:
        translate_soup(soup, language, catalogue, missing)

    soup.html["lang"] = language
    set_current_navigation(soup, page)
    add_faq_footer_link(soup, language)
    if page == "index.html":
        add_home_seo_section(soup, language)
    add_breadcrumbs(soup, page, language)
    add_related_links(soup, page, language)
    update_head(soup, page, language, photos)
    rewrite_urls(soup, language)
    add_structured_data(soup, page, language, photos)

    rendered = str(soup)
    if not rendered.lower().startswith("<!doctype"):
        rendered = "<!doctype html>\n" + rendered
    return rendered + "\n"


def build_sitemap(photos: list[dict[str, Any]]) -> None:
    sitemap_ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    xhtml_ns = "http://www.w3.org/1999/xhtml"
    image_ns = "http://www.google.com/schemas/sitemap-image/1.1"
    ET.register_namespace("", sitemap_ns)
    ET.register_namespace("xhtml", xhtml_ns)
    ET.register_namespace("image", image_ns)
    root = ET.Element(f"{{{sitemap_ns}}}urlset")

    for page, config in PAGES.items():
        if not config["index"]:
            continue
        for language in LANGUAGES:
            url = ET.SubElement(root, f"{{{sitemap_ns}}}url")
            ET.SubElement(url, f"{{{sitemap_ns}}}loc").text = localized_url(page, language)
            ET.SubElement(url, f"{{{sitemap_ns}}}lastmod").text = TODAY
            ET.SubElement(url, f"{{{sitemap_ns}}}changefreq").text = config["changefreq"]
            ET.SubElement(url, f"{{{sitemap_ns}}}priority").text = config["priority"]
            for alternate_language in LANGUAGES:
                ET.SubElement(url, f"{{{xhtml_ns}}}link", {
                    "rel": "alternate",
                    "hreflang": alternate_language,
                    "href": localized_url(page, alternate_language),
                })
            ET.SubElement(url, f"{{{xhtml_ns}}}link", {
                "rel": "alternate",
                "hreflang": "x-default",
                "href": localized_url(page, "fr"),
            })
            if page in {"index.html", "logement.html", "photos.html"}:
                for photo in photos:
                    image = ET.SubElement(url, f"{{{image_ns}}}image")
                    ET.SubElement(image, f"{{{image_ns}}}loc").text = f"{BASE}/{photo['original']}"
                    caption = photo.get("captions", {}).get(language) or photo.get("captions", {}).get("fr") or "Paris Auriol"
                    ET.SubElement(image, f"{{{image_ns}}}caption").text = caption
                    ET.SubElement(image, f"{{{image_ns}}}title").text = f"Paris Auriol — {caption}"

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def write_robots() -> None:
    content = """User-agent: *
Allow: /
Disallow: /scripts/
Disallow: /package/
Disallow: /data/
Disallow: /README.md

Sitemap: https://parisauriol.com/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(content, encoding="utf-8")


def validate_outputs(photos: list[dict[str, Any]]) -> dict[str, Any]:
    titles: dict[str, set[str]] = {language: set() for language in LANGUAGES}
    indexed_url_count = 0
    for page, config in PAGES.items():
        for language in LANGUAGES:
            path = output_path(page, language)
            if not path.exists():
                raise RuntimeError(f"Page manquante : {path.relative_to(ROOT)}")
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            expected_canonical = localized_url(page, language)
            canonical = soup.find("link", rel="canonical")
            if not canonical or canonical.get("href") != expected_canonical:
                raise RuntimeError(f"Canonical incorrect : {path.relative_to(ROOT)}")
            alternates = soup.find_all("link", rel="alternate", hreflang=True)
            if len(alternates) != len(LANGUAGES) + 1:
                raise RuntimeError(f"Hreflang incomplet : {path.relative_to(ROOT)}")
            robots = soup.find("meta", attrs={"name": "robots"})
            if config["index"] and (not robots or "noindex" in robots.get("content", "")):
                raise RuntimeError(f"Page indexable marquée noindex : {path.relative_to(ROOT)}")
            if not config["index"] and (not robots or "noindex" not in robots.get("content", "")):
                raise RuntimeError(f"Page utilitaire sans noindex : {path.relative_to(ROOT)}")
            if soup.title:
                if soup.title.string in titles[language] and config["index"]:
                    raise RuntimeError(f"Titre dupliqué en {language} : {soup.title.string}")
                titles[language].add(soup.title.string or "")
            h1_count = len(soup.find_all("h1"))
            if page != "404.html" and h1_count != 1:
                raise RuntimeError(f"Nombre de H1 incorrect ({h1_count}) : {path.relative_to(ROOT)}")
            for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
                json.loads(script.string or "{}")
            if "?lang=" in path.read_text(encoding="utf-8"):
                raise RuntimeError(f"Ancienne URL linguistique détectée : {path.relative_to(ROOT)}")
            if config["index"]:
                indexed_url_count += 1

    home = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
    scripts = [json.loads(script.string or "{}") for script in home.find_all("script", attrs={"type": "application/ld+json"})]
    vacation_nodes = []
    for payload in scripts:
        for node in payload.get("@graph", []):
            if node.get("@type") == "VacationRental":
                vacation_nodes.append(node)
    if len(vacation_nodes) != 1:
        raise RuntimeError("Un unique VacationRental est attendu sur la page d’accueil.")
    rental = vacation_nodes[0]
    for required in ("containsPlace", "identifier", "image", "latitude", "longitude", "name"):
        if required not in rental:
            raise RuntimeError(f"VacationRental incomplet : {required}")
    if len(rental["image"]) < 8 or len(photos) < 8:
        raise RuntimeError("VacationRental doit contenir au moins huit images.")
    if rental["containsPlace"].get("occupancy", {}).get("value") != 3:
        raise RuntimeError("Occupation maximale incorrecte dans VacationRental.")

    sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
    sitemap_ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = sitemap.findall("sm:url", sitemap_ns)
    if len(sitemap_urls) != indexed_url_count:
        raise RuntimeError(f"Sitemap incomplet : {len(sitemap_urls)} URL(s), {indexed_url_count} attendues.")

    return {
        "generated_at": TODAY,
        "languages": list(LANGUAGES),
        "pages_per_language": len(PAGES),
        "indexable_urls": indexed_url_count,
        "sitemap_urls": len(sitemap_urls),
        "vacation_rental_images": len(rental["image"]),
        "status": "valid",
    }


def main() -> int:
    catalogue = load_catalogue()
    photos = load_photos()
    source_pages: dict[str, str] = {}
    for page in PAGES:
        if page == "faq.html":
            source_pages[page] = (ROOT / "sejour.html").read_text(encoding="utf-8")
        else:
            source_pages[page] = (ROOT / page).read_text(encoding="utf-8")

    missing_report: dict[str, list[str]] = {}
    for language in LANGUAGES:
        missing: set[str] = set()
        for page, source_html in source_pages.items():
            rendered = process_page(source_html, page, language, catalogue, photos, missing)
            target = output_path(page, language)
            target.write_text(rendered, encoding="utf-8")
        missing_report[language] = sorted(missing)

    build_sitemap(photos)
    write_robots()
    report = validate_outputs(photos)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(missing_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SEO_MANIFEST_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for language, items in missing_report.items():
        if language == "fr":
            continue
        print(f"{language}: {len(items)} texte(s) français sans correspondance explicite")
        for item in items[:40]:
            print(f"  - {item}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
