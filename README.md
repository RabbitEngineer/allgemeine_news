# Allgemeine News

Ein täglicher Nachrichtenüberblick für jemanden, der in Frankfurt am Main wohnt,
veröffentlicht als **kostenlose GitHub-Pages-Website**, die sich jeden Morgen
selbst neu baut.

Oben stehen drei Reiter nach Zeithorizont — **Aktuell**, **In den nächsten
Wochen**, **In den nächsten Monaten**. Unter jedem Reiter liegen dieselben sechs
Rubriken, gefüllt mit den Beiträgen dieses Zeitraums:

1. **Neubau & Immobilien in Frankfurt** — Bauvorhaben, die für Privatkunden
   zählen: Eigentumswohnungen, neue Mietwohnungen, ganze Wohnquartiere, mit
   Stadtteil, Wohnungszahl, Preisen und Zeitplan, soweit die Quelle sie nennt.
2. **Konzerte, Kino & Comedy in Deutschland** — internationale Pop-Acts, K-Pop,
   bekannte Stars aus Asien, US-Comedians, Filmstarts und große Tourneen. Mit
   Termin, **Stadt**, Spielort und Vorverkaufsstart.
3. **Sport** — internationale Damenturniere in Tennis und Volleyball, die in
   Deutschland stattfinden, damit man rechtzeitig Karten bekommt.
4. **Messen & Feste in Frankfurt** — Publikumsmessen, Buchmesse, Dippemess,
   Wäldchestag, Museumsuferfest, Weihnachtsmärkte, dazu die großen Fachmessen,
   weil sie die Stadt für eine Woche verändern.
5. **Frankfurt & Infrastruktur** — was den Alltag hier betrifft: Verkehr,
   Baustellen, Nahverkehr, Stadtpolitik mit praktischen Folgen, Museen,
   Neueröffnungen.
6. **Peking & China** — China als möglicher künftiger Arbeitsort: deutsche
   Arbeitgeber vor Ort, Arbeitserlaubnis und Visum, Arbeitsmarkt für Fachkräfte.
   **Keine Stellenanzeigen** — warum nicht, steht unten.

## Die Radien sind je Rubrik verschieden

Das ist die wichtigste Entwurfsentscheidung und der Grund, warum die Seite nicht
mehr „Frankfurt Kompakt" heißt:

| Rubrik | Radius | warum |
|---|---|---|
| Neubau & Immobilien | nur Frankfurt | man wohnt an einem Ort |
| Messen & Feste | nur Frankfurt | man geht dort hin, wo man wohnt |
| Frankfurt & Infrastruktur | nur Frankfurt | betrifft den täglichen Weg |
| Konzerte, Kino & Comedy | ganz Deutschland | für einen Weltstar fährt man nach Köln oder Berlin |
| Sport | nur Deutschland | Karten kauft man für das, was erreichbar ist |
| Peking & China | China | ein möglicher künftiger Arbeitsort, kein Alltag |

Bei den deutschlandweiten Rubriken kommt eine Qualitätsschwelle dazu: Konzerte
nur bei **großen internationalen Namen**, nicht bei regionalen Bands oder
Clubkonzerten. Der Maßstab im Prompt lautet: Würde jemand dafür in eine andere
Stadt fahren und Monate vorher eine Karte kaufen? Wenn nein, fällt es raus.

Läuft kostenlos auf GitHub Actions. Der einzige Kostenpunkt ist ein LLM-Aufruf
pro Tag — mit dem Standardmodell etwa **1,50 bis 2,80 US-Dollar im Jahr**.

## Wie es funktioniert

