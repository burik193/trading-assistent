# User story: Migrations on startup and frontend env in Docker

**Part:** 4 — Production expansion  
**ID:** 05-deployment-and-devops

---

## As a deployer, I want Docker Compose (or the chosen deployment path) to run database migrations on startup and I want the frontend to use the correct API URL in each environment, so that new deployments are consistent and the browser can reach the backend without CORS or URL mistakes.

## What should be done

- **Migrations on startup.** Docker Compose currently does not run database migrations when the stack starts; the README says “run migrations once after first start” (e.g. manually exec into the backend container and run `alembic upgrade head`). Add an init step or a dedicated job that runs migrations as part of startup—e.g. a script that runs before the main backend process, or an init container in Compose that runs `alembic upgrade head` and exits. New deployments (e.g. pull and up) should then have an up-to-date schema without manual steps. Document this in the README or quickstart so that deployers know migrations run automatically.

- **Frontend API URL in Docker.** The frontend container is built with `NEXT_PUBLIC_API_URL: http://localhost:8000`. When the browser runs on a different host or port (e.g. user visits the app via a reverse proxy or a different domain), this URL can be wrong—the browser would call localhost:8000 from the user’s machine, not the backend. The project should document how to set `NEXT_PUBLIC_API_URL` per environment (e.g. same-origin when behind a reverse proxy, or the public backend URL when frontend and backend are on different hosts). Optionally, provide an example in docker-compose or env.example for a typical production-like setup (e.g. empty string for same-origin proxy) so that deployers know what to configure.

## Why

- **Deployment consistency:** Automating migrations ensures every new instance starts with the correct schema and avoids “works on my machine” vs “forgot to run migrations” issues.
- **Correct behaviour in production:** The frontend must call the backend URL that the user’s browser can reach; misconfiguration leads to failed requests or CORS errors.

## Out of scope

- Adding a full CI/CD pipeline or Kubernetes manifests; only Compose and env documentation are in scope.
- Changing how the backend serves the frontend (e.g. static assets); only migration automation and frontend API URL configuration are in scope.
