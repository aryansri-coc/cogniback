const prisma = require("../config/prisma");
const axios = require("axios");

const syncHealthData = async (req, res) => {
  try {
    const data = req.body;

    // 🔹 1. Store Health Data
    const savedHealthData = await prisma.healthData.create({
      data: {
        userId: data.userId,
        timestamp: new Date(data.timestamp),

        steps: data.vitals.steps,
        heartRateAvg: data.vitals.heartRateAvg,
        hrvSdnnMs: data.vitals.hrvSdnnMs,
        bloodOxygenAvg: data.vitals.bloodOxygenAvg,

        gaitSpeedMs: data.movement.gaitSpeedMs,
        stepCadence: data.movement.stepCadence,
        walkingAsymmetry: data.movement.walkingAsymmetry,

        totalSleepHours: data.sleep.totalHours,
        deepSleepHours: data.sleep.deepSleepHours,
        remSleepHours: data.sleep.remSleepHours,
        latencyMinutes: data.sleep.latencyMinutes,
        awakenings: data.sleep.awakenings,

        reactionTimeMs: data.cognitivePerformance.reactionTimeMs,
        memoryScore: data.cognitivePerformance.memoryScore,
        testType: data.cognitivePerformance.testType,
      },
    });

    // 🔹 2. Send Same JSON to ML Model
    const mlResponse = await axios.post(
      "http://localhost:8000/predict",  // change if needed
      data
    );

    const mlResult = mlResponse.data;

    // 🔹 3. Store AI Prediction
    await prisma.aiPrediction.create({
      data: {
        userId: data.userId,
        cognitiveIndex: mlResult.cognitiveIndex,
        healthStatus: mlResult.healthStatus,
        statusColor: mlResult.statusColor,

        stabilityScore: mlResult.predictions.stabilityScore,
        fatigueRisk: mlResult.predictions.fatigueRisk,
        neuroDeclineProbability:
          mlResult.predictions.neuroDeclineProbability,

        anomalies: mlResult.anomalies,
        aiInsights: mlResult.aiInsights,

        modelVersion: "CHI_v1",
      },
    });

    // 🔹 4. Send Response Back to Android
    return res.json({
      status: "success",
      data: {
        ...mlResult,
        lastSync: new Date().toISOString(),
      },
    });

  } catch (error) {
    console.error("Health Sync Error:", error);
    return res.status(500).json({
      status: "error",
      message: "Health sync failed",
    });
  }
};

module.exports = { syncHealthData };