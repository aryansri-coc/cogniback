const { PrismaClient } = require('@prisma/client');
const { generateAndStoreReport } = require('../services/reportService');
const prisma = new PrismaClient();

// GET /api/reports — list all reports for logged-in user
const getReports = async (req, res) => {
  try {
    const reports = await prisma.report.findMany({
      where: { userId: req.user.id },
      orderBy: { createdAt: 'desc' }
    });
    res.json({ reports });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch reports' });
  }
};

// GET /api/reports/:id — single report details
const getReportById = async (req, res) => {
  try {
    const report = await prisma.report.findFirst({
      where: { id: req.params.id, userId: req.user.id }
    });
    if (!report) return res.status(404).json({ error: 'Report not found' });
    res.json({ report });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch report' });
  }
};

// POST /api/reports/generate — manually trigger report generation
const generateReport = async (req, res) => {
  const { type } = req.body; // "weekly" or "fortnightly"
  if (!['weekly', 'fortnightly'].includes(type)) {
    return res.status(400).json({ error: 'type must be "weekly" or "fortnightly"' });
  }
  try {
    const reportId = await generateAndStoreReport(req.user.id, type);
    res.json({ message: 'Report generated successfully', reportId });
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate report', details: err.message });
  }
};

module.exports = { getReports, getReportById, generateReport };