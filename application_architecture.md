# Anwendungsarchitektur

## Was diese Anwendung tut

Ein **täglicher Frankfurt-Nachrichtenüberblick, veröffentlicht als statische
Website auf GitHub Pages**. Einmal am Tag sammelt sie Meldungen über Frankfurt am
Main, lässt ein LLM die interessantesten auswählen und zusammenfassen, speichert
das Ergebnis als JSON und baut aus allen gespeicherten Ausgaben eine statische
Seite neu.

Sie ist für einen bestimmten Leser gebaut: **eine Privatperson, die in Frankfurt
lebt** — keinen Immobilienprofi und keinen Journalisten. Jeder Hauptbeitrag trägt
deshalb eine Einordnung in Alltagssprache, die die Handlung oder Entscheidung
benennt, um die es geht.

Die Seite gliedert sich zweifach: **drei Reiter nach Zeithorizont** — Aktuell, In
den nächsten Wochen, In den nächsten Monaten — und darunter jeweils dieselben
**vier Rubriken**. Der Zeithorizont beantwortet „wann betrifft mich das“, die
Rubrik „worum geht es“; beide Fragen stellt dieser Leser, und keine der beiden
lässt sich aus der anderen ableiten.

Vier Rubriken:

1. **Neubau & Immobilien** — ausschließlich Vorhaben, die für Privatkunden
   zählen: Eigentumswohnungen zum Kauf, neue Mietwohnungen, Wohnquartiere,
   Sanierungen. Mit Stadtteil, Wohnungszahl, Preisen und Zeitplan, soweit die
   Quelle sie hergibt. Reine Gewerbe-, Büro- und Logistikprojekte,
   Transaktionsmeldungen und Branchenpersonalien fallen weg — der Leser will
   wissen, wo er wohnen kann, nicht was die Branche macht.
2. **Konzerte, Kino & Comedy** — Pop- und Rockkonzerte internationaler Stars in
   Frankfurt mit Schwerpunkt auf US-Acts und K-Pop, dann Comedy und Kabarett,
   Kino, Musical und Bühne. Immer mit Termin, Spielort und Vorverkaufsstart,
   soweit genannt, weil man genau dabei rechtzeitig handeln muss.
3. **Messen & Feste** — alles, wozu man als Besucher hingehen kann:
   Publikumsmessen, Buchmesse, Dippemess, Wäldchestag, Museumsuferfest,
   Weihnachtsmärkte. Die großen Fachmessen zählen mit, weil sie die Stadt für
   eine Woche verändern.
4. **Frankfurt allgemein** — was den Alltag trifft: Verkehr, Baustellen,
   Streckensperrungen, Stadtpolitik mit praktischen Folgen, Museen,
   Neueröffnungen. Ohne Polizeibericht, Sportergebnisse und Wetter.

Entwurfsziel: **nahezu keine Kosten**. Kostenlose RSS-Feeds, kostenlose GitHub
Actions, kostenloses GitHub Pages und genau **ein LLM-Aufruf pro Tag**
(~1,50–2,80 $/Jahr mit dem Standardmodell). Das Repository muss öffentlich sein:
GitHub Pages aus einem privaten Repository verlangt einen kostenpflichtigen Plan,
der ein Vielfaches des restlichen Projekts kosten würde. Der LLM-Aufruf läuft
über OpenRouter, ein API-Key erreicht damit alle Anbieter, und das Modell zu
wechseln ist eine Repository-Variable.

## Wie es funktioniert

