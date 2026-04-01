const prisma = require("../config/prisma");
const axios = require("axios");

const ML_SERVICE_URL =
  process.env.ML_SERVICE_URL ||
  "https://industrious-wonder-production-8960.up.railway.app";

const syncHealthData = async (req, res) => {
  try {
    // ── Auth guard ──────────────────────────────────────────────────────────
    if (!req.user) {
      return res.status(401).json({ message: "Unauthorized: no user in token" });
    }

    // Always pull userId from the verified JWT, never from the body
    const userId = req.user.userId;
    const data = req.body;

    // ── Profile completeness check (non-blocking warning) ───────────────────
    const user = await prisma.user.findUnique({ where: { id: userId } });

    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    if (!user?.age || !user?.sex) {
      console.warn(
        `SYNC WARN: User ${userId} is missing age/sex — AI risk scoring may be limited`
      );
    }

    // ── Normalise sleep fields ──────────────────────────────────────────────
    // Mobile (Kotlin) sends: sleep.deep / sleep.rem / sleep.latency
    // Web / Postman sends:   sleep.deepSleepHours / sleep.remSleepHours / sleep.latencyMinutes
    // We support BOTH so neither client breaks.
    const sleep = data.sleep ?? {};
    const totalSleepHours = sleep.totalHours                       ?? null;
    const deepSleepHours  = sleep.deepSleepHours  ?? sleep.deep    ?? null;
    const remSleepHours   = sleep.remSleepHours   ?? sleep.rem     ?? null;
    const latencyMinutes  = sleep.latencyMinutes  ?? sleep.latency ?? null;
    const awakenings      = sleep.awakenings                       ?? null;

    // ── Persist health record ───────────────────────────────────────────────
    const healthRecord = await prisma.healthData.create({
      data: {
        userId,
        timestamp:       new Date(data.timestamp ?? Date.now()),

        // vitals
        steps:           data.vitals?.steps          ?? null,
        heartRateAvg:    data.vitals?.heartRateAvg   ?? null,
        hrvSdnnMs:       data.vitals?.hrvSdnnMs      ?? null,
        bloodOxygenAvg:  data.vitals?.bloodOxygenAvg ?? null,

        // movement
        gaitSpeedMs:      data.movement?.gaitSpeedMs      ?? null,
        stepCadence:      data.movement?.stepCadence      ?? null,
        walkingAsymmetry: data.movement?.walkingAsymmetry ?? null,

        // sleep (normalised above — works for both mobile and web)
        totalSleepHours,
        deepSleepHours,
        remSleepHours,
        latencyMinutes,
        awakenings,

        // cognitive performance
        reactionTimeMs: data.cognitivePerformance?.reactionTimeMs ?? null,
        memoryScore:    data.cognitivePerformance?.memoryScore    ?? null,
        testType:       data.cognitivePerformance?.testType       ?? null,
      },
    });

    // ── Call ML service ─────────────────────────────────────────────────────
    let mlResult = null;
    try {
      const mlPayload = {
        user_id: userId,
        age:     user?.age ?? null,
        sex:     user?.sex ?? null,
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
            reactionTimeMs:   data.cognitivePerformance?.reactionTimeMs ?? null,
            memoryScore:      data.cognitivePerformance?.memoryScore    ?? null,
          },
        ],
      };

      const mlResponse = await axios.post(
        `${ML_SERVICE_URL}/assess-risk`,
        mlPayload,
        { timeout: 10000 }
      );

      mlResult = mlResponse.data;
    } catch (mlError) {
      console.error("ML SERVICE ERROR:", mlError?.response?.data ?? mlError?.message ?? mlError);
    }

    // ── Build response ──────────────────────────────────────────────────────
    // Flat structure supports both mobile (Kotlin) and web (Next.js) clients
    return res.status(200).json({
      status: "success",
      data: {
        // raw vitals — mobile expects these at top level of data {}
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

        // ML results
        cognitiveIndex:  mlResult?.data?.cognitiveIndex  ?? mlResult?.cognitiveIndex  ?? null,
        healthStatus:    mlResult?.data?.healthStatus    ?? mlResult?.healthStatus    ?? "Stable",
        statusColor:     mlResult?.data?.statusColor     ?? mlResult?.statusColor     ?? "#4CAF50",
        predictions:     mlResult?.data?.predictions     ?? mlResult?.predictions     ?? {},
        anomalies:       mlResult?.data?.anomalies       ?? mlResult?.anomalies       ?? [],
        aiInsights:      mlResult?.data?.aiInsights      ?? mlResult?.aiInsights      ?? [],
        lastSync:        healthRecord.timestamp.toISOString(),
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
