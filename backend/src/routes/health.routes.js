const router = require("express").Router();
const { verifyToken } = require("../middleware/auth.middleware");
const prisma = require("../config/prisma");
const { syncHealthData } = require("../controllers/health.controller");

// POST /api/health/sync
router.post("/sync", verifyToken, syncHealthData);

// GET /api/health/latest — return most recent health data + prediction
router.get("/latest", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    const latest = await prisma.healthData.findFirst({
      where: { userId },
      orderBy: { timestamp: "desc" }
    });

    const prediction = await prisma.aiPrediction.findFirst({
      where: { userId },
      orderBy: { createdAt: "desc" }
    });

    if (!latest) {
      return res.status(404).json({ status: "error", message: "No health data found" });
    }

    return res.status(200).json({
      status: "success",
      data: {
        steps:               latest.steps            ?? null,
        heartRateAvg:        latest.heartRateAvg     ?? null,
        hrvSdnnMs:           latest.hrvSdnnMs        ?? null,
        bloodOxygenAvg:      latest.bloodOxygenAvg   ?? null,
        gaitSpeedMs:         latest.gaitSpeedMs      ?? null,
        stepCadence:         latest.stepCadence      ?? null,
        walkingAsymmetry:    latest.walkingAsymmetry ?? null,
        sleepTotalHours:     latest.totalSleepHours  ?? null,
        sleepDeepHours:      latest.deepSleepHours   ?? null,
        sleepRemHours:       latest.remSleepHours    ?? null,
        sleepLatencyMinutes: latest.latencyMinutes   ?? null,
        sleepAwakenings:     latest.awakenings       ?? null,
        cognitiveIndex:      prediction?.cognitiveIndex  ?? null,
        healthStatus:        prediction?.healthStatus    ?? null,
        statusColor:         prediction?.statusColor     ?? null,
        aiInsights:          prediction?.aiInsights      ?? [],
        lastSync:            latest.timestamp
      }
    });
  } catch (error) {
    console.error("ERROR [GET /health/latest]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// GET /api/health/history
router.get("/history", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { limit = 20, offset = 0 } = req.query;

    const records = await prisma.healthData.findMany({
      where: { userId },
      orderBy: { timestamp: "desc" },
      take: parseInt(limit),
      skip: parseInt(offset),
    });

    res.json({ status: "success", data: records });
  } catch (error) {
    console.error("GET /history ERROR:", error);
    res.status(500).json({ message: "Failed to fetch health history", error: error.message });
  }
});

// GET /api/health/history/:id
router.get("/history/:id", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { id } = req.params;

    const record = await prisma.healthData.findFirst({
      where: { id, userId },
    });

    if (!record) {
      return res.status(404).json({ message: "Health record not found" });
    }

    res.json({ status: "success", data: record });
  } catch (error) {
    console.error("GET /history/:id ERROR:", error);
    res.status(500).json({ message: "Failed to fetch health record", error: error.message });
  }
});

// GET /api/health/predictions
router.get("/predictions", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    const latest = await prisma.healthData.findFirst({
      where: { userId },
      orderBy: { timestamp: "desc" },
    });

    if (!latest) {
      return res.status(404).json({ message: "No health data available for predictions" });
    }

    res.json({ status: "success", data: { predictions: latest } });
  } catch (error) {
    console.error("GET /predictions ERROR:", error);
    res.status(500).json({ message: "Failed to fetch predictions", error: error.message });
  }
});

module.exports = router;
