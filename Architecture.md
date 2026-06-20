## Architecture du Projet

Le projet respecte une structure stricte en couches pour assurer la separation des responsabilites et faciliter la testabilite :

```
base-fastapi-pro/
├── app/
│   ├── main.py                    # Point d'entree de l'application FastAPI
│   ├── config.py                  # Configuration et chargement des variables d'environnement
│   ├── database.py                # Connexion et gestion des clients MongoDB et Redis
│   ├── models/                    # Definitions des documents MongoDB (base, user)
│   ├── schemas/                   # Validation des donnees d'entree/sortie avec Pydantic
│   ├── repositories/              # Couche d'acces aux donnees (CRUD generique et specifique)
│   ├── services/                  # Couche logique metier (auth, user, email)
│   ├── routes/                    # Endpoints de l'API REST (auth, users, health)
│   ├── middleware/                # Middlewares (CORS, Rate Limiting, Request Logging)
│   ├── core/                      # Utilitaires securite, exceptions et dependances
│   ├── tasks/                     # Configuration Celery et definition des taches asynchrones
│   └── templates/                 # Modeles d'e-mails HTML Jinja2
├── monitoring/                    # Configurations Prometheus et Grafana
├── tests/                         # Suite de tests d'integration E2E
├── Dockerfile                     # Image Docker de l'application
├── docker-compose.yml             # Orchestration des services en mode developpement
├── docker-compose.prod.yml        # Surcharges de configuration pour la production
├── Makefile                       # Commandes d'automatisation (dev, prod, test)
└── README.md                      # Documentation du projet
```

---