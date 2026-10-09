# Installér Q042-modellen selv

Du skal bruge to filer. Hele den afprøvede modelopdatering er indbygget i Python-filen; en separat patch eller ZIP er ikke nødvendig.

## Upload i GitHub

Åbn **Morfindien/bubbleverse-model** på GitHub og vælg branchen **main**.

1. Upload **install_q042_model.py** i repositoryets rod, ved siden af `README.md`. Commit filen til `main`.
2. Åbn mappen **.github/workflows** og upload **install-q042-model.yml** dér. Commit filen til `main`.
3. Åbn **Actions → Install Q042 Model → Run workflow**, vælg `main`, og start jobbet.

Behold filnavnene præcis som ovenfor. Filernes endelige stier skal være:

```text
install_q042_model.py
.github/workflows/install-q042-model.yml
```

Begge filer hører til **bubbleverse-model**. Upload dem ikke i det videnskabelige kilderepository.

## Hvad jobbet gør

Jobbet kontrollerer installationsfilens hash og det eksisterende modelgrundlag. Det tillader netop de to nye installationsfiler oven på det afprøvede input, men stopper ved andre modelændringer siden grundlaget.

Det bygger Q042 i et midlertidigt arbejdsområde og kører Q042-, formalmodel-, regressions-, integrations- og public-healthcheck-testene. Det sammenligner tidligere snapshots og de originale kildefilers hashes. Først efter grønne kontroller fast-forwardes den lokale model til **v0.4 / R000004 gennem Q042**.

Derefter publicerer dit manuelt startede GitHub-job ændringen og registrerer de faktiske Git-commit-identiteter. En publicering markeres kun verificeret, når GitHub-repositoryets observerede hoved svarer til det lokale commit. Den afsluttende kvittering ligger i:

```text
release/Q042_INSTALLATION_RESULT.json
release/MODEL_RELEASE_HANDOFF.json
```

En genkørsel kontrollerer integriteten og opretter ikke en vilkårlig ny modelversion. Et teknisk installations- eller publiceringsproblem er ikke en videnskabelig falsifikation.

Q042 bevares som dokumenteret **inkonklusiv afslutning**. Den fysiske model ændres ikke. Referencegrundlaget forbliver **BLOCKED**, det numeriske slutresultat **UNRESOLVED**, og ingen produktionsberegning genstartes. Jobbet starter ikke et nyt videnskabeligt spørgsmål.

Jeg har oprettet installationsfilerne lokalt. Jeg har ikke uploadet disse filer, startet et GitHub-job eller skrevet modelopdateringen til GitHub.

## Hvis jobbet bliver rødt

Åbn det fejlede trin i Actions. Installerens fejl begynder med `INSTALLATION_BLOCKED:`. Den bevarer egne ucommittede ændringer og stopper ved et modelgrundlag, der ikke svarer til den gennemgåede opdatering.

Hvis et `git push` bliver afvist, er lokal installation og publicering separate: jobbet kan have gennemført den lokale kontrol uden at GitHub har accepteret opdateringen. Se publiceringskvitteringen og sidste verifikation, før du kalder modellen promoveret. Repositoryets tilladelser eller regler for `main` skal tillade jobbets publicering.

## Lokal installation på en computer

Python 3.11 eller nyere og Git er nok; ingen ekstra Python-pakker skal installeres. Kør scriptet fra et rent checkout af `Morfindien/bubbleverse-model` på `main`:

```bash
python install_q042_model.py --repo .
```

Scriptet installerer og committer lokalt. Scriptet foretager ikke et push. Du publicerer selv:

```bash
git push origin HEAD:main
python install_q042_model.py --repo . --record-publication
git push origin HEAD:main
```

Kun kontrol, uden installation eller commit:

```bash
python install_q042_model.py --repo . --check
```

## Afprøvning og integritet

Installationen er testet i ni scenarier: installation efter operatørens to uploads og idempotent genkørsel; kontrol uden ændring af hoved/model; bevarelse af egne ucommittede ændringer; afvisning af et ændret modelgrundlag; afvisning af en beskadiget payload; publiceringskvittering først efter observeret remote-match; hele workflowets shell-kommandoer mod et lokalt bare testrepository; afvisning af et samtidigt branchskift på samme commit; og isoleret kontrol ved allerede installeret Q042. Alle ni bestod. Et faktisk GitHub Actions-job er ikke startet af mig.

Den medfølgende model består Q042 11/11, formalmodel 13/13, regression 11/11, offentlig healthcheck 20/20 og modelintegration 4/4. Disse tests genbruger delvist de samme kontroller og er ikke uafhængige videnskabelige beviser.

Afprøvet videnskabeligt modelinput:

```text
10fa83797b2f7740519d4e43b1bebf0a6e35bada
```

SHA256 for den indbyggede komplette patch:

```text
a8954661839b6d644c430bc47819566be8f9749749e3fbd7b25751ccc2192834
```

| Fil | SHA256 |
|---|---|
| install_q042_model.py | `4dc0dae3234b7f30ea7b055ff05cb83c969c9fc6d432cd6cbd8fe1a39f7315c2` |
| install-q042-model.yml | `4357b908eca84834c15bd23a30092a3cc7d99855d0bb8912f2e42aa35138253d` |