```
GitHub-Actions-Cron (täglich 05:00 UTC)
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│ main.py      (Modell und Feeds kommen aus configuration.py)  │
│                                                              │
│  1. HOLEN      Alle Beiträge aus 33 RSS-Feeds ziehen, in     │
│                einem einzigen parallelen Pool                │
│                • Rückblick je Rubrik: 24 h bis 168 h,        │
│                  verbreitert, wenn ein Lauf ausfiel          │
│                • kein Stichwortfilter — das LLM wählt aus    │
│                • Limit je Feed, dann 30 Kandidaten je Rubrik │
│                                                              │
│  2. ENTDOPPELN digests/*.json laden, jeden Kandidaten        │
│                verwerfen, dessen Link in den letzten 9       │
│                Ausgaben vorkam                               │
│                                                              │
│  3. AUSWÄHLEN  EIN LLM-Aufruf über OpenRouter, liefert       │
│                strukturiertes JSON: Hauptbeiträge mit        │
│                Einordnung, dazu einzeilige Erwähnungen —     │
│                jeder Beitrag mit Rubrik UND Zeithorizont     │
│                                                              │
│  4. SPEICHERN  digests/<datum>.json schreiben, dann alle     │
│                Ausgaben jenseits der neuesten 30 löschen     │
│                                                              │
│  5. BAUEN      render.py baut die GANZE Seite aus allen      │
│                gespeicherten Ausgaben neu: Startseite mit    │
│                drei Reitern à vier Rubriken, Archivseiten    │
│                je Tag, Archivliste, Atom-Feed                │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
Workflow committet digests/, deployt dann site/ auf GitHub Pages
        │
        ▼
https://<benutzer>.github.io/<repo>/   (+ feed.xml für den RSS-Reader)
```

Wesentliche Entwurfsentscheidungen:

- **Die Auswahl passiert im LLM, nicht im Code.** Alles im Zeitfenster geht an
  das Modell (Eingabe-Token sind billig), und *es* entscheidet, was zählt —
  Auswahl nach Bedeutung, nicht nach Aktualität. Genau so wird auch der
  Ortsbezug durchgesetzt: der Prompt sagt, dass Kassel, Wiesbaden und „der
  deutsche Wohnungsmarkt“ nicht hierhergehören, statt das in Stichwortlisten zu
  gießen, die an jedem Ortsnamen scheitern würden, den niemand vorhergesehen hat.
- **Der Ortsbezug ist die härteste Regel im Prompt.** Mehrere Quellen sind
  überregional (immobilienmanager) oder decken ganz Hessen ab (hessenschau), und
  Google-News-Suchen liefern regelmäßig Treffer aus anderen Städten. Ohne eine
  ausdrückliche, weit oben stehende Regel füllt sich die Seite mit Meldungen, die
  formal zum Suchbegriff passen und für diesen Leser wertlos sind.
- **Der Zeithorizont wird vom Modell vergeben, nicht aus einem Datum gerechnet.**
  Die Termine stehen als Fließtext in den Meldungen („ab Herbst 2027“, „Karten ab
  Freitag“, „im kommenden Frühjahr“), oft mehrere in einem Beitrag und meist
  ohne Jahreszahl. Ein Parser müsste raten, welches der genannten Daten das
  maßgebliche ist — genau die Entscheidung, für die das Modell ohnehin schon
  da ist. Es bekommt das heutige Datum im Nutzertext mitgeliefert und ordnet
  jeden Beitrag einem der drei Horizonte zu.
- **Ein unbekannter Horizont fällt auf den ersten zurück, statt zu
  verschwinden.** `fix_horizon()` in `main.py` nagelt den Wert beim Einlesen auf
  die bekannten Schlüssel fest, `horizon_of()` in `render.py` tut dasselbe beim
  Rendern. Doppelt, weil die Folgen sonst still wären: Ein Beitrag mit einem
  erfundenen Horizont läge unter keinem Reiter und wäre damit unsichtbar,
  obwohl er in der gespeicherten Ausgabe steht. Dieselbe Absicherung deckt
  ältere Ausgaben aus der Zeit vor den Reitern ab.
- **Die Reiter kommen ohne JavaScript aus.** Drei Radiobuttons, deren
  `:checked`-Zustand per Geschwister-Selektor die Beschriftung hervorhebt und das
  passende Panel einblendet; die neun Regeln dafür erzeugt `_horizon_css()` aus
  `HORIZONS`, damit ein zusätzlicher Reiter nicht daran scheitert, dass jemand
  eine Zeile vergisst. Die Seite bleibt damit eine reine Textdatei ohne
  Laufzeitabhängigkeit, und die Pfeiltasten schalten die Reiter von Haus aus
  weiter. Der Preis: Die Textsuche des Browsers findet nur den sichtbaren Reiter.
