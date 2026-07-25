"""Was der Digest liest, welches Modell ihn schreibt und wie lange er bleibt.

Nur einfache Werte — keine Imports, keine Logik, hier kann also nichts kaputt
gehen. Alles Übrige steht neben dem Code, der es benutzt: Zeitfenster, Limits
und Pfade in main.py, der redaktionelle Auftrag ebenfalls in main.py
(SYSTEM_PROMPT), Seitentitel, Rubriknamen und Farben in render.py.

MODEL und KEEP_DIGESTS lassen sich auch als GitHub-Repository-Variable gleichen
Namens setzen (Settings -> Secrets and variables -> Actions -> Variables), was
den Wert hier für einen Lauf überschreibt, ohne einen Commit zu brauchen.

Nicht hier: der API-Key. Der ist ein Repository-Secret namens OPENROUTER_API_KEY.
"""

# ---------------------------------------------------------------------------
# Modell
# ---------------------------------------------------------------------------

# OpenRouter-Slug inklusive Anbieter-Präfix — auf openrouter.ai/models prüfen,
# ein falscher Slug endet in einem 404. Kosten/Jahr bei dieser Last
# (~6K rein, ~3K raus, einmal täglich):
#   openai/gpt-5.6-luna            $1.20-1.70  Standard: am günstigsten und im
#                                              Artificial-Analysis-Index über
#                                              Haiku 4.5
#   anthropic/claude-haiku-4.5     $5.00-7.00  sehr guter deutscher Stil
#   openai/gpt-5.4-mini            $4.30-6.00  ebenso vertretbar
#   google/gemini-3-flash-preview  $2.90-4.10  günstigster der guten Klasse
#   openai/gpt-5                     ~$12.00   Spitzenpreis fürs Zusammenfassen
# Repository-Variable: MODEL
MODEL = "openai/gpt-5.6-luna"

# Nur ändern, um auf ein anderes OpenAI-kompatibles Gateway zu zeigen.
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ---------------------------------------------------------------------------
# Feeds
# ---------------------------------------------------------------------------
# Ein Eintrag pro Rubrik, die Schlüssel entsprechen SECTIONS in render.py.
# Jeder Feed ist ein Paar ("Anzeigename", "url"). Einen hinzuzufügen ist
# ungefährlich: es gibt keinen Stichwortfilter, das Modell entscheidet über
# Relevanz, und eine schwache Quelle wird schlicht nie ausgewählt.
#
# Viele Einträge sind Google-News-Suchfeeds. Das ist Absicht: für Frankfurter
# Nischenthemen (Neubauprojekte, K-Pop-Konzerte) gibt es keine eigenen Feeds,
# und Google News bündelt alle Lokalmedien, die einzeln keinen brauchbaren
# Feed anbieten. Aufbau der URL:
#   https://news.google.com/rss/search?q=SUCHE&hl=de&gl=DE&ceid=DE:de
# Suchbegriffe mit + verbinden, OR wird unterstützt. Bewusst ohne Umlaute,
# damit die URL in dieser Datei ASCII bleibt.
#
# Die Links solcher Feeds zeigen auf news.google.com und leiten weiter. main.py
# liest den echten Herausgeber aus dem Feed aus, damit unter jedem Beitrag
# "Weiterlesen bei FAZ" steht und nicht "bei news.google.com".

_GN = "https://news.google.com/rss/search?q={}&hl=de&gl=DE&ceid=DE:de"

# Neubau- und Immobilienprojekte. Bewusst auf Vorhaben für Privatkunden
# ausgerichtet — der Prompt in main.py wirft Büro-, Logistik- und
# Investorenmeldungen wieder raus. SkylineAtlas verfolgt Frankfurter
# Bauprojekte von der Planung bis zur Fertigstellung und ist die einzige
# echte Fachquelle, die ausschließlich über diese Stadt schreibt.
IMMOBILIEN_FEEDS = [
    ("SkylineAtlas", "https://skylineatlas.de/feed/"),
    ("immobilienmanager", "https://www.immobilienmanager.de/rss.xml"),
    ("Neubau Frankfurt", _GN.format("Frankfurt+Neubau+Wohnungen")),
    ("Neubauprojekte", _GN.format("Frankfurt+Neubauprojekt")),
    ("Wohnquartiere", _GN.format("Frankfurt+Wohnquartier+OR+Wohnbauprojekt")),
    ("Hochhausbau", _GN.format("Frankfurt+Hochhaus+Bauprojekt")),
    ("Wohnungsmarkt", _GN.format("Frankfurt+Immobilienmarkt+Wohnung+kaufen")),
    ("Eigentumswohnungen", _GN.format("Frankfurt+Eigentumswohnung+Preise")),
]

