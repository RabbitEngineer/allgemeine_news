"""Strukturierte Ausgaben in eine statische Website rendern.

Das Modell liefert strukturiertes JSON (siehe SYSTEM_PROMPT in main.py); die
gesamte Darstellung liegt hier. Weil das eine echte Website ist und kein
Newsletter, gelten keine E-Mail-Einschränkungen — modernes CSS, Custom
Properties, Dark Mode und responsives Layout sind erlaubt.

Ausgabebaum:
    site/index.html            die aktuelle Ausgabe
    site/archive/index.html    alle früheren Ausgaben, neueste zuerst
    site/archive/<datum>.html  eine Seite je Ausgabe
    site/feed.xml              Atom-Feed, damit ein Reader neue Ausgaben holt
"""

import html
import re
from datetime import datetime, timezone

# Browser-Tab, Seitenkopf und RSS-Feed. Reiner Text: "&" als "&" schreiben.
SITE_TITLE = "Allgemeine News"

# Rubriken in Seitenreihenfolge. Der Schlüssel muss dem entsprechen, den das
# Modell zurückgibt (siehe SYSTEM_PROMPT in main.py), einem Eintrag in FEEDS
# (configuration.py) und einer `.section.<key>`-Farbregel im CSS weiter unten.
# main.py liest seine Rubrikschlüssel von hier. Die Beschriftung ist frei.
#
# Die Rubriken haben absichtlich unterschiedliche Radien, und die Beschriftung
# sagt das: Wohnen, Feste und Infrastruktur sind an Frankfurt gebunden, weil
# sie den Alltag vor Ort betreffen; Konzerte und Sport decken Deutschland ab,
# weil man für einen Auftritt oder ein Turnier auch reist; Peking steht für
# sich, weil es um einen möglichen künftigen Arbeitsort geht. Welcher Radius
# für welche Rubrik gilt, steht als Regel im SYSTEM_PROMPT (main.py) — die
# Feedauswahl allein kann das nicht durchsetzen.
SECTIONS = [
    ("immobilien", "Neubau & Immobilien in Frankfurt"),
    ("events", "Konzerte, Kino & Comedy in Deutschland"),
    ("sport", "Sport"),
    ("messen", "Messen & Feste in Frankfurt"),
    ("stadt", "Frankfurt & Infrastruktur"),
    ("peking", "Peking & China"),
    ("jobs", "Neue Stellen in China"),
]

# Zeithorizonte als Reiter über den Rubriken. Jeder Beitrag bekommt vom Modell
# ein "horizon"-Feld mit einem dieser Schlüssel; in jedem Reiter stehen dann
# wieder alle sieben Rubriken, gefüllt mit den Beiträgen dieses Zeitraums.
# Der erste Eintrag ist der Rückfallwert für alles, was sich nicht einordnen
# lässt — er muss deshalb der Reiter für die Gegenwart sein.
# Ein neuer Horizont braucht zusätzlich einen Absatz im SYSTEM_PROMPT (main.py);
# das CSS erzeugt seine Regeln aus dieser Liste.
HORIZONS = [
    ("aktuell", "Aktuell"),
    ("wochen", "In den nächsten Wochen"),
    ("monate", "In den nächsten Monaten"),
]

# Das Etikett auf jedem Hauptbeitrag. Die Schlüssel sind exakt die Werte, die
# das Modell für "tag" verwenden darf — ein neuer braucht einen Eintrag in
# SYSTEM_PROMPT und ein --tag-<key>-bg/-fg-Paar im CSS unten, sonst fällt er
# auf das neutrale "news" zurück.
TAG_LABELS = {
    "neubau": "Neubau",
    "baustart": "Baustart",
    "verkauf": "Verkaufsstart",
    "fertig": "Bezugsfertig",
    "preise": "Preise",
    "konzert": "Konzert",
    "kino": "Kino",
    "comedy": "Comedy",
    "buehne": "Bühne",
    "tennis": "Tennis",
    "volleyball": "Volleyball",
    "jobs": "Arbeitsmarkt",
    "visum": "Visum",
    "stelle": "Stelle",
    "messe": "Messe",
    "fest": "Fest",
    "verkehr": "Verkehr",
    "news": "News",
}