- **Alle vier Rubriken erscheinen in jedem Reiter, auch die leeren.** Zwölf
  Blöcke für ein gutes Dutzend Beiträge klingt nach Verschwendung, aber sichtbar
  ist immer nur ein Reiter, und eine Rubrik, die je nach Zeitraum verschwände,
  ließe den Leser rätseln, ob es nichts gibt oder ob etwas kaputt ist — dieselbe
  Überlegung, aus der eine leere Rubrik ihre Überschrift behält.
- **Voreingestellt ist der erste Reiter, der etwas enthält.** Stur der erste zu
  sein hieße, dass die Seite an einem Tag ohne aktuelle Termine auf einer leeren
  Ansicht aufgeht, obwohl weiter hinten etwas steht.
- **Die Obergrenzen gelten je Rubrik, nicht je Reiter.** Sonst entstünde ein
  Anreiz, Beiträge in einen falschen Zeitraum zu schieben, damit ein Reiter
  voller wirkt; der Prompt verbietet das ausdrücklich.
- **Das Modell liefert JSON, keinen Fließtext.** Die gesamte Darstellung liegt in
  `render.py`. Fließtext zurück in gestaltetes HTML zu parsen ist brüchig;
  strukturierte Daten speisen sauber die Seite, das Archiv und den Feed.
- **Gespeicherte Ausgaben sind zugleich Archiv und Zustand der
  Wiederholungssperre.** Keine Datenbank, keine getrennte Zustandsdatei. Die
  Zeitfenster überlappen den täglichen Takt mit Absicht, damit nichts durch eine
  Lücke fällt; die Entdoppelung ist das, was diese Überlappung wiederholungsfrei
  macht.
- **Die ganze Seite wird bei jedem Lauf neu gebaut.** Eine Änderung an Vorlage
  oder Farbpalette erreicht damit jede frühere Ausgabe, nicht nur die von heute —
  sonst bliebe das Archiv im Design des Tages eingefroren, an dem es entstand.
- **Der Neubau läuft auch an ruhigen Tagen.** Überlebt nichts die Entdoppelung,
  entfällt der LLM-Aufruf, die Seite wird aber trotzdem gebaut, sodass eine
  Gestaltungsänderung nicht auf Nachrichten warten muss.
- **Unterschiedliche Zeitfenster je Rubrik, statt 24 Stunden für alle.** Die
  Nachrichtenmenge ist hier sehr ungleich verteilt: vier Lokalredaktionen liefern
  täglich, ein neues Bauvorhaben oder eine Konzertankündigung nur alle paar Tage.
  Ein einheitliches Tagesfenster hielte Immobilien und Events fast immer leer.
  Daher 168 h für Immobilien und Messen, 120 h für Events, 24 h für die Stadt.
- **Google-News-Suchfeeds als bewusste Quellenwahl.** Für Frankfurter
  Nischenthemen gibt es keine eigenen Feeds. Journal Frankfurt (403) und
  Frankfurt-Tipp (404) sperren automatisierte Abrufe aus, Messe Frankfurt und
  frankfurt.de bieten keinen nutzbaren Feed. Eine Google-News-Suche bündelt genau
  die Lokalmedien, die einzeln nicht abonnierbar sind, und ist die einzige
  Quelle, mit der sich ein Thema wie „K-Pop-Konzert in Frankfurt“ überhaupt
  gezielt beobachten lässt. Alle in `configuration.py` eingetragenen Feeds wurden
  vor Aufnahme auf Erreichbarkeit und Aktualität geprüft.
