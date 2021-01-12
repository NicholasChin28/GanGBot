-- upgrade --
DROP TABLE IF EXISTS "guild";
-- downgrade --
CREATE TABLE IF NOT EXISTS "guild" (
    "message_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "completed" BOOL NOT NULL  DEFAULT False,
    "time" TIMESTAMPTZ NOT NULL,
    "message" TEXT NOT NULL,
    "options" JSONB NOT NULL,
    "votes" JSONB
);;
