const router = require("express").Router();
const authController = require("../controllers/auth.controller");
const { verifyToken } = require("../middleware/auth.middleware");
const prisma = require("../config/prisma");
const bcrypt = require('bcryptjs');
const crypto = require("crypto");

/* ================================
   AUTH ROUTES
================================ */
router.post("/register", authController.register);
router.post("/login", authController.login);

/* ================================
   GET USER PROFILE
================================ */
router.get("/profile", verifyToken, async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.userId },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        createdAt: true
      }
    });
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }
    res.json(user);
  } catch (error) {
    console.error("PROFILE ERROR:", error);
    res.status(500).json({ message: "Server error" });
  }
});

/* ================================
   FORGOT PASSWORD
================================ */
router.post("/forgot-password", async (req, res) => {
  try {
    const { email } = req.body ?? {};

    if (!email) {
      return res.status(400).json({ message: "Email is required" });
    }

    const user = await prisma.user.findUnique({ where: { email } });

    if (!user) {
      return res.status(200).json({ message: "If that email exists, a reset link has been sent." });
    }

    await prisma.passwordReset.deleteMany({ where: { userId: user.id } });

    const resetToken = crypto.randomBytes(32).toString("hex");

    await prisma.passwordReset.create({
      data: {
        userId:    user.id,
        token:     resetToken,
        expiresAt: new Date(Date.now() + 3600000)
      }
    });

    // TODO: Send email when nodemailer is set up
    // For now return token directly (remove in production)
    return res.status(200).json({
      message: "Password reset token generated",
      resetToken
    });
  } catch (error) {
    console.error("FORGOT PASSWORD ERROR:", error);
    return res.status(500).json({ message: "Failed to generate reset token", error: error.message });
  }
});

/* ================================
   RESET PASSWORD
================================ */
router.post("/reset-password", async (req, res) => {
  try {
    const { token, password } = req.body ?? {};

    if (!token || !password) {
      return res.status(400).json({ message: "Token and password are required" });
    }

    const resetEntry = await prisma.passwordReset.findUnique({ where: { token } });

    if (!resetEntry) {
      return res.status(400).json({ message: "Invalid reset token" });
    }
    if (resetEntry.expiresAt < new Date()) {
      return res.status(400).json({ message: "Reset token has expired" });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    await prisma.user.update({
      where: { id: resetEntry.userId },
      data:  { password: hashedPassword }
    });

    await prisma.passwordReset.delete({ where: { token } });

    return res.status(200).json({
      status:  "success",
      message: "Password reset successful. You can now log in with your new password."
    });
  } catch (error) {
    console.error("RESET PASSWORD ERROR:", error);
    return res.status(500).json({ message: "Password reset failed", error: error.message });
  }
});


/* ================================
   CHANGE PASSWORD (LOGGED IN)
================================ */
router.post("/change-password", verifyToken, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body ?? {};
    const userId = req.user.userId;

    if (!currentPassword || !newPassword) {
      return res.status(400).json({ message: "Both current and new passwords are required" });
    }

    const user = await prisma.user.findUnique({ where: { id: userId } });
    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    const isMatch = await bcrypt.compare(currentPassword, user.password);
    if (!isMatch) {
      return res.status(400).json({ message: "Current password is incorrect" });
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10);
    await prisma.user.update({
      where: { id: userId },
      data:  { password: hashedPassword }
    });

    return res.status(200).json({
      status:  "success",
      message: "Password changed successfully."
    });
  } catch (error) {
    console.error("CHANGE PASSWORD ERROR:", error);
    return res.status(500).json({ message: "Failed to change password", error: error.message });
  }
});

module.exports = router;