- **Der Herausgeber wird nachgeschlagen, nicht vom Modell abgeschrieben.**
  Google-News-Links zeigen auf `news.google.com` und leiten weiter, die Domain
  taugt also nicht als Quellenangabe. `entry_publisher()` liest den echten
  Herausgeber aus dem `<source>`-Element des Feeds, `attach_publishers()` ordnet
  ihn nach dem Modellaufruf über den Link wieder zu. Abgetippt wäre er
  irgendwann falsch, nachgeschlagen ist er es nie. `strip_publisher_suffix()`
  entfernt zusätzlich das „ – FNP“, das Google News an jede Überschrift hängt.
- **Keine Meldung erscheint in zwei Rubriken, und `drop_cross_section()` setzt
  das durch.** Die Rubriken werden aus getrennten Feedlisten gebaut und
  unabhängig entdoppelt; eine Zeitung, die über Neubau und Stadtpolitik
  schreibt, böte dieselbe Meldung sonst beiden an, und das Modell könnte sie
  zweimal platzieren. Frühere Rubriken gewinnen.
- **Ein Limit je Feed verhindert, dass eine Quelle die Rubrik füllt.** `per_feed`
  (6) in `SECTION_TUNING`. Das ist hier wichtiger als im Vorgängerprojekt: bei
  einem 168-Stunden-Fenster liefert ein Feed wie immobilienmanager über zwanzig
  Beiträge, von denen die meisten nichts mit Frankfurt zu tun haben.
- **Die Rubriken sind fest und unabhängig.** Alle vier erscheinen immer, in
  derselben Reihenfolge, und keine borgt Kapazität von einer anderen. Eine leere
  Rubrik behält ihre Überschrift und liest sich als „Heute nichts Neues.“, statt
  zu verschwinden — eine ruhige Quelle bleibt so sichtbar von einer kaputten
  unterscheidbar. Jede Rubrik wird nur an ihren eigenen Kandidaten gemessen.
- **Aufholen nach einem ausgefallenen Lauf.** `effective_window()` verbreitert
  jedes Fenster um einen Tag je fehlender Ausgabe, weil geplante Actions-Läufe
  regelmäßig verzögert und gelegentlich ganz übersprungen werden — ohne das wären
  die Nachrichten eines ausgefallenen Tages für jede künftige Ausgabe verloren.
- **Die Entdoppelung muss weiter reichen als das breiteste Fenster.**
  `DEDUP_EDITIONS` (9) deckt mehr Tage ab als 168 Stunden plus etwas Reserve. Ein
  Fenster darüber hinaus zu verbreitern, ohne diesen Wert anzuheben, ließe alte
  Beiträge wieder auftauchen.
- **Das Archiv ist begrenzt und wird in Python beschnitten, nicht im Workflow.**
  `KEEP_DIGESTS` (30) entfernt die ältesten Ausgaben, bevor die Seite gebaut
  wird, damit das Archiv auf der Platte und auf der Seite immer übereinstimmen
  und lokale Läufe sich gleich verhalten. Der Wert liegt deutlich über
  `DEDUP_EDITIONS`, weil eine gelöschte Ausgabe eine Wiederholung nicht mehr
  verhindern kann.
- **Ein Anbieter, alle Modelle.** Die gesamte Inferenz läuft über OpenRouter im
  OpenAI-kompatiblen `/chat/completions`-Format statt über ein Anbieter-SDK. Ein
  Key, kein Aufschlag pro Token, Zugriff auf neue Modelle am Erscheinungstag,
  automatisches Ausweichen bei Störungen.
- **Sowohl die Ausgabe des Modells als auch der Inhalt der Feeds gelten als
  ungeprüft.** RSS kann jeder veröffentlichen, ein Feedeintrag könnte also Prompt
  Injection versuchen; der System-Prompt erklärt Kandidatentext zu Daten, niemals
  zu Anweisungen. Modellausgaben werden überall escaped, wo sie gerendert werden,
  und der Tag-Wert steht auf einer Positivliste, bevor er in ein
  `style`-Attribut gelangt.
