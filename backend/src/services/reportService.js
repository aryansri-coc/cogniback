const prisma = require("../config/prisma");
const axios = require("axios");

const ML_SERVICE_URL = process.env.ML_SERVICE_URL;

async function generateAndStoreReport(userId, reportType) {
  // 1. Determine date range
  const periodEnd = new Date();
  const periodStart = new Date();

  if (reportType === "weekly") {
    periodStart.setDate(periodEnd.getDate() -  90);
  } else if (reportType === "fortnightly") {
    periodStart.setDate(periodEnd.getDate() -  90);
  } else {
    periodStart.setDate(periodEnd.getDate() -  90);
  }

  // 2. Fetch user profile
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new Error(`User ${userId} not found`);

  const profileComplete = !!user.age && !!user.sex;
  if (!profileComplete) {
    console.warn(`[REPORT] User ${userId} missing age/sex — using fallbacks`);
  }

  // 3. Fetch all HealthData records in the period
  const records = await prisma.healthData.findMany({
    where: {
      userId,
      timestamp: {
        gte: periodStart,
        lte: periodEnd,
      },
    },
    orderBy: { timestamp: "asc" },
  });

  if (records.length === 0) {
    console.warn(`[REPORT] No health records found for user ${userId} in period`);
    throw new Error("No health data available for this period");
  }

  console.log(`[REPORT] Found ${records.length} records for user ${userId} (${reportType})`);

  // 4. Build ML payload with all records
  const mlPayload = {
    user_id: userId,
    age: user.age ?? 45,
    sex: user.sex?.toLowerCase() === "female" ? "female" : "male",
    records: records.map((r) => ({
      timestamp:        r.timestamp.toISOString(),
      steps:            r.steps,
      heartRateAvg:     r.heartRateAvg,
      hrvSdnnMs:        r.hrvSdnnMs,
      bloodOxygenAvg:   r.bloodOxygenAvg,
      gaitSpeedMs:      r.gaitSpeedMs,
      stepCadence:      r.stepCadence,
      walkingAsymmetry: r.walkingAsymmetry,
      totalSleepHours:  r.totalSleepHours,
      deepSleepHours:   r.deepSleepHours,
      remSleepHours:    r.remSleepHours,
      latencyMinutes:   r.latencyMinutes,
      awakenings:       r.awakenings,
      reactionTimeMs:   r.reactionTimeMs,
      memoryScore:      r.memoryScore,
    })),
  };

  // 5. Call ML service
  let mlResult = null;
  try {
    const mlResponse = await axios.post(
      `${ML_SERVICE_URL}/assess-risk`,
      mlPayload,
      { timeout: 30000 } // longer timeout for batch
    );
    mlResult = mlResponse.data;
    console.log(`[REPORT] ML responded for user ${userId}`);
  } catch (err) {
    const mlError = err?.response?.data ?? err?.message ?? "ML unreachable";
    console.error(`[REPORT] ML ERROR for user ${userId}:`, JSON.stringify(mlError));
    throw new Error("ML service failed: " + JSON.stringify(mlError));
  }

  // 6. Build report summary from ML response
  const mlData = mlResult?.data ?? {};

  const reportSummary = {
    recordCount:             records.length,
    periodStart:             periodStart.toISOString(),
    periodEnd:               periodEnd.toISOString(),
    profileComplete,
    cognitiveIndex:          mlData.cognitiveIndex          ?? null,
    healthStatus:            mlData.healthStatus            ?? "Unknown",
    statusColor:             mlData.statusColor             ?? "#9E9E9E",
    predictions: {
      stabilityScore:          mlData.predictions?.stabilityScore          ?? null,
      fatigueRisk:             mlData.predictions?.fatigueRisk             ?? null,
      neuroDeclineProbability: mlData.predictions?.neuroDeclineProbability ?? null,
    },
    anomalies:   mlData.anomalies  ?? [],
    aiInsights:  mlData.aiInsights ?? [],
    modelVersion: mlData.modelVersion ?? null,
    // Averages computed from raw records
    averages: computeAverages(records),
  };

  // 7. Persist report to DB
  const report = await prisma.report.create({
    data: {
      userId,
      type:        reportType,
      status:      "completed",
      periodStart,
      periodEnd,
      fileUrl:     JSON.stringify(reportSummary), // storing JSON in fileUrl for now
    },
  });

  console.log(`[REPORT] Stored report ${report.id} for user ${userId}`);
  return report.id;
}

// Helper: compute averages from raw HealthData records
function computeAverages(records) {
  const avg = (key) => {
    const vals = records.map((r) => r[key]).filter((v) => v !== null && v !== undefined);
    if (vals.length === 0) return null;
    return parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2));
  };

  return {
    steps:            avg("steps"),
    heartRateAvg:     avg("heartRateAvg"),
    hrvSdnnMs:        avg("hrvSdnnMs"),
    bloodOxygenAvg:   avg("bloodOxygenAvg"),
    gaitSpeedMs:      avg("gaitSpeedMs"),
    stepCadence:      avg("stepCadence"),
    walkingAsymmetry: avg("walkingAsymmetry"),
    totalSleepHours:  avg("totalSleepHours"),
    deepSleepHours:   avg("deepSleepHours"),
    remSleepHours:    avg("remSleepHours"),
    latencyMinutes:   avg("latencyMinutes"),
    awakenings:       avg("awakenings"),
    reactionTimeMs:   avg("reactionTimeMs"),
    memoryScore:      avg("memoryScore"),
  };
}

module.exports = { generateAndStoreReport };