# Für Datumsangaben ohne Locale-Abhängigkeit: GitHub-Runner laufen unter der
# C-Locale, %A und %B lieferten dort englische Namen.
WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag",
               "Samstag", "Sonntag"]
MONTHS_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
             "August", "September", "Oktober", "November", "Dezember"]


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def domain(url: str) -> str:
    if not url:
        return ""
    host = re.sub(r"^https?://", "", str(url)).split("/")[0]
    return re.sub(r"^www\.", "", host)


def attribution(entry: dict) -> str:
    """Wem der Beitrag zugeschrieben wird.

    main.py hängt an jeden Eintrag den echten Herausgeber aus dem Feed. Ohne
    das stünde bei Google-News-Treffern überall "news.google.com", weil deren
    Links über eine Weiterleitung laufen. Die Domain bleibt der Rückfallwert.
    """
    return str(entry.get("source") or "").strip() or domain(entry.get("url"))


def section_of(digest: dict, key: str, horizon: str | None = None) -> dict:
    """Eine Rubrik, wahlweise auf einen Zeithorizont eingeschränkt."""
    section = digest.get(key) if isinstance(digest.get(key), dict) else {}
    top = section.get("top") or []
    also = section.get("also") or []
    if horizon is not None:
        top = [i for i in top if horizon_of(i) == horizon]
        also = [b for b in also if horizon_of(b) == horizon]
    return {"top": top, "also": also}


def horizon_of(entry: dict) -> str:
    """Der Zeithorizont eines Beitrags, auf die bekannten Werte begrenzt.

    Der Rückfallwert deckt zwei Fälle ab: ein Modell, das das Feld weglässt oder
    einen unbekannten Wert liefert, und ältere gespeicherte Ausgaben aus der
    Zeit vor den Reitern. Beide landen unter "Aktuell", statt zu verschwinden.
    """
    value = str(entry.get("horizon") or "").strip().lower()
    return value if value in dict(HORIZONS) else HORIZONS[0][0]


def item_count(digest: dict, horizon: str | None = None) -> int:
    return sum(
        len(section_of(digest, k, horizon)["top"])
        + len(section_of(digest, k, horizon)["also"])
        for k, *_ in SECTIONS
    )


def read_time(digest: dict) -> int:
    words = sum(len(str(t).split()) for t in digest.get("tldr") or [])
    for key, *_ in SECTIONS:
        section = section_of(digest, key)
        for i in section["top"]:
            words += len(f"{i.get('title','')} {i.get('summary','')} {i.get('why','')}".split())
        words += sum(len(str(b.get("title", "")).split()) for b in section["also"])
    return max(1, round(words / 200 + 0.5))


def pretty_date(iso: str) -> str:
    try:
        day = datetime.strptime(iso, "%Y-%m-%d")
    except ValueError:
        return iso
    return (f"{WEEKDAYS_DE[day.weekday()]}, {day.day}. "
            f"{MONTHS_DE[day.month - 1]} {day.year}")


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

