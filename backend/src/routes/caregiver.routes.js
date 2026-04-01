const express = require("express");
const router = express.Router();
const { verifyToken } = require("../middleware/auth.middleware");
const { verifyCaregiver } = require("../middleware/caregiver.middleware");
const prisma = require("../config/prisma");

/* 🔗 Assign caregiver to a patient — caregiver only */
router.post("/assign", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const { patientId } = req.body;
    const patient = await prisma.user.findUnique({ where: { id: patientId } });
    if (!patient) {
      return res.status(404).json({ message: "Patient not found" });
    }
    if (patient.role !== "USER") {
      return res.status(400).json({ message: "Target is not a patient" });
    }
    const relation = await prisma.caregiverPatient.create({
      data: { caregiverId: req.user.userId, patientId }
    });
    res.status(201).json({ message: "Patient assigned successfully", relation });
  } catch (error) {
    if (error.code === "P2002") {
      return res.status(400).json({ message: "Patient already assigned to you" });
    }
    console.error("ERROR [POST /caregiver/assign]:", error);
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

/* 👥 Get all patients of a caregiver — caregiver only */
router.get("/my-patients", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const relations = await prisma.caregiverPatient.findMany({
      where: { caregiverId: req.user.userId },
      include: {
        patient: {
          select: { id: true, name: true, email: true, createdAt: true }
        }
      }
    });
    const patients = relations.map(r => ({ ...r.patient, assignedAt: r.assignedAt }));
    res.json({ total: patients.length, patients });
  } catch (error) {
    console.error("ERROR [GET /caregiver/my-patients]:", error);
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

/* 📱 GET /api/caregiver/patients — get care providers for logged in user */
router.get("/patients", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    const providers = await prisma.careProvider.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" }
    });

    return res.status(200).json({ status: "success", data: providers });
  } catch (error) {
    console.error("ERROR [GET /caregiver/patients]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

/* ➕ POST /api/caregiver/add — add a care provider */
router.post("/add", verifyToken, async (req, res) => {
  try {
    const userId      = req.user.userId;
    const name        = req.body.name         ?? null;
    const specialty   = req.body.specialty    ?? null;
    const email       = req.body.email        ?? null;
    const phoneNumber = req.body.phoneNumber  ?? null;
    const hospitalName= req.body.hospitalName ?? null;
    const imageUrl    = req.body.imageUrl     ?? null;

    if (!name) {
      return res.status(400).json({ status: "error", message: "Name is required" });
    }

    const provider = await prisma.careProvider.create({
      data: { userId, name, specialty, email, phoneNumber, hospitalName, imageUrl }
    });

    return res.status(201).json({ status: "success", data: provider });
  } catch (error) {
    console.error("ERROR [POST /caregiver/add]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

/* 📋 Get a patient's health history — caregiver only */
router.get("/patients/:patientId/history", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const { patientId } = req.params;
    const relation = await prisma.caregiverPatient.findUnique({
      where: {
        caregiverId_patientId: {
          caregiverId: req.user.userId,
          patientId
        }
      }
    });
    if (!relation) {
      return res.status(403).json({ message: "Not assigned to this patient" });
    }
    const history = await prisma.healthData.findMany({
      where: { userId: patientId },
      orderBy: { timestamp: "desc" }
    });
    res.json({ total: history.length, history });
  } catch (error) {
    console.error("ERROR [GET /caregiver/patients/:patientId/history]:", error);
    res.status(500).json({ message: "Server error", error: error.message });
  }
});

module.exports = router;
