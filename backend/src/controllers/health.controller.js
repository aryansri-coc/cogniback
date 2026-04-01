const prisma = require("../config/prisma");
const axios = require("axios");

const ML_SERVICE_URL = process.env.ML_SERVICE_URL;

const syncHealthData = async (req, res) => {
  try {
    // ── Auth guard ──────────────────────────────────────────────────────────
    if (!req.user) {
      return res.status(401).json({ message: "Unauthorized: no user in token" });
    }

    const userId = req.user.userId;
    const data = req.body;

    // ── Fetch user ──────────────────────────────────────────────────────────
    const user = await prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    const profileComplete = !!user.age && !!user.sex;
    if (!profileComplete) {
      console.warn(
        `SYNC WARN: User ${userId} is missing age/sex — using fallbacks for ML payload`
      );
    }

    // ── Normalise sleep fields ──────────────────────────────────────────────
    const sleep = data.sleep ?? {};
    const totalSleepHours = sleep.totalHours                        ?? null;
    const deepSleepHours  = sleep.deepSleepHours  ?? sleep.deep     ?? null;
    const remSleepHours   = sleep.remSleepHours   ?? sleep.rem      ?? null;
    const latencyMinutes  = sleep.latencyMinutes  ?? sleep.latency  ?? null;
    const awakenings      = sleep.awakenings                        ?? null;

    // ── Persist health record ───────────────────────────────────────────────
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

    // ── Build ML payload — NEVER send null for required fields ──────────────
    //
    // ML schema requires age: integer, sex: string — no nulls allowed.
    // Fallbacks below are medically neutral population averages; they allow
    // the model to run and return a result while the user profile is incomplete.
    // The `profileComplete` flag is surfaced in the response so the frontend
    // can prompt the user to fill in their profile for personalised scoring.
    //
    const mlPayload = {
      user_id: userId,
      age:     user.age  ?? 45,          // fallback: population median
      sex:     user.sex  ?? "unknown",   // fallback: neutral category
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

    // ── Call ML service ─────────────────────────────────────────────────────
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
      mlError = err?.response?.data ?? err?.message ?? "ML service unreachable";
      console.error("ML SERVICE ERROR:", JSON.stringify(mlError, null, 2));
    }

    // ── Persist ML prediction (fire-and-forget, non-blocking) ───────────────
    // Only persists when we get a real ML result back
    if (mlResult) {
      prisma.aiPrediction.create({
        data: {
          userId,
          cognitiveIndex:          mlResult?.cognitiveIndex          ?? null,
          healthStatus:            mlResult?.healthStatus            ?? null,
          statusColor:             mlResult?.statusColor             ?? null,
          stabilityScore:          mlResult?.predictions?.stabilityScore          ?? null,
          fatigueRisk:             mlResult?.predictions?.fatigueRisk             ?? null,
          neuroDeclineProbability: mlResult?.predictions?.neuroDeclineProbability ?? null,
          anomalies:               mlResult?.anomalies  ?? [],
          aiInsights:              mlResult?.aiInsights ?? [],
          modelVersion:            mlResult?.modelVersion ?? null,
        },
      }).catch((e) => console.error("PREDICTION PERSIST ERROR:", e.message));
    }

    // ── Build response ──────────────────────────────────────────────────────
    return res.status(200).json({
      status: "success",
      data: {
        // Raw vitals — flat structure for both mobile (Kotlin) and web (Next.js)
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

        // ML results — single access path (no more double-fallback chains)
        cognitiveIndex:  mlResult?.cognitiveIndex  ?? null,
        healthStatus:    mlResult?.healthStatus    ?? "Stable",
        statusColor:     mlResult?.statusColor     ?? "#4CAF50",
        predictions:     mlResult?.predictions     ?? {},
        anomalies:       mlResult?.anomalies       ?? [],
        aiInsights:      mlResult?.aiInsights      ?? [],

        // Meta
        lastSync:        healthRecord.timestamp.toISOString(),
        profileComplete,                    // frontend can prompt for age/sex
        mlAvailable:     mlResult !== null, // false = ML failed, using defaults
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