# Konzerte, Kino, Comedy, Bühne. Die Hallen einzeln abzufragen bringt mehr als
# eine allgemeine Suche: Ankündigungen nennen fast immer den Spielort, und so
# tauchen auch Auftritte auf, die kein Lokalmedium als Nachricht behandelt.
EVENT_FEEDS = [
    ("Festhalle", _GN.format("Festhalle+Frankfurt+Konzert")),
    ("Jahrhunderthalle & Batschkapp",
     _GN.format("Jahrhunderthalle+Frankfurt+OR+Batschkapp")),
    ("Deutsche Bank Park", _GN.format("Deutsche+Bank+Park+Konzert")),
    ("Konzerte", _GN.format("Konzert+Frankfurt+Tour")),
    ("Tickets & Vorverkauf", _GN.format("Frankfurt+Konzert+Tickets+Vorverkauf")),
    ("K-Pop", _GN.format("K-Pop+Konzert+Deutschland+Tour")),
    ("Comedy", _GN.format("Comedy+OR+Kabarett+Frankfurt")),
    ("Kino", _GN.format("Kino+Frankfurt+Filmstart")),
    ("Alte Oper", _GN.format("Alte+Oper+Frankfurt+Programm")),
    ("Musical & Show", _GN.format("Musical+OR+Show+Frankfurt+Premiere")),
]

# Messen und Stadtfeste. Publikumsmessen zählen mehr als reine Fachmessen —
# das entscheidet der Prompt, nicht die Feedauswahl. Die Feste-Suchen laufen
# saisonal: Dippemess und Wäldchestag liefern monatelang nichts und dann viel.
MESSE_FEEDS = [
    ("Messe Frankfurt", _GN.format("Messe+Frankfurt")),
    ("Fachmessen",
     _GN.format("Automechanika+OR+Ambiente+OR+Light+Building+Frankfurt")),
    ("Buchmesse", _GN.format("Frankfurter+Buchmesse")),
    ("Stadtfeste", _GN.format("Frankfurt+Fest+OR+Volksfest+OR+Weihnachtsmarkt")),
    ("Traditionsfeste",
     _GN.format("Museumsuferfest+OR+Dippemess+OR+Waeldchestag")),
    ("Saisonmaerkte", _GN.format("Frankfurt+Weihnachtsmarkt+OR+Sommerfest")),
]

# Alles, was den Alltag in der Stadt betrifft. Hier stehen echte Redaktionen
# statt Suchfeeds, weil es für Lokalnachrichten gute eigene Feeds gibt.
# hessenschau deckt ganz Hessen ab, liefert also viel, was nicht Frankfurt ist —
# der Prompt sortiert das aus, deshalb ist das Limit pro Feed in main.py wichtig.
STADT_FEEDS = [
    ("FAZ Frankfurt", "https://www.faz.net/rss/aktuell/rhein-main/frankfurt/"),
    ("Frankfurter Rundschau", "https://www.fr.de/frankfurt/rssfeed.rdf"),
    ("Frankfurter Neue Presse", "https://www.fnp.de/frankfurt/rssfeed.rdf"),
    ("hessenschau", "https://www.hessenschau.de/index.rss"),
    ("hessenschau Kultur", "https://www.hessenschau.de/kultur/index.rss"),
    ("Stadtpolitik", _GN.format("Frankfurt+am+Main+Stadt")),
    ("Verkehr & Baustellen", _GN.format("Frankfurt+Verkehr+OR+VGF+OR+Baustelle")),
    ("Museen & Ausstellungen", _GN.format("Frankfurt+Museum+Ausstellung")),
    ("Gastronomie", _GN.format("Frankfurt+am+Main+Restaurant+Eroeffnung")),
]

# Zuordnung Rubrik -> Feeds. Die Schlüssel müssen exakt denen in SECTIONS
# (render.py) entsprechen; main.py baut die Rubriken aus diesem Verzeichnis.
FEEDS = {
    "immobilien": IMMOBILIEN_FEEDS,
    "events": EVENT_FEEDS,
    "messen": MESSE_FEEDS,
    "stadt": STADT_FEEDS,
}

# ---------------------------------------------------------------------------
# Archiv
# ---------------------------------------------------------------------------

# Ausgaben, die auf der Platte und auf der Seite bleiben; ältere werden
# gelöscht. Muss über DEDUP_EDITIONS in main.py liegen — eine gelöschte Ausgabe
# kann eine Wiederholung nicht mehr verhindern. 0 behält alles für immer.
# Repository-Variable: KEEP_DIGESTS
KEEP_DIGESTS = 30
