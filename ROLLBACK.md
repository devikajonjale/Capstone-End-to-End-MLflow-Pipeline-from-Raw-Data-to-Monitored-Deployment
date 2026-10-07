# Rollback Procedure

When a release introduces issues, you can revert to the previous Docker image that was attached to the prior GitHub release.

## Steps
1. Identify the tag of the last known-good release (e.g., `v1.0.0`).
2. Download the Docker image tarball from the release assets:
   ```powershell
   curl -L -o mlops-project.tar https://github.com/<your-repo>/releases/download/v1.0.0/mlops-project-v1.0.0.tar
   ```
3. Load the image into Docker:
   ```powershell
   docker load -i mlops-project.tar
   ```
4. Stop the currently running containers (if any):
   ```powershell
   docker compose down
   ```
5. Start the previous version:
   ```powershell
   docker compose up -d
   ```
   The `docker-compose.yml` will pull the image tag `mlops-project:<sha>` that was loaded in step 3.

## Verification
- Check the API health endpoint: `curl http://localhost:8000/health`.
- Verify that the model version displayed in the response matches the expected previous version.
- Ensure Grafana dashboards show metrics from the rolled-back service.

---
*Prepared by Antigravity assistant.*