# Der Aufbau der Palette stammt von frankfurtflyer.de (WordPress-Theme
# MH Magazine Lite): ein rotes Leitmotiv, Anthrazit als Schriftfarbe,
# Seitengrund #f7f7f7, Linien #ebebeb. Das Layout ist unverändert — nur die
# Werte sind neu.
#
# Die Buntwerte sind gegenüber der Vorlage deutlich entsättigt: das Signalrot
# #e64946 war als Markenfarbe, als Rubrikfarbe UND als Reiterhintergrund im
# Einsatz und wurde dadurch zu laut. Farbe trägt hier nur noch die
# Rubrikzuordnung, und zwar in Bauteilen, die schmal sind — Trennlinie unter
# der Rubriküberschrift, 4px-Kante der Karte, Linkfarbe. Für großflächige
# Bauteile bleibt es bei Grau.
#
# Alle Rubrikfarben erreichen auf ihrem jeweiligen Grund mindestens 4.5:1, sie
# tragen nämlich Text (die Rubriküberschrift und die "Weiterlesen bei"-Zeile),
# nicht nur Ränder.
CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{
  --bg:#f7f7f7; --surface:#fff; --raised:#ebebeb;
  --ink:#2a2a2a; --muted:#555; --faint:#7c7c7c;
  --line:#ebebeb; --line-strong:#d3d3d3;
  --brand:#a8504d;
  --immobilien:#9e4a48; --events:#8a5273; --sport:#3f6b5e;
  --messen:#8a6a3d; --stadt:#4f4f4f; --peking:#4a5f85; --jobs:#6b5340;
  /* Reiterleiste nach dem Vorbild der Hauptnavigation von frankfurtflyer.de:
     anthrazitfarbener Balken, roter Unterstrich, aktiver Punkt rot hinterlegt.
     Das Aktiv-Rot ist eine Spur tiefer als die Markenfarbe, damit weiße
     Versalien darauf lesbar bleiben; der Unterschied ist mit bloßem Auge
     nicht auszumachen. */
  --tabbar:#2a2a2a; --tabink:#d8d8d8;
  --tab-active-bg:#8f4442; --tab-active-ink:#fff;
  --shadow:0 1px 2px rgba(0,0,0,.06),0 8px 24px rgba(0,0,0,.06);
  --tag-bg:#e8e8e8; --tag-fg:#4c4c4c;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#161616; --surface:#1f1f1f; --raised:#292929;
    --ink:#ececec; --muted:#b3b3b3; --faint:#8c8c8c;
    --line:#303030; --line-strong:#454545;
    --brand:#d1817f;
    --immobilien:#d1817f; --events:#c79ab4; --sport:#8fbdae;
    --messen:#c2a577; --stadt:#c8c8c8; --peking:#9db3d4; --jobs:#c4a893;
    /* Im Dunkelmodus trägt der aktive Reiter dunkle Schrift auf hellem Rot —
       weiß auf #d1817f wäre zu kontrastarm. */
    --tabbar:#262626; --tabink:#c0c0c0;
    --tab-active-bg:#d1817f; --tab-active-ink:#1a1a1a;
    --shadow:0 1px 2px rgba(0,0,0,.5),0 8px 24px rgba(0,0,0,.35);
    --tag-bg:#2c2c2c; --tag-fg:#b8b8b8;
  }
}

/* Alle Tags tragen dieselbe neutrale Plakette. Vorher hatte jedes der 13 Tags
   eine eigene Farbe — grün, bernstein, türkis, violett, blau —, was zusammen
   mit den sieben Rubrikfarben und dem Rot der Reiterleiste einen kompletten
   Farbkreis auf einer Seite ergab. Die Rubrik steht schon am Kartenrand und
   in der Rubriküberschrift; das Tag muss sie nicht ein drittes Mal codieren,
   sein Text sagt ohnehin, worum es geht.

   Die Paare bleiben einzeln bestehen, damit ein neues Tag weiterhin nur einen
   Eintrag in TAG_LABELS und eine Zeile hier braucht (und damit sich eine
   einzelne Rubrik wieder abheben ließe, falls das je gewollt ist). Weil beide
   Themes --tag-bg/--tag-fg auf :root setzen, folgt der Alias von selbst. */
