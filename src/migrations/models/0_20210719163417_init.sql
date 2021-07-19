-- upgrade --
CREATE TABLE IF NOT EXISTS "playsound" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "duration" DOUBLE PRECISION NOT NULL,
    "uploader" BIGINT NOT NULL,
    "file_location" TEXT NOT NULL,
    "played" INT NOT NULL,
    "guild" BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS "role" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "role_id" BIGINT NOT NULL,
    "guild" BIGINT NOT NULL,
    "playsound_permission" BOOL NOT NULL  DEFAULT True
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