- **Jede URL, die das Modell zurückgibt, wird gegen die tatsächlich gesendeten
  Kandidatenlinks geprüft** (`sanitize_urls`). Das schließt zwei Lücken auf
  einmal: eine `javascript:`- oder `data:`-URL landete sonst in einem `href` auf
  einer öffentlichen Seite, und Modelle erfinden gelegentlich eine plausible URL,
  was einen toten Link veröffentlichen würde. Ein nicht überprüfbarer Link wird
  entfernt, der Text des Beitrags bleibt.
- **Alle Feeds werden parallel geholt.** `prefetch()` füllt einen Cache für alle
  vier Rubriken, bevor eine davon gebaut wird, der Lauf dauert also so lange wie
  der langsamste einzelne Feed und nicht wie die Summe.
- **Die Ausgabe ist nach oben begrenzt** (`MAX_OUTPUT_TOKENS`, 6000). Eine
  randvolle Ausgabe misst gerechnet rund 4.000 Token; der Wert schneidet also nie
  eine echte Ausgabe ab, begrenzt aber die Kosten im schlimmsten Fall.
- **Kontrolliertes Nachgeben bei Fehlern.** Ein kaputter Feed wird mit einer
  Warnung übersprungen. Fehlerhaftes JSON wird repariert, wo es geht (Code-Fences,
  Fließtext drumherum), bevor aufgegeben wird. Erwartete Fehler geben Hinweise
  aus statt eines Tracebacks.

## Dateien

| Datei | Zweck |
|---|---|
| `configuration.py` | **Worum es geht, als einfache Werte:** Modell, Feedlisten, `KEEP_DIGESTS`. Keine Imports, keine Logik — nichts hier kann eine Ausnahme werfen. |
| `main.py` | Ablaufsteuerung. Ein Tuning-Block (Zeitfenster, Limits, Pfade, Überschreiben per Repository-Variable), `SYSTEM_PROMPT`, dann Feedabruf, `summarize` / `parse_digest`, Speicherung (`load_editions`, `save_digest`, `prune_editions`), Entdoppelung und `build_site`. |
| `render.py` | Die gesamte Darstellung, in sich geschlossen: `SITE_TITLE`, `SECTIONS`, `TAG_LABELS` und `CSS` oben, darunter die Vorlagen, die gespeicherte Ausgaben in `index.html`, Archivseiten je Tag, die Archivliste und `feed.xml` verwandeln. |
| `.github/workflows/daily-digest.yml` | Täglicher Cron plus manueller Auslöser. Baut, committet `digests/`, veröffentlicht `site/` über `upload-pages-artifact` / `deploy-pages` auf GitHub Pages. |
| `digests/<datum>.json` | Eine gespeicherte Ausgabe. Vom Workflow committet — Archiv und Zustand der Wiederholungssperre. |
| `requirements.txt` | `openai` (der OpenAI-kompatible Client, auf OpenRouter gerichtet) und `feedparser`. |
| `README.md` | Einrichtung, Modellwahl, Fehlersuche, Kosten. |
| `application_architecture.md` | Dieses Dokument. |

**Die Aufteilung folgt der Zielgruppe, nicht dem Dateityp.** `configuration.py`
beantwortet die Fragen, die ein Betreiber stellt — *welches Modell, welche
Quellen, wie lange behalte ich das* — und sonst nichts. Sie ist bewusst leblos:
reine Literale, keine Imports, keine Funktionsaufrufe. Ein Tippfehler dort ist
ein Syntaxfehler statt eines subtilen Laufzeitfehlers, und sie lässt sich
ändern, ohne Code zu lesen.

Alles Übrige steht neben dem Code, der es benutzt, weil es für sich genommen
nicht verständlich ist. `DEDUP_EDITIONS` ergibt nur im Verhältnis zu den
Zeitfenstern Sinn, `MAX_CANDIDATES_PER_SECTION` nur im Verhältnis zu den
Obergrenzen im Prompt, `SECTIONS` und `TAG_LABELS` nur im Verhältnis zum CSS, das
sie einfärbt. Diese Werte in eine Einstellungsdatei zu heben, trennte jeden von
der Bedingung, die ihn erklärt, und machte aus einer Änderung zwei Dateien.