:root{
  --tag-neubau-bg:var(--tag-bg);   --tag-neubau-fg:var(--tag-fg);
  --tag-baustart-bg:var(--tag-bg); --tag-baustart-fg:var(--tag-fg);
  --tag-verkauf-bg:var(--tag-bg);  --tag-verkauf-fg:var(--tag-fg);
  --tag-fertig-bg:var(--tag-bg);   --tag-fertig-fg:var(--tag-fg);
  --tag-preise-bg:var(--tag-bg);   --tag-preise-fg:var(--tag-fg);
  --tag-konzert-bg:var(--tag-bg);  --tag-konzert-fg:var(--tag-fg);
  --tag-kino-bg:var(--tag-bg);     --tag-kino-fg:var(--tag-fg);
  --tag-comedy-bg:var(--tag-bg);   --tag-comedy-fg:var(--tag-fg);
  --tag-buehne-bg:var(--tag-bg);   --tag-buehne-fg:var(--tag-fg);
  --tag-tennis-bg:var(--tag-bg);   --tag-tennis-fg:var(--tag-fg);
  --tag-volleyball-bg:var(--tag-bg); --tag-volleyball-fg:var(--tag-fg);
  --tag-jobs-bg:var(--tag-bg);     --tag-jobs-fg:var(--tag-fg);
  --tag-visum-bg:var(--tag-bg);    --tag-visum-fg:var(--tag-fg);
  --tag-stelle-bg:var(--tag-bg);   --tag-stelle-fg:var(--tag-fg);
  --tag-messe-bg:var(--tag-bg);    --tag-messe-fg:var(--tag-fg);
  --tag-fest-bg:var(--tag-bg);     --tag-fest-fg:var(--tag-fg);
  --tag-verkehr-bg:var(--tag-bg);  --tag-verkehr-fg:var(--tag-fg);
  --tag-news-bg:var(--tag-bg);     --tag-news-fg:var(--tag-fg);
}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;background:var(--bg);color:var(--ink);
  font:400 16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
.wrap{max-width:760px;margin:0 auto;padding:32px 20px 72px}
a{color:var(--brand)}
a:focus-visible,button:focus-visible{outline:2px solid var(--brand);outline-offset:2px;border-radius:3px}

.masthead{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:baseline;
  padding-bottom:18px;border-bottom:2px solid var(--line-strong);margin-bottom:28px}
.masthead h1{margin:0;font-size:1.5rem;line-height:1.2;letter-spacing:-.015em;text-wrap:balance}
.masthead h1 a{color:var(--ink);text-decoration:none}
.masthead nav{margin-left:auto;display:flex;gap:16px;font-size:.88rem}
.dateline{width:100%;color:var(--faint);font-size:.88rem;margin-top:-4px}
.dateline .dot{opacity:.5;padding:0 .45em}

.tldr{background:var(--raised);border-left:4px solid var(--brand);border-radius:8px;
  padding:16px 20px;margin:0 0 34px}
.tldr h2{margin:0 0 10px;font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--brand)}
.tldr ul{margin:0;padding-left:1.15em;display:flex;flex-direction:column;gap:7px}
.tldr li{font-size:1.02rem;line-height:1.55}

/* Reiter ohne JavaScript: drei Radiobuttons, deren :checked-Zustand per
   Geschwister-Selektor die zugehörige Beschriftung hervorhebt und das passende
   Panel einblendet. Die Regeln dafür stehen am Ende dieser Datei, aus HORIZONS
   erzeugt. Radiobuttons statt Klick-Handler heißt: die Pfeiltasten schalten die
   Reiter von Haus aus weiter, und die Seite bleibt eine reine Textdatei. */
.tabs{margin:0 0 34px}
.tabs>input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.tablist{display:flex;flex-wrap:wrap;background:var(--tabbar);
  border-bottom:4px solid var(--brand);border-radius:6px 6px 0 0;overflow:hidden}
.tablist label{flex:1 1 auto;text-align:center;padding:12px 14px;cursor:pointer;
  font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  line-height:1.3;color:var(--tabink);transition:background .12s}
