# Uploading this repository with raw data to GitHub and Zenodo

This repository includes raw XML data so users can practice the full workflow.

## Size check

- Raw-data files included: 937
- Raw-data uncompressed size: 3.34 GB
- Largest single file: 29.1 MB

No single file in the included raw-data folder is above 100 MB.  This matters
because GitHub blocks files larger than 100 MiB and warns about files larger
than 50 MiB.  However, the repository is large, so cloning will be slower than a
code-only repository.

## Option A: GitHub contains code + raw_data folder

Use this if you want users to clone everything directly.

```bash
git init
git add README.md CITATION.cff LICENSE requirements.txt pyproject.toml .gitignore
git add src scripts docs config tests data raw_data
git commit -m "Initial TMW/TMCA analysis workflow with raw data"
git branch -M main
git remote add origin https://github.com/YOUR_USER/tmw-tmca-solidification-cracking-analysis.git
git push -u origin main
```

Then create a release:

```bash
git tag -a v1.0.0 -m "Manuscript submission version"
git push origin v1.0.0
```

## Option B: GitHub contains code; Zenodo contains raw archive

This is often easier for large raw data.

1. Upload the code repository to GitHub without `raw_data/`.
2. Upload `raw_data` or a zipped raw-data archive to Zenodo.
3. Add the Zenodo DOI to the GitHub README and to the manuscript.

Zenodo can accept large uploads; using one compressed raw-data archive is often
easier than uploading hundreds of individual files.

## Recommendation for this project

For maximum transparency, you can keep `raw_data/` in GitHub because the largest
individual file is below 50 MB.  If pushing/cloning is slow, use Option B:
GitHub for code and Zenodo for raw data.

## Data availability wording after DOI

```latex
\section*{Data availability}
The processed data, raw controller logs, and Python scripts required to reproduce
the reported \TMW\ and \TMCA\ summary metrics are available at
\color{red}{[insert repository DOI/link]}. Additional large CT volume files
and original microscopy/image-measurement files are available from the
corresponding author upon reasonable request.
```