Der Abhängigkeitsgraph bleibt zyklenfrei: `main.py` importiert `configuration`
und `render`; `render` importiert keines von beiden. Deshalb steht `SECTIONS` in
`render.py`, und `main.py` leitet `SECTION_KEYS` daraus ab — andersherum würden
sich die beiden Module gegenseitig importieren.

### `configuration.py`

| Was | Einstellung |
|---|---|
| Modell | `MODEL` |
| Quellen für Neubau und Immobilien | `IMMOBILIEN_FEEDS` |
| Quellen für Konzerte, Kino und Comedy | `EVENT_FEEDS` |
| Quellen für Messen und Feste | `MESSE_FEEDS` |
| Quellen für allgemeine Stadtnachrichten | `STADT_FEEDS` |
| Zuordnung Rubrik → Feedliste | `FEEDS` |
| Wie viele Ausgaben auf der Platte bleiben | `KEEP_DIGESTS` (30) |

### `main.py`

| Was | Wo |
|---|---|
| Leserprofil, Ortsbezug, was als interessant gilt | `SYSTEM_PROMPT` |
| Beiträge je Rubrik | der Block `Umfang:` innerhalb von `SYSTEM_PROMPT` |
| Grenzen zwischen den Reitern | der Block `ZEITHORIZONT` innerhalb von `SYSTEM_PROMPT` |
| Zeithorizont absichern | `fix_horizon()`, `HORIZON_KEYS` |
| Rückblick und Feedlimit je Rubrik | `SECTION_TUNING`, gelesen über `tuning()` |
| Kandidatenobergrenze je Rubrik | `MAX_CANDIDATES_PER_SECTION` (30) |
| Wie viele frühere Ausgaben die Entdoppelung umfasst | `DEDUP_EDITIONS` (9) |
| Obergrenze der Ausgabe | `MAX_OUTPUT_TOKENS` (6000) |
| Wohin Ausgaben und Seite geschrieben werden | `DIGEST_DIR`, `SITE_DIR` |
| Parallelität und Zeitlimit beim Abruf | `FEED_WORKERS`, `FEED_TIMEOUT_SECONDS`, `USER_AGENT` |
| Überschreiben per Repository-Variable, `int()`-Umwandlung | `env_or()`, `env_int()` |
| Herausgeber aus Sammelfeeds | `entry_publisher()`, `strip_publisher_suffix()`, `attach_publishers()` |
| Entdoppelung über Rubriken hinweg | `drop_cross_section()` |
| Aufholen nach einem ausgefallenen Lauf | `effective_window()` |
| Archiv auf `KEEP_DIGESTS` kürzen | `prune_editions()` |
| Pages-Adresse aus dem Repository ableiten | `default_site_url()` |
| Prüfung von Key und Feedzuordnung vor dem Lauf | `preflight()` |

### `render.py`

| Was | Wo |
|---|---|
| Seitenname | `SITE_TITLE` |
| Reihenfolge und Anzeigenamen der Rubriken | `SECTIONS` |
| Reihenfolge und Anzeigenamen der Reiter | `HORIZONS` |
| Reiterleiste, Panels, voreingestellter Reiter | `_tabs()`, `_horizon_css()` |
| Zuordnung eines Beitrags zu einem Reiter | `horizon_of()`, `section_of()` |
| Beschriftung der Tag-Etiketten | `TAG_LABELS` |
| Deutsche Wochentags- und Monatsnamen | `WEEKDAYS_DE`, `MONTHS_DE`, `pretty_date()` |
| Quellenangabe unter einem Beitrag | `attribution()` |
| Farben, Typografie, Layout, Dark Mode | `CSS` |

Sieben Einstellungen nehmen eine gleichnamige Repository-Variable an, einmalig im
Tuning-Block von `main.py` aufgelöst: `MODEL`, `SITE_URL`, `KEEP_DIGESTS` und die
vier `MAX_AGE_HOURS_<RUBRIK>`. Ein nicht numerischer Wert warnt und fällt auf den
Wert aus der Datei zurück, statt den Lauf scheitern zu lassen.

