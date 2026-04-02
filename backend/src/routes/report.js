const express = require('express');
const router = express.Router();
const { getReports, getReportById, generateReport } = require('../controllers/reportController');
const { verifyToken } = require('../middleware/auth.middleware'); // your existing JWT middleware

router.use(verifyToken);

router.get('/', getReports);
router.get('/:id', getReportById);
router.post('/generate', generateReport);

module.exports = router;
