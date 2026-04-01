const exerciseService = require("../services/exercise.service");

// ─── GET /api/v1/exercises/word ───────────────────────────────────────────────
const getWordGame = async (req, res) => {
    try {
        const game = exerciseService.generateWordGame();
        return res.status(200).json({
            status: "success",
            data: game,
        });
    } catch (error) {
        console.error("Word Game Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch word game.",
        });
    }
};

// ─── GET /api/v1/exercises/quiz ───────────────────────────────────────────────
const getQuizGame = async (req, res) => {
    try {
        const game = exerciseService.generateQuizGame();
        return res.status(200).json({
            status: "success",
            data: game,
        });
    } catch (error) {
        console.error("Quiz Game Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch quiz game.",
        });
    }
};

// ─── GET /api/v1/exercises/sequence/:level ────────────────────────────────────
const getSequenceGame = async (req, res) => {
    try {
        const { level } = req.params;
        const game = exerciseService.generateSequenceGame(level);
        return res.status(200).json({
            status: "success",
            data: game,
        });
    } catch (error) {
        console.error("Sequence Game Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch sequence game.",
        });
    }
};

// ─── GET /api/v1/exercises/pattern/:level ─────────────────────────────────────
const getPatternGame = async (req, res) => {
    try {
        const { level } = req.params;
        const { current_score } = req.query;
        const game = exerciseService.generatePatternGame(level, parseInt(current_score) || 0);
        return res.status(200).json({
            status: "success",
            data: game,
        });
    } catch (error) {
        console.error("Pattern Game Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch pattern game.",
        });
    }
};

// ─── GET /api/v1/exercises/daily ──────────────────────────────────────────────
const getDailyExercises = async (req, res) => {
    try {
        const userId = req.user.id;
        const daily = await exerciseService.getDailyExercises(userId);
        return res.status(200).json({
            status: "success",
            data: daily,
        });
    } catch (error) {
        console.error("Daily Exercises Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch daily exercises.",
        });
    }
};

// ─── POST /api/v1/exercises/submit ───────────────────────────────────────────
const submitExercise = async (req, res) => {
    try {
        const userId = req.user.id;
        const { gameType, gameId, score, completed } = req.body;

        if (!gameType) {
            return res.status(400).json({
                status: "error",
                message: "gameType is required.",
            });
        }

        const validGameTypes = ["word", "quiz", "sequence", "pattern"];
        if (!validGameTypes.includes(gameType)) {
            return res.status(400).json({
                status: "error",
                message: `Invalid gameType. Must be one of: ${validGameTypes.join(", ")}.`,
            });
        }

        const result = await exerciseService.submitExercise(userId, {
            gameType,
            gameId,
            score,
            completed,
        });

        return res.status(200).json({
            status: "success",
            data: result,
        });
    } catch (error) {
        console.error("Submit Exercise Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to submit exercise.",
        });
    }
};

// ─── GET /api/v1/exercises/progress ──────────────────────────────────────────
const getProgress = async (req, res) => {
    try {
        const userId = req.user.id;
        const progress = await exerciseService.getProgress(userId);
        return res.status(200).json({
            status: "success",
            data: progress,
        });
    } catch (error) {
        console.error("Progress Error:", error.message);
        return res.status(500).json({
            status: "error",
            message: "Failed to fetch progress.",
        });
    }
};

module.exports = {
    getWordGame,
    getQuizGame,
    getSequenceGame,
    getPatternGame,
    getDailyExercises,
    submitExercise,
    getProgress,
};