### Kopplungen, die man beachten muss

Fünf Einstellungen reichen über mehr als eine Datei, eine zu ändern heißt also,
ihren Partner mitzuändern:

- **Die Schlüssel in `SECTIONS`** (`render.py`) müssen den Rubrikschlüsseln im
  `SYSTEM_PROMPT` (`main.py`), den Schlüsseln in `FEEDS` (`configuration.py`) und
  denen in `SECTION_TUNING` (`main.py`) entsprechen, und jeder braucht eine
  `.section.<schlüssel>`-Farbregel samt Custom-Property im CSS. `preflight()`
  fängt eine fehlende Feedliste ab, bevor Arbeit anfällt.
- **Die Schlüssel in `TAG_LABELS`** (`render.py`) müssen den erlaubten
  `tag`-Werten im `SYSTEM_PROMPT` entsprechen, und jeder braucht ein Paar
  `--tag-<schlüssel>-bg` / `-fg` im CSS, in beiden Farbschemata. Ein unbekanntes
  Tag fällt auf die neutrale `news`-Darstellung zurück, statt etwas kaputtzumachen.
- **`KEEP_DIGESTS`** (`configuration.py`) **muss über `DEDUP_EDITIONS`**
  (`main.py`) liegen, weil eine gelöschte Ausgabe eine Wiederholung nicht mehr
  verhindern kann.
- **`DEDUP_EDITIONS`** (`main.py`) muss mehr Tage abdecken als das breiteste
  Fenster in `SECTION_TUNING` (derzeit 168 Stunden = 7 Tage).
- **Die Schlüssel in `HORIZONS`** (`render.py`) müssen den erlaubten
  `horizon`-Werten im Block `ZEITHORIZONT` des `SYSTEM_PROMPT` entsprechen. Das
  CSS erzeugt sich aus der Liste, dort ist nichts nachzuziehen. Der **erste**
  Eintrag muss der Reiter für die Gegenwart bleiben: Er ist der Rückfallwert für
  jeden Beitrag ohne brauchbaren Horizont.

## Das Modell wechseln

`MODEL` in `configuration.py` ändern oder eine Repository-**Variable** namens
`MODEL` setzen (Settings → Secrets and variables → Actions → Tab Variables) — die
Variable gewinnt, und der nächste Lauf übernimmt sie ohne Commit. Lokal:
`$env:MODEL = "openai/gpt-5.4-mini"`. Weil alles über OpenRouter läuft, ist der
Anbieterwechsel derselbe Vorgang wie der Modellwechsel. Den exakten Slug von
OpenRouter verwenden — `openai/gpt-5.6-luna` hat einen Punkt, keinen Bindestrich.

Dasselbe Muster gilt für die vier `MAX_AGE_HOURS_<RUBRIK>`, `KEEP_DIGESTS` und
`SITE_URL`: Vorgabe in der Datei, Repository-Variable überschreibt sie.

## Die Länge einer Ausgabe einstellen

Die Zahlen je Rubrik stehen im Block `Umfang:` des `SYSTEM_PROMPT`:

| Rubrik | Hauptbeiträge | „Außerdem notiert“ |
|---|---|---|
| Neubau & Immobilien | 4 | 5 |
| Konzerte, Kino & Comedy | 5 | 6 |
| Messen & Feste | 3 | 4 |
| Frankfurt allgemein | 4 | 6 |

Das sind Deckel, keine Zielvorgaben. „Außerdem notiert“ ist der billige Regler —
jeder Eintrag kostet eine überfliegbare Zeile, für mehr Überblick ohne längere
Lesezeit also dort erhöhen. Für eine schnellere Lektüre die Zahl der
Hauptbeiträge senken.

## Quellen ändern

