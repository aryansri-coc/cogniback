const cron = require('node-cron');
const { PrismaClient } = require('@prisma/client');
const { generateAndStoreReport } = require('../services/reportService');

const prisma = new PrismaClient();

async function runReportJob(reportType) {
  console.log(`[CRON] Starting ${reportType} report generation...`);
  const users = await prisma.user.findMany({ select: { id: true } });

  for (const user of users) {
    try {
      await generateAndStoreReport(user.id, reportType);
      console.log(`[CRON] Report generated for user ${user.id}`);
    } catch (err) {
      console.error(`[CRON] Failed for user ${user.id}:`, err.message);
    }
  }
}

function startReportJobs() {
  // Every Sunday at 11 PM
  cron.schedule('0 23 * * 0', () => runReportJob('weekly'));

  // Every 14 days at 11 PM (1st and 15th of each month as proxy)
  cron.schedule('0 23 1,15 * *', () => runReportJob('fortnightly'));

  console.log('[CRON] Report jobs scheduled.');
}

module.exports = { startReportJobs };