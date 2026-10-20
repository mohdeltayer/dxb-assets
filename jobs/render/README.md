# Render jobs

One `<name>.json` per Reel for the render runner (`.github/workflows/render.yml`); the format is in `templates/render_job.py`. A push of a job file to main renders it on GitHub Actions; the runner deletes the file in the commit that adds the Reel. This README keeps the folder.
