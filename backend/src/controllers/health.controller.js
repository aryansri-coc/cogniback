const prisma = require("../config/prisma");
const axios = require("axios");

const ML_SERVICE_URL = process.env.ML_SERVICE_URL;

const syncHealthData = async (req, res) => {
  try {
    if (!req.user) {
      return res.status(401).json({ message: "Unauthorized: no user in token" });
    }

    const userId = req.user.userId;
    const data = req.body;

    const user = await prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    const profileComplete = !!user.age && !!user.sex;
    if (!profileComplete) {
      console.warn(`SYNC WARN: User ${userId} missing age/sex — using fallbacks`);
    }

    const sleep = data.sleep ?? {};
    const totalSleepHours = sleep.totalHours                        ?? null;
    const deepSleepHours  = sleep.deepSleepHours  ?? sleep.deep     ?? null;
    const remSleepHours   = sleep.remSleepHours   ?? sleep.rem      ?? null;
    const latencyMinutes  = sleep.latencyMinutes  ?? sleep.latency  ?? null;
    const awakenings      = sleep.awakenings                        ?? null;

    const healthRecord = await prisma.healthData.create({
      data: {
        userId,
        timestamp:        new Date(data.timestamp ?? Date.now()),
        steps:            data.vitals?.steps          ?? null,
        heartRateAvg:     data.vitals?.heartRateAvg   ?? null,
        hrvSdnnMs:        data.vitals?.hrvSdnnMs      ?? null,
        bloodOxygenAvg:   data.vitals?.bloodOxygenAvg ?? null,
        gaitSpeedMs:      data.movement?.gaitSpeedMs      ?? null,
        stepCadence:      data.movement?.stepCadence      ?? null,
        walkingAsymmetry: data.movement?.walkingAsymmetry ?? null,
        totalSleepHours,
        deepSleepHours,
        remSleepHours,
        latencyMinutes,
        awakenings,
        reactionTimeMs: data.cognitivePerformance?.reactionTimeMs ?? null,
        memoryScore:    data.cognitivePerformance?.memoryScore    ?? null,
        testType:       data.cognitivePerformance?.testType       ?? null,
      },
    });

    // ── ML payload — never send null for required fields ──────────────────
    const mlPayload = {
      user_id: userId,
      age:     user.age ?? 45,
      sex:     (user.sex?.toLowerCase() === "female") ? "female" : "male",
      records: [
        {
          timestamp:        data.timestamp ?? new Date().toISOString(),
          steps:            data.vitals?.steps          ?? null,
          heartRateAvg:     data.vitals?.heartRateAvg   ?? null,
          hrvSdnnMs:        data.vitals?.hrvSdnnMs      ?? null,
          bloodOxygenAvg:   data.vitals?.bloodOxygenAvg ?? null,
          gaitSpeedMs:      data.movement?.gaitSpeedMs      ?? null,
          stepCadence:      data.movement?.stepCadence      ?? null,
          walkingAsymmetry: data.movement?.walkingAsymmetry ?? null,
          totalSleepHours,
          deepSleepHours,
          remSleepHours,
          latencyMinutes,
          awakenings,
          reactionTimeMs: data.cognitivePerformance?.reactionTimeMs ?? null,
          memoryScore:    data.cognitivePerformance?.memoryScore    ?? null,
        },
      ],
    };

    let mlResult = null;
    let mlError  = null;

    try {
      const mlResponse = await axios.post(
        `${ML_SERVICE_URL}/assess-risk`,
        mlPayload,
        { timeout: 10000 }
      );
      mlResult = mlResponse.data;
      console.log("ML RESPONSE:", JSON.stringify(mlResult, null, 2));
    } catch (err) {
      mlError = err?.response?.data ?? err?.message ?? "ML unreachable";
      console.error("ML SERVICE ERROR:", JSON.stringify(mlError, null, 2));
    }

    // ── Persist ML prediction ─────────────────────────────────────────────
    if (mlResult) {
      prisma.aiPrediction.create({
        data: {
          userId,
          cognitiveIndex:          mlResult?.data?.cognitiveIndex                    ?? null,
          healthStatus:            mlResult?.data?.healthStatus                      ?? null,
          statusColor:             mlResult?.data?.statusColor                       ?? null,
          stabilityScore:          mlResult?.data?.predictions?.stabilityScore       ?? null,
          fatigueRisk:             mlResult?.data?.predictions?.fatigueRisk          ?? null,
          neuroDeclineProbability: mlResult?.data?.predictions?.neuroDeclineProbability ?? null,
          anomalies:               mlResult?.data?.anomalies  ?? [],
          aiInsights:              mlResult?.data?.aiInsights ?? [],
          modelVersion:            mlResult?.data?.modelVersion ?? null,
        },
      }).catch((e) => console.error("PREDICTION PERSIST ERROR:", e.message));
    }

    return res.status(200).json({
      status: "success",
      data: {
        // raw vitals
        steps:               data.vitals?.steps          ?? null,
        heartRateAvg:        data.vitals?.heartRateAvg   ?? null,
        hrvSdnnMs:           data.vitals?.hrvSdnnMs      ?? null,
        bloodOxygenAvg:      data.vitals?.bloodOxygenAvg ?? null,
        gaitSpeedMs:         data.movement?.gaitSpeedMs      ?? null,
        stepCadence:         data.movement?.stepCadence      ?? null,
        walkingAsymmetry:    data.movement?.walkingAsymmetry ?? null,
        sleepTotalHours:     totalSleepHours,
        sleepDeepHours:      deepSleepHours,
        sleepRemHours:       remSleepHours,
        sleepLatencyMinutes: latencyMinutes,
        sleepAwakenings:     awakenings,

        // ML results — nested under mlResult.data
        cognitiveIndex:  mlResult?.data?.cognitiveIndex  ?? null,
        healthStatus:    mlResult?.data?.healthStatus    ?? "Stable",
        statusColor:     mlResult?.data?.statusColor     ?? "#4CAF50",
        predictions:     mlResult?.data?.predictions     ?? {},
        anomalies:       mlResult?.data?.anomalies       ?? [],
        aiInsights:      mlResult?.data?.aiInsights      ?? [],

        // meta
        lastSync:        healthRecord.timestamp.toISOString(),
        profileComplete,
        mlAvailable:     mlResult !== null,
      },
    });

  } catch (error) {
    console.error("SYNC ERROR:", error);
    return res.status(500).json({
      message: "Health sync failed",
      error: error.message,
    });
  }
};

module.exports = { syncHealthData };
