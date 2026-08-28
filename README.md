# brain-control-plane

Autoria Sofia, KB/RAG, GraphBundle, assets, campanhas, personas e APIs administrativas.
Extraido de `brain-plataform` no SHA `b6ee5edc884e233cc0ff41798f4c19239e04fd88`.

Deploy nao executa migrations. Readiness exige schema minimo 130 e `BRAIN_DB_JWT`
com claim `role=brain_control_plane`; `service_role` e recusada. Operacoes de
journey usam `BRAIN_RUNTIME_URL` e `AI_BRAIN_WEBHOOK_TOKEN` para chamar
`/internal/v1/*`, sem escrever diretamente o dominio do runtime.
