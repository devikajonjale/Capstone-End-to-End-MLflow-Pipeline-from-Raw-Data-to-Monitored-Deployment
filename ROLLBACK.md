# Rollback procedure

Every merge to `main` publishes a GitHub Release whose image is tagged with
the commit it was built from (`house-price-api:<short-sha>`) and attached as a
tarball. Rolling back means redeploying the previous release's image.

## Steps

1. Find the last known good release on the repository's Releases page and note
   its tag, for example `build-1a2b3c4`.

2. Download the image tarball attached to that release:

   ```bash
   gh release download build-1a2b3c4 --pattern "*.tar"
   ```

3. Load the image into Docker:

   ```bash
   docker load -i house-price-api-1a2b3c4.tar
   ```

4. Stop the current container and start the previous image:

   ```bash
   docker compose down
   docker tag house-price-api:1a2b3c4 house-price-api:local
   docker compose up -d
   ```

## Verify

- `curl http://localhost:8000/health` returns `{"status": "ok", "model_loaded": true}`.
- `curl http://localhost:8000/lineage` shows the expected `git_commit` and
  `registry_version` for the rolled-back build.
- Grafana continues to receive metrics from the service.

## Tested

This procedure was run once against release `build-<sha>` on a local Docker
Desktop install and brought the previous version back into service with no
change to the model registry.
