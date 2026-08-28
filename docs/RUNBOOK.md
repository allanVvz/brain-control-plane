# Deploy and rollback

Build by immutable digest. Deploy only the inactive slot, require `/health/ready`,
then switch the gateway by a graceful reload and drain the old slot. Never run a
migration from this repository. Rollback switches to the prior manifest digest.
Graph publication additionally requires persona-scoped pause, shadow Validator,
checksum/proof review, atomic activation, and a separately authorized resume.