.tablist label:hover{background:rgba(168,80,77,.30);color:#fff}
.tablist .n{display:inline-block;margin-left:.5em;opacity:.65;
  font-variant-numeric:tabular-nums}
.tabpanel{display:none;padding-top:26px}
.tabpanel .section:last-child{margin-bottom:0}

.section{margin:0 0 40px}
.section-head{display:flex;align-items:baseline;gap:12px;
  padding-bottom:9px;border-bottom:2px solid var(--accent);margin-bottom:18px}
.section-head h2{margin:0;font-size:.76rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.section-head .count{margin-left:auto;color:var(--faint);font-size:.8rem;font-variant-numeric:tabular-nums}
.section.immobilien{--accent:var(--immobilien)}
.section.events{--accent:var(--events)}
.section.sport{--accent:var(--sport)}
.section.messen{--accent:var(--messen)}
.section.stadt{--accent:var(--stadt)}
.section.peking{--accent:var(--peking)}
.section.jobs{--accent:var(--jobs)}

.cards{display:flex;flex-direction:column;gap:14px}
.card{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);
  border-radius:8px;padding:16px 18px;box-shadow:var(--shadow)}
.tag{display:inline-block;font-size:.66rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;padding:4px 9px;border-radius:4px;margin-bottom:9px}
.card h3{margin:0 0 7px;font-size:1.1rem;line-height:1.35;letter-spacing:-.005em;text-wrap:balance}
.card h3 a{color:var(--ink);text-decoration:none}
.card h3 a:hover{text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:3px}
.card .summary{margin:0;color:var(--muted);font-size:.95rem}
.why{margin-top:12px;padding-top:11px;border-top:1px solid var(--line)}
.why b{display:block;font-size:.68rem;font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;color:var(--accent);margin-bottom:3px}
.why span{color:var(--muted);font-size:.93rem}
.source{display:inline-block;margin-top:13px;font-size:.86rem;font-weight:600;
  color:var(--accent);text-decoration:none;border-bottom:1px solid currentColor;padding-bottom:1px}

.also{margin-top:18px}
.also h3{margin:0 0 8px;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--faint)}
.also ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:7px}
.also li{font-size:.92rem;color:var(--muted);padding-left:1.1em;position:relative}
.also li::before{content:"\\2022";position:absolute;left:0;color:var(--accent)}
.also a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--line-strong)}
.also a:hover{border-bottom-color:var(--accent)}
.also .src{color:var(--faint)}

.empty{color:var(--faint);font-style:italic;margin:0}

.archive-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px}
.archive-list li{border-bottom:1px solid var(--line)}
.archive-list a{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;
  padding:14px 4px;text-decoration:none;color:var(--ink)}
.archive-list a:hover{background:var(--surface)}
.archive-list .d{font-weight:600}
.archive-list .n{color:var(--faint);font-size:.85rem;font-variant-numeric:tabular-nums;margin-left:auto}
.archive-list .peek{width:100%;color:var(--muted);font-size:.9rem;line-height:1.5}

footer{margin-top:48px;padding-top:18px;border-top:1px solid var(--line);
  color:var(--faint);font-size:.84rem;display:flex;flex-wrap:wrap;gap:6px 14px}

