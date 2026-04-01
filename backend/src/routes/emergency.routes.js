const express = require("express");
const router = express.Router();
const prisma = require("../config/prisma");
const { verifyToken } = require("../middleware/auth.middleware");

// POST /api/emergency/contact
router.post("/contact", verifyToken, async (req, res) => {
  try {
    const userId       = req.user.userId;
    const name         = req.body.name         ?? null;
    const phoneNumber  = req.body.phoneNumber  ?? null;
    const relationship = req.body.relationship ?? null;
    const imageUrl     = req.body.imageUrl     ?? null;

    if (!name || !phoneNumber) {
      return res.status(400).json({ status: "error", message: "name and phoneNumber are required" });
    }

    const contact = await prisma.emergencyContact.create({
      data: { userId, name, phoneNumber, relationship, imageUrl }
    });

    return res.status(201).json({ status: "success", data: contact });
  } catch (error) {
    console.error("ERROR [POST /emergency/contact]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// GET /api/emergency/contacts
router.get("/contacts", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    const contacts = await prisma.emergencyContact.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" }
    });

    return res.status(200).json({ status: "success", data: contacts });
  } catch (error) {
    console.error("ERROR [GET /emergency/contacts]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

module.exports = router;
