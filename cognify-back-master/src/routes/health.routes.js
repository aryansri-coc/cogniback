const router = require("express").Router();
const { verifyToken } = require("../middleware/auth.middleware");
const prisma = require("../config/prisma");
const axios = require("axios");

/* 🔥 FULL AI SYNC FLOW */
router.post("/sync", verifyToken, async (req, res) => {
  try {
    const data = req.body;

    // 1️⃣ Store Health Data (Advanced Structure)
    const savedHealthData = await prisma.healthData.create({
      data: {
        userId: req.user.userId,
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

    // 2️⃣ TEMP MOCK ML RESPONSE (for testing)
    const mlResult = {
      cognitiveIndex: 78,
      healthStatus: "Stable",
      statusColor: "#4CAF50",
      predictions: {
        stabilityScore: 0.82,
        fatigueRisk: "Low",
        neuroDeclineProbability: 0.12,
      },
      anomalies: [],
      aiInsights: ["Sleep pattern stable."],
    };

    // 3️⃣ Store AI Prediction
    await prisma.aiPrediction.create({
      data: {
        userId: req.user.userId,
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

    // 4️⃣ Send Response Back
    res.json({
      status: "success",
      data: {
        ...mlResult,
        lastSync: new Date().toISOString(),
      },
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Health sync failed" });
  }
});

/* 📊 Get Latest AI Prediction */
router.get("/latest", verifyToken, async (req, res) => {
  try {
    const prediction = await prisma.aiPrediction.findFirst({
      where: { userId: req.user.userId },
      orderBy: { createdAt: "desc" },
    });

    res.json(prediction);
  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error fetching latest prediction" });
  }
});

/* 📅 Get All Health History (with optional date filter) */
router.get("/history", verifyToken, async (req, res) => {
  try {
    const { from, to } = req.query;

    const filters = { userId: req.user.userId };

    if (from || to) {
      filters.timestamp = {};
      if (from) filters.timestamp.gte = new Date(from);
      if (to) filters.timestamp.lte = new Date(to);
    }

    const history = await prisma.healthData.findMany({
      where: filters,
      orderBy: { timestamp: "desc" },
    });

    res.json({
      total: history.length,
      history,
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error fetching health history" });
  }
});

/* 🔍 Get Single Health Record by ID */
router.get("/history/:id", verifyToken, async (req, res) => {
  try {
    const record = await prisma.healthData.findUnique({
      where: { id: req.params.id },
    });

    if (!record) {
      return res.status(404).json({ message: "Record not found" });
    }

    // Make sure user can only access their own records
    if (record.userId !== req.user.userId) {
      return res.status(403).json({ message: "Unauthorized" });
    }

    res.json(record);

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error fetching record" });
  }
});


/* 🤖 Get All AI Predictions */
router.get("/predictions", verifyToken, async (req, res) => {
  try {
    const { from, to } = req.query;

    const filters = { userId: req.user.userId };

    if (from || to) {
      filters.createdAt = {};
      if (from) filters.createdAt.gte = new Date(from);
      if (to) filters.createdAt.lte = new Date(to);
    }

    const predictions = await prisma.aiPrediction.findMany({
      where: filters,
      orderBy: { createdAt: "desc" },
    });

    res.json({
      total: predictions.length,
      predictions,
    });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Error fetching predictions" });
  }
});

module.exports = router;