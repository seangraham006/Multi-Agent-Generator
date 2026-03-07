multi-agent-generator/
│
├── README.md
├── docker-compose.yml
├── .env
│
├── docs/
│   ├── architecture.md
│   ├── event_schema.md
│   ├── database.md
│   └── dev_rules.md
│
├── config/
│   ├── infra.yaml
│   └── agents.yaml
│
├── services/
│   ├── villager-agent/
│   │   ├── app/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── memory-controller/
│       ├── app/
│       ├── Dockerfile
│       └── requirements.txt
│
├── shared/
│   ├── events/
│   │   └── schema.py
│   └── utils/
│
└── infrastructure/
    └── postgres/
        └── init.sql