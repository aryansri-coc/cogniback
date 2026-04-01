exports.verifyCaregiver = (req, res, next) => {
  if (req.user.role !== "CAREGIVER") {
    return res.status(403).json({ message: "Access denied. Caregivers only." });
  }
  next();
};