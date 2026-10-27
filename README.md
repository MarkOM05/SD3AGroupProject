# AL: Agentic Lender

Group project, Year 3, 2026. Full team process: [docs/HANDBOOK.md](docs/HANDBOOK.md).
System design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Schema: [docs/schema.md](docs/schema.md)

## Quick start (needs Docker Desktop + Git)

    git clone <repo-url> && cd al-agentic-lender
    cp .env.example .env            # then fill in the keys (ask the lead)
    docker compose up -d --build
    ./scripts/smoke-test.sh         # checks every service answers

| What              | URL                          |
|-------------------|------------------------------|
| AL-Web            | http://localhost:3000        |
| AI engine + docs  | https://sd3agroupproject.onrender.com/docs#/ |
| Local EVM (RPC)   | http://localhost:8545        |
| Ollama            | http://localhost:11434       |

## Folders

    mobile/       AL-Mobile (Android Studio project)
    web/          AL-Web (React)
    ai-engine/    ML valuation + agent committee
    core/         FastAPI
    blockchain/   Hardhat + Solidity
    firebase/     Firestore rules + emulator config
    docs/         handbook, architecture, decisions
    scripts/      helper scripts
    secrets/      local keys (gitignored)

AL-Mobile is not in Docker: open `mobile/` in Android Studio. The emulator
reaches your PC at http://10.0.2.2:8000.
