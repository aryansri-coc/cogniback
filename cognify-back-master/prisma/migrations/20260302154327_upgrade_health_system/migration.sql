/*
  Warnings:

  - You are about to drop the `HealthRecord` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "HealthRecord" DROP CONSTRAINT "HealthRecord_userId_fkey";

-- DropTable
DROP TABLE "HealthRecord";

-- CreateTable
CREATE TABLE "HealthData" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "timestamp" TIMESTAMP(3) NOT NULL,
    "steps" INTEGER,
    "heartRateAvg" INTEGER,
    "hrvSdnnMs" DOUBLE PRECISION,
    "bloodOxygenAvg" DOUBLE PRECISION,
    "gaitSpeedMs" DOUBLE PRECISION,
    "stepCadence" INTEGER,
    "walkingAsymmetry" DOUBLE PRECISION,
    "totalSleepHours" DOUBLE PRECISION,
    "deepSleepHours" DOUBLE PRECISION,
    "remSleepHours" DOUBLE PRECISION,
    "latencyMinutes" INTEGER,
    "awakenings" INTEGER,
    "reactionTimeMs" INTEGER,
    "memoryScore" INTEGER,
    "testType" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "HealthData_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AiPrediction" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "cognitiveIndex" INTEGER,
    "healthStatus" TEXT,
    "statusColor" TEXT,
    "stabilityScore" DOUBLE PRECISION,
    "fatigueRisk" TEXT,
    "neuroDeclineProbability" DOUBLE PRECISION,
    "anomalies" JSONB,
    "aiInsights" JSONB,
    "modelVersion" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AiPrediction_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "HealthData" ADD CONSTRAINT "HealthData_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AiPrediction" ADD CONSTRAINT "AiPrediction_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
