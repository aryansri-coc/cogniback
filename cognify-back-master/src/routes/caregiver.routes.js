const router = require("express").Router();
const { verifyToken } = require("../middleware/auth.middleware");
const { verifyCaregiver } = require("../middleware/caregiver.middleware");
const prisma = require("../config/prisma");

/* 🔗 Assign caregiver to a patient */
router.post("/assign", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const { patientId } = req.body;

    const patient = await prisma.user.findUnique({
      where: { id: patientId },
    });

    if (!patient) {
      return res.status(404).json({ message: "Patient not found" });
    }

    if (patient.role !== "USER") {
      return res.status(400).json({ message: "Target is not a patient" });
    }

    const relation = await prisma.caregiverPatient.create({
      data: {
        caregiverId: req.user.userId,
        patientId,
      },
    });

    res.status(201).json({
      message: "Patient assigned successfully",
      relation,
    });

  } catch (error) {
    if (error.code === "P2002") {
      return res.status(400).json({ message: "Patient already assigned to you" });
    }
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
});

/* 👥 Get all patients of a caregiver */
router.get("/patients", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const relations = await prisma.caregiverPatient.findMany({
      where: { caregiverId: req.user.userId },
      include: {
        patient: {
          select: { id: true, name: true, email: true, createdAt: true },
        },
      },
    });

    const patients = relations.map((r) => ({
      ...r.patient,
      assignedAt: r.assignedAt,
    }));

    res.json({ total: patients.length, patients });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
});

/* 📋 Get a patient's health history */
router.get("/patients/:patientId/history", verifyToken, verifyCaregiver, async (req, res) => {
  try {
    const { patientId } = req.params;

    const relation = await prisma.caregiverPatient.findUnique({
      where: {
        caregiverId_patientId: {
          caregiverId: req.user.userId,
          patientId,
        },
      },
    });

    if (!relation) {
      return res.status(403).json({ message: "Not assigned to this patient" });
    }

    const history = await prisma.healthData.findMany({
      where: { userId: patientId },
      orderBy: { timestamp: "desc" },
    });

    res.json({ total: history.length, history });

  } catch (error) {
    console.error(error);
    res.status(500).json({ message: "Server error" });
  }
});

module.exports = router;