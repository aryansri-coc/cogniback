const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

const USER_ID = "47b4a050-2d3a-4085-8e80-dfd5b47e6ff4"; // aryan@cognify.com

function randomBetween(min, max) {
  return Math.random() * (max - min) + min;
}

function randomInt(min, max) {
  return Math.floor(randomBetween(min, max));
}

async function main() {
  console.log("🌱 Seeding 60 days of health data...");

  // Clear existing health data for this user
  await prisma.healthData.deleteMany({ where: { userId: USER_ID } });
  await prisma.aiPrediction.deleteMany({ where: { userId: USER_ID } });

  const now = new Date();

  for (let i = 60; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(now.getDate() - i);
    date.setHours(10, 0, 0, 0);

    // Gradual slight decline in some metrics over 60 days (realistic for cognitive study)
    const declineFactor = i / 60; // 1.0 at day 60, 0.0 at today

    await prisma.healthData.create({
      data: {
        userId:           USER_ID,
        timestamp:        date,
        // Vitals
        steps:            randomInt(3000 + declineFactor * 2000, 8000 + declineFactor * 2000),
        heartRateAvg:     randomInt(65, 90),
        hrvSdnnMs:        parseFloat(randomBetween(30 + declineFactor * 20, 60 + declineFactor * 10).toFixed(1)),
        bloodOxygenAvg:   parseFloat(randomBetween(96, 99.5).toFixed(1)),
        // Movement
        gaitSpeedMs:      parseFloat(randomBetween(0.7 + declineFactor * 0.2, 1.1).toFixed(2)),
        stepCadence:      randomInt(90, 120),
        walkingAsymmetry: parseFloat(randomBetween(0.01, 0.08).toFixed(3)),
        // Sleep
        totalSleepHours:  parseFloat(randomBetween(5.5, 8.5).toFixed(1)),
        deepSleepHours:   parseFloat(randomBetween(0.8, 2.0).toFixed(1)),
        remSleepHours:    parseFloat(randomBetween(1.0, 2.5).toFixed(1)),
        latencyMinutes:   randomInt(8, 30),
        awakenings:       randomInt(0, 4),
        // Cognitive
        reactionTimeMs:   randomInt(250 + (1 - declineFactor) * 100, 450),
        memoryScore:      randomInt(60 + declineFactor * 20, 95),
        testType:         "daily"
      }
    });

    // Seed a matching AI prediction every 7 days
    if (i % 7 === 0) {
      await prisma.aiPrediction.create({
        data: {
          userId:                  USER_ID,
          createdAt:               date,
          cognitiveIndex:          randomInt(65 + declineFactor * 20, 90),
          healthStatus:            declineFactor > 0.5 ? "Stable" : "Monitor",
          statusColor:             declineFactor > 0.5 ? "#4CAF50" : "#FFC107",
          stabilityScore:          parseFloat(randomBetween(0.6, 0.95).toFixed(2)),
          fatigueRisk:             declineFactor > 0.7 ? "Low" : "Moderate",
          neuroDeclineProbability: parseFloat(randomBetween(0.05, 0.25).toFixed(2)),
          anomalies:               [],
          aiInsights:              [
            "Sleep quality is within normal range.",
            "Gait speed is consistent with previous week.",
            "Memory score shows stable performance."
          ],
          modelVersion:            "v1.0"
        }
      });
    }
  }

  console.log("✅ Seeded 60 days of health data!");
  console.log("✅ Seeded 9 AI predictions!");
  console.log("🎉 Done!");
}

main()
  .catch((e) => {
    console.error("❌ Seed failed:", e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