1. **Holen** — sammelt aktuelle Beiträge aus kostenlosen RSS-Feeds. Es braucht
   keinen News-API-Key.
   - *Lokalpresse mit eigenem Feed*: FAZ Frankfurt, Frankfurter Rundschau,
     Frankfurter Neue Presse, hessenschau (Nachrichten und Kultur).
   - *Fachquelle*: [SkylineAtlas](https://skylineatlas.de) verfolgt Frankfurter
     Bauprojekte von der Planung bis zur Fertigstellung.
   - *Google-News-Suchfeeds* für alles Übrige — Tourneen und Vorverkäufe,
     K-Pop, asiatische und US-Stars, die großen Arenen, US-Comedians, Kinostarts,
     WTA-Turniere, Damenvolleyball, Messe Frankfurt, Buchmesse, Stadtfeste,
     Verkehr, Nahverkehr, Infrastruktur, Gastronomie.

   **Kein überregionaler Immobilien-Fachdienst mehr.** `immobilienmanager` stand
   hier und lieferte Logistikhallen in Köln, ESG-Übernahmen und Bilanzen von
   Projektentwicklern. Der Prompt verwarf davon zuverlässig alles — aber der Feed
   belegte mit seinem Limit von 6 vorher zwei Drittel des Kandidatenbudgets der
   Rubrik, sodass echte Frankfurter Bauvorhaben gar nicht erst zur Auswahl kamen.

   Warum so viele Suchfeeds: Für Frankfurter Nischenthemen gibt es schlicht keine
   eigenen Feeds. Journal Frankfurt und Frankfurt-Tipp wären naheliegend, liefern
   aber 403 beziehungsweise 404 an automatisierte Abrufe; die Messe Frankfurt und
   die Stadt Frankfurt bieten keinen nutzbaren Feed an. Google News bündelt
   genau die Lokalmedien, die man einzeln nicht abonnieren kann. Keine Meldung
   erscheint in zwei Rubriken.

2. **Entdoppeln** — alles, was die letzten 16 Ausgaben schon gebracht haben, fällt
   raus. Eine Meldung erscheint einmal, auch wenn das Zeitfenster zwei Wochen
   umspannt.
3. **Auswählen und zusammenfassen** — alle verbliebenen Kandidaten (bis zu 30 je
   Rubrik) gehen in einen einzigen LLM-Aufruf, der strukturiertes JSON
   zurückgibt: was hervorgehoben wird, was nur erwähnt, und zu jedem
   Hauptbeitrag eine Einordnung in Alltagssprache.
4. **Veröffentlichen** — die Ausgabe wird als `digests/<datum>.json` gespeichert,
   die ganze Seite aus allen gespeicherten Ausgaben neu gebaut, und GitHub Pages
   liefert sie aus.

## Was dabei herauskommt

| Adresse | |
|---|---|
| `/` | die Ausgabe von heute |
| `/archive/` | alle früheren Ausgaben, neueste zuerst |
| `/archive/<datum>.html` | eine Seite je Ausgabe |
| `/feed.xml` | Atom-Feed — in einem RSS-Reader abonnieren und benachrichtigt werden |

Jede Rubrik hat zwei Stufen, man bekommt also Tiefe bei dem, was zählt, und sieht
trotzdem alles Übrige. Zielwert sind **drei bis vier Minuten Lesezeit**.

| Rubrik | Hauptbeiträge | „Außerdem notiert“ |
|---|---|---|
| Neubau & Immobilien | bis zu 4 | bis zu 5 |
| Konzerte, Kino & Comedy | bis zu 5 | bis zu 6 |
| Sport | bis zu 3 | bis zu 4 |
| Messen & Feste | bis zu 3 | bis zu 4 |
| Frankfurt & Infrastruktur | bis zu 4 | bis zu 6 |
| Peking & China | bis zu 3 | bis zu 4 |

Das sind Deckel, keine Zielvorgaben — der Prompt verbietet das Auffüllen, ein
Beitrag muss sich seinen Platz also verdienen, und ein ruhiger Tag ergibt eine
ehrlich kurze Ausgabe.

**„Außerdem notiert“ ist keine reine Überschriftenliste** — jeder Eintrag trägt
einen Satz dazu, was der Beitrag tatsächlich meldet, und einen eigenen Link.

**Die sechs Rubriken sind fest und unabhängig.** Alle sechs erscheinen in jedem
Reiter, in derselben Reihenfolge. Eine Rubrik ohne Beiträge in diesem Zeitraum
liest sich schlicht als *„Nichts in diesem Zeitraum.“* statt zu verschwinden —
sonst bliebe offen, ob es nichts gibt oder ob etwas kaputt ist. Rubriken borgen
nicht voneinander, jede wird nur an ihren eigenen Kandidaten gemessen.

**Sport wird oft leer sein, und das ist beabsichtigt.** Damentennis und
-volleyball in Deutschland sind ein schmales Feld — im Tennis im Wesentlichen
Stuttgart, Berlin und Bad Homburg, dazu Volleyball-Bundesliga, Pokalfinale und
Länderspiele. Der Prompt verbietet ausdrücklich, ein Auslandsturnier oder einen
Ergebnisbericht aufzunehmen, nur damit dort etwas steht. Eine leere Sportrubrik
ist das ehrliche Ergebnis, keine Störung.

Die Seite folgt der Hell-/Dunkel-Einstellung des Systems und ist auf dem Handy
lesbar.

## Die Reiter

Jeder Beitrag bekommt vom Modell ein Feld `horizon`, das entscheidet, unter
welchem Reiter er landet. Maßstab ist, **wann das Ereignis für den Leser
stattfindet**, gemessen am heutigen Datum — nicht, wann die Meldung erschienen
ist.

| Reiter | Was hineingehört |
|---|---|
| **Aktuell** | läuft gerade, war gerade, oder beginnt in den nächsten sieben Tagen. Dazu alles ohne künftigen Termin: Verkehrsmeldungen, beschlossene Entscheidungen, Marktberichte, bereits erfolgte Eröffnungen. Auch der Rückfall im Zweifel. |
| **In den nächsten Wochen** | etwa eine Woche bis drei Monate voraus — ein Fest im nächsten Monat, eine Messe im Herbst, ein Verkaufsstart in sechs Wochen. |
| **In den nächsten Monaten** | mehr als etwa drei Monate voraus — eine Tournee im nächsten Jahr, ein Bauvorhaben mit Bezug in einigen Jahren. |

Bei Immobilien zählt der **nächste Schritt, der den Leser betrifft**: Ein
Verkaufsstart nächste Woche steht unter „Aktuell“, auch wenn die Wohnungen erst
2029 bezugsfertig sind. Bei Konzerten zählt der Auftrittstermin — ein Vorverkauf,
der in den nächsten Tagen startet, zieht den Beitrag aber nach „Aktuell“, weil
dann gehandelt werden muss. Im Sport gilt dasselbe; dort liegt der Schwerpunkt
naturgemäß auf **„In den nächsten Monaten“**, denn genau dafür gibt es die
Rubrik — ein Turnier im nächsten Frühjahr will früh gebucht werden.

Die Zahl neben jedem Reiter zeigt, wie viele Beiträge dort liegen. Voreingestellt
ist der erste Reiter, der überhaupt etwas enthält — an einem Tag ohne aktuelle
Termine öffnet die Seite also nicht auf einer leeren Ansicht.

**Die Reiter kommen ohne JavaScript aus.** Sie sind drei Radiobuttons, deren
`:checked`-Zustand per CSS das passende Panel einblendet. Damit bleibt die Seite
eine reine Textdatei, und die Pfeiltasten schalten die Reiter von Haus aus
weiter. Ein Nebeneffekt: Die Textsuche des Browsers findet nur, was im gerade
sichtbaren Reiter steht.

Die Obergrenzen aus der Tabelle oben gelten **je Rubrik, nicht je Reiter**. Der
Prompt verbietet ausdrücklich, Beiträge auf die Zeiträume zu verteilen, damit ein
Reiter voller wirkt.

## Farbschema

Der Aufbau ist von [frankfurtflyer.de](https://frankfurtflyer.de) übernommen
(dort das WordPress-Theme *MH Magazine Lite*): ein rotes Leitmotiv, Anthrazit
`#2a2a2a` als Schriftfarbe, Seitenhintergrund `#f7f7f7`, Linien `#ebebeb`.
Übernommen wurde **nur die Palette** — Layout, Typografie und Aufbau der Seite
sind unverändert die dieses Projekts.

Die Buntwerte sind gegenüber der Vorlage deutlich entsättigt. Deren Signalrot
`#e64946` war gleichzeitig Markenfarbe, erste Rubrikfarbe und Hintergrund des
aktiven Reiters und wurde in dieser Häufung zu laut. Farbe trägt jetzt nur noch
die Rubrikzuordnung, und zwar in schmalen Bauteilen — Trennlinie unter der
Rubriküberschrift, 4px-Kante der Karte, Linkfarbe:

| Rubrik | hell | dunkel |
|---|---|---|
| Neubau & Immobilien | `#9e4a48` | `#d1817f` |
| Konzerte, Kino & Comedy | `#8a5273` | `#c79ab4` |
| Sport | `#3f6b5e` | `#8fbdae` |
| Peking & China | `#4a5f85` | `#9db3d4` |
| Messen & Feste | `#8a6a3d` | `#c2a577` |
| Frankfurt & Infrastruktur | `#4f4f4f` | `#c8c8c8` |

**Die Tag-Plaketten sind neutral grau.** Vorher hatte jedes der 13 Tags eine
eigene Farbe — grün, bernstein, türkis, violett, blau —, was zusammen mit den
vier Rubrikfarben einen kompletten Farbkreis auf einer Seite ergab. Die Rubrik
steht schon an der Kartenkante und in der Überschrift; das Tag muss sie nicht
ein drittes Mal codieren, sein Text sagt ohnehin, worum es geht. Wer eine
einzelne Rubrik wieder abheben will, überschreibt ihr `--tag-<key>-bg`/`-fg`-Paar
in `render.py` mit festen Werten statt mit `var(--tag-bg)`.

Alle Rubrikfarben erreichen auf ihrem Grund mindestens 4.5:1 — sie tragen Text
(Rubriküberschrift, „Weiterlesen bei"-Zeile), nicht nur Ränder.

Alles davon steht als CSS-Custom-Property im `CSS`-Block in `render.py`, jeweils
einmal für hell und einmal für dunkel.

## Loslegen

Ungefähr 15 Minuten, das meiste davon Warten auf GitHub. Man braucht ein
GitHub-Konto und etwa 5 € OpenRouter-Guthaben für das erste Jahr.

### Schritt 1 — OpenRouter-API-Key holen

1. Auf [openrouter.ai](https://openrouter.ai) anmelden.
2. Guthaben aufladen unter [openrouter.ai/credits](https://openrouter.ai/credits).
   **5 € reichen reichlich.** (OpenRouter berechnet beim Aufladen ~5,5 %, aus 5 €
   werden also etwa 4,72 € nutzbares Guthaben.)
3. Auf [openrouter.ai/keys](https://openrouter.ai/keys) → **Create Key**, Name
   zum Beispiel `allgemeine-news`, und den Wert kopieren. Er beginnt mit
   `sk-or-v1-`.

   **Jetzt kopieren** — OpenRouter zeigt einen Key genau einmal. Ist er weg,
   löscht man ihn und legt einen neuen an.

### Schritt 2 — Den Code in ein eigenes GitHub-Repository legen

Ein leeres Repository auf GitHub anlegen (**New repository**, ohne README, ohne
.gitignore), dann aus diesem Ordner:

```bash
git remote set-url origin https://github.com/<benutzername>/<repo>.git
git add -A
git commit -m "Initial commit"
git push -u origin main
```

> Zeigt `git remote -v` noch auf ein anderes Repository, ist die erste Zeile
> Pflicht — sonst landet der Code im falschen Projekt.

**Das Repository öffentlich machen.** Im kostenlosen GitHub-Plan funktioniert
Pages nur aus öffentlichen Repositories; aus einem privaten zu veröffentlichen
verlangt GitHub Pro (~4 $/Monat, also ~48 $/Jahr — mehr als alles andere hier
zusammen). Auf der Seite stehen ausschließlich Links auf öffentliche
Nachrichtenartikel, es ist also nichts Schützenswertes darin. Der API-Key liegt
in den Actions-Secrets, die auch in einem öffentlichen Repository privat bleiben.

Ein öffentliches Repository hat außerdem unbegrenzte Actions-Minuten; private
zehren an einem Kontingent von 2.000 Minuten im Monat (diese Anwendung braucht
rund 60).

### Schritt 3 — Den API-Key als Repository-Secret hinterlegen

Im Repository auf GitHub: **Settings → Secrets and variables → Actions →
New repository secret**

| Feld | Wert |
|---|---|
| Name | `OPENROUTER_API_KEY` |
| Secret | der `sk-or-v1-...`-Key aus Schritt 1 |

**Add secret** klicken. Das ist die einzige Zugangsinformation, die das Projekt
braucht — alles Weitere läuft über den `GITHUB_TOKEN`, den Actions automatisch
bereitstellt.

> Ein Secret ist nur schreibbar: GitHub zeigt es nie wieder an, und in den Logs
> taucht es nicht auf. Zum Ändern überschreibt man es an derselben Stelle.

### Schritt 4 — GitHub Pages einschalten

**Settings → Pages → Build and deployment → Source**, und dort
**GitHub Actions** wählen.

> Diesen Schritt übersieht man leicht. Es geht um die *Quelle*, nicht um einen
> Branch — also **nicht** „Deploy from a branch“ auswählen. Lässt man ihn aus,
> läuft alles durch und nur der letzte Deploy-Schritt scheitert.

### Schritt 5 — Einmal von Hand starten

Tab **Actions** → **Täglicher Nachrichtenüberblick** in der linken Spalte →
**Run workflow** → **Run workflow**.

Das dauert etwa eine Minute. Ein gesundes Protokoll sieht so aus:

```
Verwendetes Modell: openai/gpt-5.6-luna
Gesammelt: 3 Neubau & Immobilien, 12 Konzerte, Kino & Comedy, 7 Sport, 14 Messen & Feste, 25 Frankfurt & Infrastruktur
LLM-Aufruf: model=openai/gpt-5.6-luna rein=8500 raus=2100 Token
digests/2026-08-08.json gespeichert
site/ mit 1 Ausgabe(n) gebaut
Die Seite erscheint unter https://<du>.github.io/<repo>/
```

### Schritt 6 — Die eigene Seite öffnen

`https://<benutzername>.github.io/<repo>/`

Das erste Deployment braucht ein paar Minuten, bis es live ist. Die Adresse steht
auch auf der Seite des Workflow-Laufs und unter **Settings → Pages**.

Das war es — ab jetzt läuft es täglich um 05:00 UTC von selbst. Am ersten Tag
gibt es eine Ausgabe, das Archiv füllt sich nach und nach.

### Optional — benachrichtigen lassen

Die Seite veröffentlicht einen Atom-Feed unter `/feed.xml`. Diese Adresse in
einen beliebigen RSS-Reader (Feedly, NetNewsWire, Thunderbird, Outlook) eintragen,
dann kommen neue Ausgaben von selbst.

### Optional — die Uhrzeit ändern

Die `cron`-Zeile in `.github/workflows/daily-digest.yml` bearbeiten. Sie ist in
UTC und folgt der Sommerzeit nicht:

```yaml
- cron: "0 5 * * *"   # 05:00 UTC = 06:00 im Winter, 07:00 im Sommer
```

## Das Modell wählen

Standard ist `openai/gpt-5.6-luna`. Zum Ändern setzt man eine Repository-**Variable**
namens `MODEL` (Settings → Secrets and variables → Actions → Tab *Variables*)
oder ändert `MODEL` in `configuration.py`. Die Variable gewinnt.

**Warum nicht das Budget ausreizen?** Diese Aufgabe ist Auswahl und kurzes
redaktionelles Schreiben, kein schweres Schlussfolgern. Über die Qualität
entscheiden hier das Befolgen der Anweisungen (Obergrenzen, Tag-Liste, das Verbot
aufzufüllen, vor allem aber der Ortsbezug) und natürliches Deutsch in der
Einordnung. Spitzenmodelle sind für ein anderes Problem gebaut und bringen hier
kaum noch etwas.

Kosten **pro Jahr** für diese Last (~8,5K rein / ~2,1K raus, einmal täglich),
gerechnet aus Zeichenzahlen mit den Listenpreisen von OpenRouter:

| Slug | $/Jahr | |
|---|---|---|
| `openai/gpt-5.6-luna` | **1,50 – 2,80** | der Standard — günstig, schnell, nativer JSON-Modus |
| `anthropic/claude-haiku-4.5` | 6,00 – 11,00 | sehr guter deutscher Stil, hält sich streng an Vorgaben |
| `openai/gpt-5.4-mini` | 5,20 – 9,50 | ebenso vertretbar |
| `google/gemini-3-flash-preview` | 3,50 – 6,40 | günstigster der wirklich guten Klasse |
| `openai/gpt-5` | ~14,00 | Spitzenpreis für eine Zusammenfassungsaufgabe |

Die Spanne reicht von einem typischen Tag bis zu einer randvollen Ausgabe. Sie
liegt über den Werten des Vorgängerprojekts, weil sechs Rubriken statt drei mehr
Kandidaten und mehr Ausgabetext bedeuten und deutscher Text je Zeichen mehr Token
braucht als englischer.

Den OpenRouter-Slug exakt übernehmen, samt Zeichensetzung —
`openai/gpt-5.6-luna` hat einen **Punkt**, keinen Bindestrich. Nachsehen unter
[openrouter.ai/models](https://openrouter.ai/models); ein falscher Slug ergibt
einen 404, und der Lauf sagt das auch so.

## Zeitfenster, oder: warum nicht überall 24 Stunden

Anders als bei einem Techniknewsticker ist die Nachrichtenmenge hier sehr
ungleich verteilt. Die Lokalpresse liefert jeden Tag; ein neues Bauvorhaben oder
eine Konzertankündigung kommt aber nur alle paar Tage. Ein 24-Stunden-Fenster für
alle Rubriken hielte die halbe Seite dauerhaft leer.

| Rubrik | Rückblick | Warum |
|---|---|---|
| Neubau & Immobilien | 168 h (7 Tage) | Bauvorhaben werden selten gemeldet; ein Wochenfenster fängt sie ein |
| Konzerte, Kino & Comedy | 120 h (5 Tage) | Ankündigungen kommen schubweise, oft am Wochenanfang |
| Sport | 336 h (14 Tage) | das schmalste Feld überhaupt — eine Turnierankündigung darf nicht durchrutschen |
| Peking & China | 336 h (14 Tage) | bewegt sich über Wochen; in 7 Tagen blieben nach Abzug der Konjunkturmeldungen kaum drei Kandidaten |
| Messen & Feste | 168 h (7 Tage) | stark saisonal — monatelang nichts, dann viel |
| Frankfurt & Infrastruktur | 24 h | vier Redaktionen liefern täglich mehr als genug |

Die Entdoppelung sorgt dafür, dass ein weiteres Fenster nichts wiederholt — es
fügt nur Abdeckung hinzu. Ändern lässt sich das ohne Codeänderung über
Repository-Variablen: `MAX_AGE_HOURS_IMMOBILIEN`, `MAX_AGE_HOURS_EVENTS`,
`MAX_AGE_HOURS_SPORT`, `MAX_AGE_HOURS_MESSEN`, `MAX_AGE_HOURS_STADT`,
`MAX_AGE_HOURS_PEKING`.

**`DEDUP_EDITIONS` in `main.py` muss mehr Tage abdecken als das breiteste
Fenster.** Das ist Sport mit 14 Tagen, der Wert steht deshalb auf 16 (früher 9).
Wer ein Fenster weiter aufzieht, muss ihn mitziehen, sonst erscheint ein Beitrag
nach Ablauf der Sperre ein zweites Mal.

**Ausgefallene Läufe werden automatisch aufgeholt.** Geplante Actions-Läufe
verzögern sich manchmal oder fallen unter Last aus. Fehlt die Ausgabe von
gestern, verbreitert sich jedes Fenster um einen Tag, damit nichts still
verlorengeht.

## Woher der Herausgeber unter jedem Beitrag kommt

Viele Quellen sind Google-News-Suchfeeds, deren Links auf `news.google.com`
zeigen und weiterleiten. Ohne Gegenmaßnahme stünde unter jedem zweiten Beitrag
„Weiterlesen bei news.google.com“. Solche Feeds liefern den echten Herausgeber
aber in einem `<source>`-Element mit; `main.py` liest ihn dort aus, hängt ihn an
den Kandidaten und ordnet ihn nach dem LLM-Aufruf wieder dem passenden Beitrag
zu. Unter dem Beitrag steht deshalb „Weiterlesen bei FAZ“.

Dass die Zuordnung nach dem Modellaufruf über den Link passiert und nicht vom
Modell abgeschrieben wird, ist Absicht: abgetippt wäre der Herausgeber
irgendwann falsch, nachgeschlagen ist er es nie. Google News hängt den Namen
außerdem an jede Überschrift („… – FNP“); das wird abgeschnitten, weil es sonst
doppelt dasteht.

## Sicherheit

Die Ausgabe des Modells wird als ungeprüfte Eingabe behandelt, weil sie das ist:

- **Jede URL wird gegen die Kandidaten geprüft, die dem Modell tatsächlich
  vorlagen.** Diese Links landen in einem `href` auf einer öffentlichen Seite,
  eine `javascript:`- oder `data:`-URL wäre also ein XSS-Einfallstor. Modelle
  erfinden außerdem plausibel aussehende URLs, was tote Links veröffentlichen
  würde. Was sich nicht zuordnen lässt, verliert den Link und behält den Text.
- **Aller Modelltext wird HTML-escaped**, in jeder Ausgabe — Seite, Archiv und
  Atom-Feed.
- **Das Tag steht auf einer Positivliste**, bevor es in ein `style`-Attribut
  gelangt; ein unbekannter Wert fällt auf die neutrale Darstellung zurück.
- **RSS-Inhalte sind im Prompt als ungeprüft deklariert.** Jeder kann einen
  RSS-Beitrag veröffentlichen, ein Feedeintrag könnte also Prompt Injection
  versuchen. Der System-Prompt sagt dem Modell, dass Kandidatentext Daten sind
  und niemals Anweisungen.
- **Dateinamen von Ausgaben müssen ein reines ISO-Datum sein**, bevor sie zu
  Ausgabepfaden werden.

## Warum OpenRouter

Ein Key erreicht alle Anbieter, es gibt also nie ein zweites Konto einzurichten.
Es kommt kein Aufschlag pro Token dazu (die ~5,5 % fallen beim Aufladen an), neue
Modelle sind am Erscheinungstag verfügbar, und bei einer Störung wird automatisch
auf einen anderen Anbieter ausgewichen.

## Lokal ausführen

```powershell
pip install -r requirements.txt
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
python main.py
```

Das schreibt `digests/` und `site/` genau wie in CI — `site/index.html` im
Browser öffnen, um Gestaltungsänderungen anzusehen. Veröffentlicht wird nichts.

## Wenn etwas schiefgeht

Der Lauf erklärt sich selbst, statt einen Traceback auszukippen:

| Meldung im Actions-Protokoll | Bedeutung |
|---|---|
| `OPENROUTER_API_KEY ist nicht gesetzt` | Secret fehlt oder heißt anders — scheitert in unter einer Sekunde, bevor irgendetwas geholt wird |
| `OpenRouter hat den API-Key abgelehnt` | Key ist falsch oder zurückgezogen |
| `Das OpenRouter-Guthaben ist aufgebraucht` | Aufladen unter [openrouter.ai/credits](https://openrouter.ai/credits) |
| `OpenRouter kennt kein Modell namens ...` | Falscher Slug — meist falsche Zeichensetzung oder fehlendes `anbieter/`-Präfix |
| `Für diese Rubrik(en) fehlen Feeds` | Ein Schlüssel in `SECTIONS` (`render.py`) hat keinen Eintrag in `FEEDS` (`configuration.py`) |
| `Das Modell hat kein JSON geliefert` | Das gewählte Modell hat keinen verlässlichen JSON-Modus; eines aus der Tabelle oben nehmen |
| `N erfundene(n) Link(s) entfernt` | Normal und harmlos — eine halluzinierte URL wurde vor der Veröffentlichung entfernt |
| `... kein YYYY-MM-DD-Digest` | Eine verirrte Datei in `digests/`; kann gelöscht werden |
| `WARNUNG: <Feed> nicht lesbar` | Ein Feed ist gerade tot; die Ausgabe erscheint ohne ihn |
| Deploy-Schritt scheitert beim ersten Lauf | Pages-Quelle steht nicht auf **GitHub Actions** (Schritt 4) |

## Kosten

**Rund 1,50 bis 2,80 $ im Jahr, alles zusammen.** Das ist das LLM; alles Übrige
ist kostenlos.

| | Kosten |
|---|---|
| GitHub Actions | **kostenlos.** Unbegrenzte Minuten bei öffentlichen Repositories. (Ein privates zehrt an 2.000 freien Linux-Minuten im Monat; diese Anwendung braucht ~60.) |
| GitHub Pages | **kostenlos** — bei einem **öffentlichen** Repository. Private brauchen GitHub Pro, ~48 $/Jahr. |
| Nachrichtenquellen | **kostenlos.** Reines RSS, keine Keys, keine Kontingente. |
| LLM | **~1,50–2,80 $/Jahr.** Ein Aufruf pro Tag. |

Das sind Schätzungen aus Zeichenzahlen (~3,7 Zeichen je Token für deutschen
Text). Nach einer Woche den echten Wert unter
[openrouter.ai/activity](https://openrouter.ai/activity) nachsehen. Ein Aufladen
über 5–10 € deckt ein Jahr bequem ab.

## Anpassen

**`configuration.py` enthält, worum es geht** — Modell, Quellen, Aufbewahrung.
Nur einfache Werte, kein Code, dort kann also nichts kaputtgehen.

| Ändern | Einstellung in `configuration.py` |
|---|---|
| Das Modell | `MODEL` |
| Welche Feeds gelesen werden | `IMMOBILIEN_FEEDS`, `EVENT_FEEDS`, `SPORT_FEEDS`, `MESSE_FEEDS`, `STADT_FEEDS`, `PEKING_FEEDS` und die Zuordnung `FEEDS` |
| Wie viele Ausgaben bleiben | `KEEP_DIGESTS` (30) |

Alles Weitere steht neben dem Code, der es benutzt:

| Ändern | Wo |
|---|---|
| Was als interessant gilt, das Leserprofil, der Radius je Rubrik | `SYSTEM_PROMPT` in `main.py` — der Block `RADIUS:` |
| Wie viele Beiträge je Rubrik | der Block `Umfang:` innerhalb von `SYSTEM_PROMPT` |
| Wo die Grenzen zwischen den Reitern liegen | der Block `ZEITHORIZONT:` innerhalb von `SYSTEM_PROMPT` |
| Wie weit jede Rubrik zurückblickt | `SECTION_TUNING` oben in `main.py` |
| Wie viele Kandidaten das Modell erreichen | derselbe Block — `MAX_CANDIDATES_PER_SECTION`, `per_feed` |
| Wie weit die Entdoppelung zurückreicht | derselbe Block — `DEDUP_EDITIONS` (16) |
| Seitenname, Rubriknamen, Tag-Beschriftungen | oben in `render.py` — `SITE_TITLE`, `SECTIONS`, `TAG_LABELS` |
| Namen und Reihenfolge der Reiter | `HORIZONS` in `render.py` |
| Farben, Schrift, Layout | die Konstante `CSS` in `render.py` |

Drei Dinge, die man wissen sollte:

- **Einen Feed hinzuzufügen ist ungefährlich.** Es gibt keinen Stichwortfilter —
  das LLM entscheidet über Relevanz, im schlimmsten Fall wird eine neue Quelle
  also nie ausgewählt. Für ein neues Thema reicht eine weitere
  Google-News-Zeile mit anderem Suchbegriff.
- **Eine Rubrik hinzuzufügen berührt drei Dateien** — so ist „Sport“ entstanden:
  einen Eintrag in `SECTIONS` (`render.py`), eine Farbregel `.section.<schlüssel>`
  samt Custom-Property im `CSS`-Block darunter, einen Eintrag in `FEEDS`
  (`configuration.py`), einen in `SECTION_TUNING` (`main.py`) und einen Absatz im
  `SYSTEM_PROMPT` samt Zeile in der JSON-Form und den Obergrenzen. Der Rest der
  Pipeline läuft über `SECTIONS` und passt sich von selbst an; `preflight()`
  meldet fehlende Feeds, bevor Arbeit anfällt.
- **Einen Reiter hinzuzufügen ist einfacher**: ein Eintrag in `HORIZONS`
  (`render.py`) und ein Absatz im Block `ZEITHORIZONT` des `SYSTEM_PROMPT`. Das
  CSS für den Reiter erzeugt `_horizon_css()` aus der Liste. Der erste Eintrag
  muss der Reiter für die Gegenwart bleiben — er ist der Rückfall für jeden
  Beitrag, den das Modell nicht einordnet.
- **Ein Fenster über 14 Tage hinaus verlangt ein größeres `DEDUP_EDITIONS`**
  (beides in `main.py`), sonst tauchen alte Beiträge wieder auf.

Ein vollständiger Neubau läuft jeden Tag, eine Gestaltungs- oder Promptänderung
erreicht also auch jede frühere Ausgabe — nicht nur die von heute.

## Wie lange das Archiv bleibt

Die neuesten **30** Ausgaben bleiben; ältere werden aus `digests/` gelöscht und
verschwinden beim nächsten Lauf von der Archivseite. Änderbar über
`KEEP_DIGESTS` in `configuration.py` (oder eine gleichnamige
Repository-Variable); `0` behält alles für immer.

Der Wert sollte deutlich über `DEDUP_EDITIONS` (16, in `main.py`) liegen. Die
Entdoppelung liest die gespeicherten Ausgaben, eine gelöschte Ausgabe kann eine
Wiederholung also nicht mehr verhindern.
