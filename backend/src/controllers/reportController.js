const { PrismaClient } = require('@prisma/client');
const { generateAndStoreReport } = require('../services/reportService');
const prisma = new PrismaClient();

const getReports = async (req, res) => {
  try {
    const reports = await prisma.report.findMany({
      where: { userId: req.user.userId },
      orderBy: { createdAt: 'desc' }
    });
    res.json({ reports });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch reports' });
  }
};

const getReportById = async (req, res) => {
  try {
    const report = await prisma.report.findFirst({
      where: { id: req.params.id, userId: req.user.userId }
    });
    if (!report) return res.status(404).json({ error: 'Report not found' });
    res.json({ report });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch report' });
  }
};

const generateReport = async (req, res) => {
  const { type } = req.body;
  if (!['weekly', 'fortnightly'].includes(type)) {
    return res.status(400).json({ error: 'type must be "weekly" or "fortnightly"' });
  }
  try {
    const reportId = await generateAndStoreReport(req.user.userId, type);
    res.json({ message: 'Report generated successfully', reportId });
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate report', details: err.message });
  }
};

module.exports = { getReports, getReportById, generateReport };
