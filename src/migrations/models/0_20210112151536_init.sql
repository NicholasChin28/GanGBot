-- upgrade --
CREATE TABLE IF NOT EXISTS "vote" (
    "message_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "completed" BOOL NOT NULL  DEFAULT False,
    "time" TIMESTAMPTZ NOT NULL,
    "message" TEXT NOT NULL,
    "options" JSONB NOT NULL,
    "votes" JSONB
);
COMMENT ON TABLE "vote" IS 'This table contains the votes casted';
CREATE TABLE IF NOT EXISTS "guild" (
    "message_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "channel_id" BIGINT NOT NULL,
    "completed" BOOL NOT NULL  DEFAULT False,
    "time" TIMESTAMPTZ NOT NULL,
    "message" TEXT NOT NULL,
    "options" JSONB NOT NULL,
    "votes" JSONB
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
