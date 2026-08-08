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

# Neubau- und Immobilienprojekte — ausschließlich Frankfurt am Main. Bewusst
# auf Vorhaben für Privatkunden ausgerichtet; der Prompt in main.py wirft
# Büro-, Logistik- und Investorenmeldungen wieder raus. SkylineAtlas verfolgt
# Frankfurter Bauprojekte von der Planung bis zur Fertigstellung und ist die
# einzige echte Fachquelle, die ausschließlich über diese Stadt schreibt.
#
# Kein überregionaler Fachdienst mehr: immobilienmanager stand hier und lieferte
# Logistikhallen in Köln, ESG-Übernahmen und Bilanzen von Projektentwicklern.
# Der Prompt verwarf davon zuverlässig alles, aber der Feed belegte mit seinem
# per_feed-Limit von 6 vorher zwei Drittel des Kandidatenbudgets der Rubrik.
IMMOBILIEN_FEEDS = [
    ("SkylineAtlas", "https://skylineatlas.de/feed/"),
    ("Neubau Frankfurt", _GN.format("Frankfurt+Neubau+Wohnungen")),
    ("Neubauprojekte", _GN.format("Frankfurt+Neubauprojekt")),
    ("Wohnquartiere", _GN.format("Frankfurt+Wohnquartier+OR+Wohnbauprojekt")),
    ("Hochhausbau", _GN.format("Frankfurt+Hochhaus+Bauprojekt")),
    ("Wohnungsmarkt", _GN.format("Frankfurt+Immobilienmarkt+Wohnung+kaufen")),
    ("Eigentumswohnungen", _GN.format("Frankfurt+Eigentumswohnung+Preise")),
    ("Mietwohnungen", _GN.format("Frankfurt+Mietwohnungen+Vermietungsstart")),
]

# Konzerte, Kino, Comedy, Bühne — deutschlandweit, aber nur die großen
# internationalen Namen. Die Rubrik ist die einzige, die Frankfurt verlässt:
# Wer für Rosalía nach Köln oder für ein K-Pop-Konzert nach Berlin fährt, muss
# den Vorverkaufstermin trotzdem rechtzeitig sehen. Welche Namen groß genug
# sind, entscheidet der Prompt in main.py, nicht diese Liste.
#
# Die großen Arenen einzeln abzufragen bringt mehr als eine allgemeine Suche:
# Ankündigungen nennen fast immer den Spielort, und so tauchen auch Auftritte
# auf, die kein Medium als Nachricht behandelt. Frankfurter Spielorte stehen
# weiter vorn — die Stadt bleibt der Wohnort des Lesers.
EVENT_FEEDS = [
    ("Tourneen Deutschland",
     _GN.format("Welttournee+OR+Tournee+Deutschland+Konzert+angekuendigt")),
    ("Vorverkaufsstart",
     _GN.format("Konzert+Deutschland+Tickets+Vorverkauf+startet")),
    ("K-Pop", _GN.format("K-Pop+Konzert+Deutschland+OR+Europa+Tour")),
    ("Asiatische Stars",
     _GN.format("Japan+OR+Korea+Star+Konzert+Deutschland+Tour")),
    ("US-Stars", _GN.format("US-Star+OR+Superstar+Konzert+Deutschland+Arena")),
    ("Grosse Arenen",
     _GN.format("Lanxess+Arena+OR+Uber+Arena+OR+Barclays+Arena+Konzert")),
    ("Festhalle Frankfurt", _GN.format("Festhalle+Frankfurt+Konzert")),
    ("Stadionkonzerte",
     _GN.format("Stadionkonzert+Deutschland+OR+Deutsche+Bank+Park+Konzert")),
    ("US-Comedians",
     _GN.format("US-Comedian+OR+Stand-up+Comedy+Deutschland+Tour")),
    ("Comedy Frankfurt", _GN.format("Comedy+OR+Kabarett+Frankfurt")),
    ("Kinostarts", _GN.format("Kinostart+Deutschland+Blockbuster")),
    ("Kino Frankfurt", _GN.format("Kino+Frankfurt+Filmstart")),
]

# Sport — internationale Damenturniere in Tennis und Volleyball, und zwar nur
# solche in Deutschland. Der Zweck der Rubrik ist Ticketkauf, nicht
# Sportberichterstattung: Termin, Austragungsort und Vorverkaufsstart zählen,
# Ergebnisse und Tabellen nicht (das trennt der Prompt in main.py).
#
# Deutschland allein ist ein schmales Feld — im Tennis im Wesentlichen
# Stuttgart, Berlin und Bad Homburg, dazu Volleyball-Bundesliga, Pokalfinale
# und Länderspiele. Die Rubrik bleibt deshalb an vielen Tagen leer und liest
# sich dann als "Nichts in diesem Zeitraum". Ihr Zeitfenster in main.py ist
# mit 14 Tagen das breiteste, damit eine Ankündigung nicht durchrutscht.
SPORT_FEEDS = [
    ("WTA Deutschland", _GN.format("WTA+Turnier+Deutschland+Damen+Tennis")),
    ("Stuttgart & Berlin",
     _GN.format("Porsche+Tennis+Grand+Prix+OR+WTA+Berlin+Tickets")),
    ("Bad Homburg", _GN.format("Bad+Homburg+Open+Tennis+Damen")),
    ("Tennis-Tickets",
     _GN.format("Damen+Tennis+Turnier+Deutschland+Tickets+Vorverkauf")),
    # "Spielplan" stand hier einmal als Suchwort und zog fast nur automatisch
    # erzeugte Tabellen- und Ergebnisseiten an ("TV Dingolfing: Spielplan &
    # Ergebnisse 2. Bundesliga Süd"). Die sind keine Nachricht und für den
    # Kartenkauf wertlos. Gesucht wird deshalb nach Karten und Terminen.
    ("Volleyball Damen",
     _GN.format("Volleyball+Bundesliga+Frauen+Tickets+OR+Heimspiel")),
    ("Volleyball national",
     _GN.format("Volleyball+Nationalmannschaft+Frauen+Deutschland+Laenderspiel")),
    ("Volleyball-Turniere",
     _GN.format("Volleyball+Frauen+Turnier+in+Deutschland+Termin")),
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

# Frankfurt und seine Infrastruktur — alles, was den Alltag in der Stadt
# betrifft. Ausschließlich Frankfurt. Hier stehen echte Redaktionen statt
# Suchfeeds, weil es für Lokalnachrichten gute eigene Feeds gibt.
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
    ("Nahverkehr", _GN.format("Frankfurt+S-Bahn+OR+U-Bahn+Sperrung+OR+Ausbau")),
    ("Infrastruktur", _GN.format("Frankfurt+Bruecke+OR+Strassenbau+OR+Sanierung")),
    ("Museen & Ausstellungen", _GN.format("Frankfurt+Museum+Ausstellung")),
    ("Gastronomie", _GN.format("Frankfurt+am+Main+Restaurant+Eroeffnung")),
]

# Zuordnung Rubrik -> Feeds. Die Schlüssel müssen exakt denen in SECTIONS
# (render.py) entsprechen; main.py baut die Rubriken aus diesem Verzeichnis.
FEEDS = {
    "immobilien": IMMOBILIEN_FEEDS,
    "events": EVENT_FEEDS,
    "sport": SPORT_FEEDS,
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
