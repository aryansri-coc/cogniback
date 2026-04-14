const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const prisma = require("../config/prisma");

// ─── REGISTER ────────────────────────────────────────────────────────────────
exports.register = async (req, res) => {
  try {
    const { name, email, password, role, age, sex } = req.body;

    const existingUser = await prisma.user.findUnique({ where: { email } });
    if (existingUser) {
      return res.status(400).json({ message: "Email already exists" });
    }

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = await prisma.user.create({
      data: {
        name,
        email,
        password: hashedPassword,
        role: role || "USER",
        age:  age ? parseInt(age) : null,
        sex:  sex || null,
      },
    });

    res.status(201).json({
      message: "User registered successfully",
      userId: user.id,
    });
  } catch (error) {
    console.error("REGISTER ERROR:", error);
    res.status(500).json({ message: "Server error" });
  }
};

// ─── LOGIN ────────────────────────────────────────────────────────────────────
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) return res.status(400).json({ message: "Invalid credentials" });

    const isValid = await bcrypt.compare(password, user.password);
    if (!isValid) return res.status(400).json({ message: "Invalid credentials" });

    // Short-lived access token (15 minutes)
    const accessToken = jwt.sign(
      { userId: user.id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: "15m" }
    );

    // Long-lived refresh token (30 days)
    const refreshToken = jwt.sign(
      { userId: user.id },
      process.env.JWT_REFRESH_SECRET,
      { expiresIn: "30d" }
    );

    res.json({
      message: "Login successful",
      accessToken,
      refreshToken,
      user: {
        id:   user.id,
        name: user.name,
        role: user.role,
      },
    });
  } catch (error) {
    console.error("LOGIN ERROR:", error);
    res.status(500).json({ message: "Server error" });
  }
};

// ─── REFRESH TOKEN ────────────────────────────────────────────────────────────
exports.refreshToken = async (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken) {
    return res.status(401).json({ message: "No refresh token provided" });
  }

  try {
    const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET);

    // Make sure user still exists
    const user = await prisma.user.findUnique({ where: { id: decoded.userId } });
    if (!user) {
      return res.status(403).json({ message: "User no longer exists" });
    }

    const newAccessToken = jwt.sign(
      { userId: user.id, role: user.role },
      process.env.JWT_SECRET,
      { expiresIn: "30m" }
    );

    res.json({ accessToken: newAccessToken });
  } catch (err) {
    console.error("REFRESH ERROR:", err.message);
    return res.status(403).json({ message: "Invalid or expired refresh token. Please login again." });
  }
};
