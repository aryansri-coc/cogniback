const jwt = require("jsonwebtoken");

exports.verifyToken = (req, res, next) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ message: "No token provided", expired: false });
  }

  const token = authHeader.split(" ")[1];

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (error) {
    const isExpired = error.name === "TokenExpiredError";
    return res.status(401).json({
      message: isExpired ? "Token expired" : "Invalid token",
      expired: isExpired,   // frontend uses this flag to trigger refresh
    });
  }
};
