const express = require("express");
const router = express.Router();
const prisma = require("../config/prisma");
const { verifyToken } = require("../middleware/auth.middleware");

// POST /api/medicine/reminder
router.post("/reminder", verifyToken, async (req, res) => {
  try {
    const userId    = req.user.userId;
    const name      = req.body.name      ?? null;
    const dosage    = req.body.dosage    ?? null;
    const frequency = req.body.frequency ?? null;
    const time      = req.body.time      ?? null;

    if (!name) {
      return res.status(400).json({ status: "error", message: "Medicine name is required" });
    }

    const reminder = await prisma.medicineReminder.create({
      data: { userId, name, dosage, frequency, time, status: "PENDING" }
    });

    return res.status(201).json({ status: "success", data: reminder });
  } catch (error) {
    console.error("ERROR [POST /medicine/reminder]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// GET /api/medicine/reminders
router.get("/reminders", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    const reminders = await prisma.medicineReminder.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" }
    });

    return res.status(200).json({ status: "success", data: reminders });
  } catch (error) {
    console.error("ERROR [GET /medicine/reminders]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// PUT /api/medicine/reminder/:id/status
router.put("/reminder/:id/status", verifyToken, async (req, res) => {
  try {
    const userId      = req.user.userId;
    const { id }      = req.params;
    const status      = req.body.status      ?? null;
    const completedAt = req.body.completedAt ?? null;

    const existing = await prisma.medicineReminder.findUnique({ where: { id } });

    if (!existing) {
      return res.status(404).json({ status: "error", message: "Reminder not found" });
    }
    if (existing.userId !== userId) {
      return res.status(403).json({ status: "error", message: "Forbidden" });
    }

    const updated = await prisma.medicineReminder.update({
      where: { id },
      data: {
        status:      status      ?? existing.status,
        completedAt: completedAt ? new Date(completedAt) : existing.completedAt
      }
    });

    return res.status(200).json({ status: "success", data: updated });
  } catch (error) {
    console.error("ERROR [PUT /medicine/reminder/:id/status]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

module.exports = router;
