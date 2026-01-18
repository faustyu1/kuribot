---
description: Start KuriBot for the first time (interactive login)
---

To start KuriBot and perform the terminal login, follow these steps:

1. Ensure your `.env` file has `API_ID` and `API_HASH`.
2. Run the interactive setup:
// turbo
```bash
docker-compose run kuribot
```

Follow the prompts in the terminal to enter your phone number and code. Once the bot says "Bot started", you can stop it with `Ctrl+C` and then run it in background:

3. Start in background:
// turbo
```bash
docker-compose up -d
```