@media (max-width:560px){
  .wrap{padding:24px 16px 56px}
  .masthead nav{margin-left:0;width:100%}
  .card{padding:14px 15px}
  /* Drei Beschriftungen dieser Länge passen nicht nebeneinander; gestapelt
     bleiben sie lesbar und behalten eine gut treffbare Fläche. */
  .tablist label{flex:1 1 100%;text-align:left;padding:11px 14px}
  .tablist .n{float:right;margin-left:0}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


def _horizon_css() -> str:
    """Je Zeithorizont die drei Regeln, die den Reiter ausmachen.

    Aus HORIZONS erzeugt statt von Hand geschrieben, damit ein zusätzlicher
    Reiter nicht daran scheitert, dass jemand eine der drei Zeilen vergisst.
    """
    rules = []
    for key, _label in HORIZONS:
        rules.append(
            f'#h-{key}:checked~.tablist label[for="h-{key}"]'
            f'{{background:var(--tab-active-bg);color:var(--tab-active-ink)}}'
        )
        rules.append(f"#h-{key}:checked~#p-{key}{{display:block}}")
        # Der Radiobutton selbst ist unsichtbar, der Fokusrahmen muss also auf
        # seiner Beschriftung erscheinen — sonst tastet man blind durch.
        rules.append(
            f'#h-{key}:focus-visible~.tablist label[for="h-{key}"]'
            f"{{outline:2px solid var(--brand);outline-offset:-4px}}"
        )
    return "\n".join(rules)


CSS += _horizon_css()


def _page(title: str, body: str, *, depth: int = 0) -> str:
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{title}</title>
<link rel="alternate" type="application/atom+xml" title="{esc(SITE_TITLE)}" href="{up}feed.xml">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>"""


def _masthead(date_iso: str, digest: dict, *, depth: int) -> str:
    up = "../" * depth
    count = item_count(digest)
    return f"""<header class="masthead">
  <h1><a href="{up}index.html">{esc(SITE_TITLE)}</a></h1>
  <nav><a href="{up}archive/index.html">Archiv</a><a href="{up}feed.xml">Feed</a></nav>
  <div class="dateline">{esc(pretty_date(date_iso))}<span class="dot">&middot;</span>{read_time(digest)} Min. Lesezeit<span class="dot">&middot;</span>{count} {'Beitrag' if count == 1 else 'Beiträge'}</div>
</header>"""


def _card(item: dict) -> str:
    tag = (item.get("tag") or "news").strip().lower()
    if tag not in TAG_LABELS:
        tag = "news"
    url, title = esc(item.get("url")), esc(item.get("title"))
    heading = f'<a href="{url}">{title}</a>' if url else title

    why = ""
    if item.get("why"):
        why = (f'<div class="why"><b>Warum das interessant ist</b>'
               f'<span>{esc(item["why"])}</span></div>')
    source = ""
    if url:
        source = (f'<a class="source" href="{url}">'
                  f'Weiterlesen bei {esc(attribution(item))} &rarr;</a>')

    return f"""<article class="card">
  <span class="tag" style="background:var(--tag-{tag}-bg);color:var(--tag-{tag}-fg)">{TAG_LABELS[tag]}</span>
  <h3>{heading}</h3>
  <p class="summary">{esc(item.get('summary'))}</p>
  {why}
  {source}
</article>"""


def _also(entries: list) -> str:
    if not entries:
        return ""
    rows = []
    for entry in entries:
        url, title = esc(entry.get("url")), esc(entry.get("title"))
        linked = f'<a class="alt" href="{url}">{title}</a>' if url else title
        # "summary" ist das aktuelle Feld; "note" nutzten ältere gespeicherte
        # Ausgaben, und jede Ausgabe wird bei jedem Build neu gerendert.
        line = esc(entry.get("summary") or entry.get("note"))
        body = f'<span class="alsum">{line}</span>' if line else ""
        more = (f'<a class="alsrc" href="{url}">Weiterlesen bei '
                f'{esc(attribution(entry))} &rarr;</a>') if url else ""
        rows.append(f"<li>{linked}{body}{more}</li>")
    return f'<div class="also"><h3>Außerdem notiert</h3><ul>{"".join(rows)}</ul></div>'


def _sections(digest: dict, horizon: str) -> str:
    out = []
    for key, label in SECTIONS:
        section = section_of(digest, key, horizon)
        count = len(section["top"]) + len(section["also"])
        if count:
            body = (f'<div class="cards">{"".join(_card(i) for i in section["top"])}</div>'
                    + _also(section["also"]))
        else:
            # Alle sieben Rubriken erscheinen in jedem Reiter, auch die leeren.
            # Eine Rubrik, die je nach Zeitraum verschwände, ließe den Leser
            # rätseln, ob es nichts gibt oder ob etwas kaputt ist.
            body = '<p class="empty">Nichts in diesem Zeitraum.</p>'
        # Der Rubrikschlüssel ist zugleich die CSS-Klasse für die Akzentfarbe.
        out.append(f"""<section class="section {esc(key)}">
  <div class="section-head"><h2>{esc(label)}</h2><span class="count">{count}</span></div>
  {body}
</section>""")
    return "".join(out)


def _tabs(digest: dict) -> str:
    """Die Reiterleiste samt der drei Panels darunter.

    Voreingestellt ist der erste Reiter, der überhaupt etwas enthält. Wäre es
    stur der erste, öffnete sich die Seite an einem Tag ohne aktuelle Termine
    auf einer leeren Ansicht, obwohl weiter hinten etwas steht.
    """
    counts = {key: item_count(digest, key) for key, _label in HORIZONS}
    active = next((key for key, _l in HORIZONS if counts[key]), HORIZONS[0][0])

    inputs, labels, panels = [], [], []
    for key, label in HORIZONS:
        checked = " checked" if key == active else ""
        inputs.append(
            f'<input type="radio" name="horizon" id="h-{esc(key)}"{checked}>'
        )
        labels.append(
            f'<label for="h-{esc(key)}">{esc(label)}'
            f'<span class="n">{counts[key]}</span></label>'
        )
        panels.append(
            f'<div class="tabpanel" id="p-{esc(key)}">{_sections(digest, key)}</div>'
        )
    return (f'<div class="tabs">{"".join(inputs)}'
            f'<div class="tablist">{"".join(labels)}</div>'
            f'{"".join(panels)}</div>')


def _tldr(digest: dict) -> str:
    items = digest.get("tldr") or []
    if not items:
        return ""
    lis = "".join(f"<li>{esc(t)}</li>" for t in items)
    return f'<div class="tldr"><h2>Das Wichtigste in Kürze</h2><ul>{lis}</ul></div>'


def _footer(model: str, *, depth: int = 0) -> str:
    up = "../" * depth
    return (f'<footer><span>Täglich kuratiert von {esc(model)}.</span>'
            f'<span><a href="{up}archive/index.html">Alle früheren Ausgaben</a></span>'
            f'<span><a href="{up}feed.xml">Per RSS abonnieren</a></span></footer>')


def render_digest_page(date_iso: str, digest: dict, *, model: str, depth: int = 0) -> str:
    body = (_masthead(date_iso, digest, depth=depth) + _tldr(digest)
            + _tabs(digest) + _footer(model, depth=depth))
    return _page(f"{esc(SITE_TITLE)} — {esc(date_iso)}", body, depth=depth)


def render_archive_index(editions: list, *, model: str) -> str:
    rows = []
    for date_iso, digest in editions:
        peek = (digest.get("tldr") or [""])[0]
        count = item_count(digest)
        rows.append(
            f'<li><a href="{esc(date_iso)}.html">'
            f'<span class="d">{esc(pretty_date(date_iso))}</span>'
            f'<span class="n">{count} {"Beitrag" if count == 1 else "Beiträge"}</span>'
            f'<span class="peek">{esc(peek)}</span></a></li>'
        )
    body = f"""<header class="masthead">
  <h1><a href="../index.html">{esc(SITE_TITLE)}</a></h1>
  <nav><a href="../index.html">Aktuell</a><a href="../feed.xml">Feed</a></nav>
  <div class="dateline">{len(editions)} {'Ausgabe' if len(editions) == 1 else 'Ausgaben'}</div>
</header>
<ul class="archive-list">{''.join(rows)}</ul>
{_footer(model, depth=1)}"""
    return _page(f"Archiv — {esc(SITE_TITLE)}", body, depth=1)


def render_feed(editions: list, *, site_url: str) -> str:
    base = site_url.rstrip("/")
    updated = (
        f"{editions[0][0]}T06:00:00Z" if editions
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    entries = []
    for date_iso, digest in editions[:30]:
        summary = " ".join(digest.get("tldr") or []) or "Täglicher Nachrichtenüberblick."
        entries.append(f"""  <entry>
    <title>{esc(SITE_TITLE)} — {esc(pretty_date(date_iso))}</title>
    <link href="{esc(base)}/archive/{esc(date_iso)}.html"/>
    <id>{esc(base)}/archive/{esc(date_iso)}.html</id>
    <updated>{esc(date_iso)}T06:00:00Z</updated>
    <summary>{esc(summary)}</summary>
  </entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{esc(SITE_TITLE)}</title>
  <link href="{esc(base)}/"/>
  <link rel="self" href="{esc(base)}/feed.xml"/>
  <id>{esc(base)}/</id>
  <updated>{updated}</updated>
{chr(10).join(entries)}
</feed>"""
