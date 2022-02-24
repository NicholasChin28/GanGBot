-- upgrade --
ALTER TABLE "playsound" ADD "extension" TEXT;
-- downgrade --
ALTER TABLE "playsound" DROP COLUMN "extension";
