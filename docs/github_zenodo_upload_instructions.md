# GitHub and Zenodo upload instructions

## Recommended release strategy

For journal submission, do not upload the full raw working archive. Upload the cleaned repository containing:

- source code in `src/`;
- command scripts in `scripts/`;
- processed CSV data in `data/processed/`;
- control-CSV templates and manifest templates;
- example CSV/manifest rows for new users;
- documentation in `docs/`;
- raw-data inventory tables, not the full raw XML/CT/photo folders.

Keep the full controller logs, CT volume files, SEM folders, and specimen-photo folders private unless the authors decide to release them. These large files can be made available on reasonable request with the required metadata.

## Create the GitHub repository

1. Create a new GitHub repository, for example:

```text
tmw-tmca-solidification-cracking-analysis
```

2. From the repository folder, run:

```bash
git init
git add .
git commit -m "Initial TMW/TMCA analysis workflow release"
git branch -M main
git remote add origin https://github.com/YOUR_USER/tmw-tmca-solidification-cracking-analysis.git
git push -u origin main
```

3. Confirm that `README.md` is readable on the GitHub repository page.

## Create a fixed release

Use a version tag for the manuscript submission version:

```bash
git tag -a v1.0.0 -m "Manuscript submission analysis workflow"
git push origin v1.0.0
```

Then create a GitHub release from tag `v1.0.0`.

## Archive with Zenodo

Preferred route:

1. Connect the GitHub repository to Zenodo.
2. Archive the GitHub release `v1.0.0`.
3. Zenodo will create a DOI for the archived release.
4. Add the DOI to:
   - the manuscript Data Availability section;
   - `README.md`;
   - `CITATION.cff`;
   - the journal submission form.

Alternative route:

1. Create a new Zenodo upload.
2. Upload this repository zip file.
3. Fill in metadata: title, authors, affiliation, keywords, license, and related manuscript information.
4. Publish the record.
5. Copy the DOI into the manuscript and repository metadata.

## Suggested manuscript data-availability wording

```latex
The processed data and Python scripts required to reproduce the reported \TMW\ and \TMCA\ summary metrics are available at \color{red}{[insert DOI/link]}. Additional raw actuator, force, temperature, image-measurement, SEM, and CT-derived files are available from the corresponding author upon reasonable request. The full raw instrument logs and CT volume files are not publicly deposited because they are large instrument-output files that require run-specific metadata and accompanying interpretation notes for correct reuse.
```