Die Feedlisten in `configuration.py` bearbeiten. Jeder Eintrag ist ein Tupel
`("Anzeigename", "https://feed-url")`:

- **Neubau und Immobilien** → `IMMOBILIEN_FEEDS`
- **Konzerte, Kino, Comedy** → `EVENT_FEEDS`
- **Messen und Feste** → `MESSE_FEEDS`
- **Allgemeine Stadtnachrichten** → `STADT_FEEDS`

Für ein neues Thema reicht meist eine weitere Google-News-Zeile mit anderem
Suchbegriff; die Hilfsvorlage `_GN` oben in der Datei baut die URL. Suchbegriffe
mit `+` verbinden, `OR` wird unterstützt, und ohne Umlaute schreiben, damit die
Datei ASCII bleibt.

Es gibt keinen Stichwortfilter — alles Aktuelle ist ein Kandidat, und das LLM
entscheidet. Kaputte Feeds werden mit einer Warnung übersprungen, ein Tippfehler
legt die Ausgabe also nicht lahm. Vor dem Eintragen lohnt ein kurzer Test, ob der
Feed überhaupt antwortet und aktuelle Beiträge enthält: mehrere naheliegende
Frankfurter Quellen (Journal Frankfurt, Frankfurt-Tipp, Messe Frankfurt,
frankfurt.de) tun das nicht.

## Betrieb und Wartung

### Ersteinrichtung

1. Nach GitHub pushen — **vorher `git remote set-url origin` auf das eigene
   Repository setzen**, dieses Verzeichnis zeigt noch auf das Vorgängerprojekt.
2. Das Secret `OPENROUTER_API_KEY` hinterlegen.
3. **Settings → Pages → Source: GitHub Actions.** Keinen Branch auswählen.
4. Actions → Täglicher Frankfurt-Überblick → Run workflow.

### Ausführen

- **Automatisch:** der Cron im Workflow läuft täglich um 05:00 UTC.
- **Manuell:** Tab Actions → Run workflow.
- **Lokal:** `pip install -r requirements.txt`, `OPENROUTER_API_KEY` setzen,
  `python main.py`. Schreibt `digests/` und `site/`; `site/index.html` zum
  Ansehen öffnen. Veröffentlicht wird nichts.

### Wartung

Das ist wartungsarm — kein Server, keine Datenbank. Gelegentlich:

- **Seite aktualisiert sich nicht?** Im Tab Actions nach einem roten Lauf sehen.
  Das Protokoll nennt die Ursache (fehlender Key, falscher Modell-Slug,
  fehlerhaftes JSON). Ein grüner Lauf mit „Nichts Neues seit der letzten
  Ausgabe“ heißt, dass es wirklich nichts gab.
- **Erstes Deployment scheitert?** Fast immer steht die Pages-Quelle nicht auf
  GitHub Actions.
- **Feed-Warnungen** (`WARNUNG: ... nicht lesbar`): die Adresse ist umgezogen
  oder die Seite ist unten. Eintrag in `configuration.py` anpassen oder
  entfernen. Bei Google-News-Feeds ist das unwahrscheinlich, bei
  Zeitungsfeeds kommt es vor.
- **Eine Rubrik bleibt dauerhaft leer?** Wahrscheinlich sind ihre Suchbegriffe zu
  eng. Ein Feed, dessen neuester Beitrag älter ist als das Zeitfenster der
  Rubrik, kann per Definition nie etwas beitragen.
- **GitHub schaltet Cron-Jobs nach ~60 Tagen ohne Aktivität im Repository ab.**
  Der Workflow committet an den meisten Tagen eine Ausgabe, was als Aktivität
  zählt — sollten die Ausgaben trotzdem ausbleiben und im Tab Actions ein Banner
  stehen, auf „Enable workflow“ klicken.
- **API-Kosten:** einsehbar unter
  [openrouter.ai/activity](https://openrouter.ai/activity).
- **Qualität lässt nach?** Das Leserprofil im `SYSTEM_PROMPT` nachschärfen oder
  `MODEL` eine Stufe höher setzen.
