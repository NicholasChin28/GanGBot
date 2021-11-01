-- upgrade --
ALTER TABLE "playsound" DROP COLUMN "file_location";
-- downgrade --
ALTER TABLE "playsound" ADD "file_location" TEXT NOT NULL;
