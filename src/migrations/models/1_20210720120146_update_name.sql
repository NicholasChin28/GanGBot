-- upgrade --
ALTER TABLE "role" RENAME COLUMN "playsound_permission" TO "upload_playsound";
-- downgrade --
ALTER TABLE "role" RENAME COLUMN "upload_playsound" TO "playsound_permission";
