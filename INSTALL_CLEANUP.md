# Installer den validerede oprydning på GitHub

GitHub er endnu ikke ændret: den tilsluttede integration afviste skrivning med HTTP403. Denne engangsworkflow indeholder den præcise validerede patch og genbruger repositoryets eksisterende validatorer. Ingen ZIP eller særskilt programupload er nødvendig.

1. Download `apply-reviewed-repository-cleanup.yml`.
2. Åbn `Morfindien/bubbleverse-model` på GitHub og gå til `.github/workflows/` på standardbranchen `main`.
3. Vælg **Add file → Upload files**, upload workflowen med det præcise filnavn og commit til `main`.
4. Gå til **Actions → Apply reviewed repository cleanup → Run workflow**, vælg `main`, og start den.
5. Kontrollér, at kørslen er grøn. Dens valideringsartifact indeholder audit, separate før-/efterlogs og resultat. En grøn afslutning har også verificeret, at committen faktisk findes på GitHub.

Workflowen stopper før ændringer, hvis repositoryets øvrige filer er ændret siden auditten. Den fjerner den afsluttede Q045-installer, retter testbeskrivelser og cleanup-workflowens hashkontrol, og tilføjer en strukturel provenienspost. Modellen v0.7/R000007 og grænsen Q001–Q045 bevares. Bundlen bevares, fordi en historisk provenienspost refererer til den. Forventet slutstatus er derfor PARTIAL_CLEAN.

Engangsworkflowen fjerner sig selv fra det nye commit. Git-historikken bevarer den. Den permanente **Repository cleanup**-workflow bliver bevaret.

Hvis push afvises af branchbeskyttelse eller rettigheder, sker ingen remote oprydning. Hvis andre modelændringer er landet siden den angivne inputcommit, kræves en ny audit; omgå ikke kontrollen.

## Alternativ med Git på en computer

Den separate `repository-cleanup.patch` er samme ændring uden leveringsworkflowen. Brug den kun mod inputcommit `153713357ad029f05a32a45e9189c3ae3293aff1`, efter en ny kontrol af remote HEAD. Anvend med `git apply --check repository-cleanup.patch` og derefter `git apply repository-cleanup.patch`, kør de registrerede validatorer/healthcheck/regressioner, gennemgå diffen, og commit/push strukturelt. Workflowen ovenfor udfører hele den kontrollerede kæde automatisk.

GitHub-publicering er ikke blevet testet eller påstået udført fra denne ChatGPT-session. Lokal validering og handoff-afprøvning er dokumenteret i rapporten.
