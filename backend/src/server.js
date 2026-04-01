require("dotenv").config();
const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/auth",         require("./routes/auth.routes"));
app.use("/api/health",       require("./routes/health.routes"));
app.use("/api/user",         require("./routes/User.routes"));
app.use("/api/medicine",     require("./routes/medicine.routes"));
app.use("/api/emergency",    require("./routes/emergency.routes"));
app.use("/api/caregiver",    require("./routes/caregiver.routes"));
app.use("/api/v1/exercises", require("./routes/exercise.routes"));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
