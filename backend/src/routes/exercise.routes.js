const express = require("express");
const router = express.Router();
const prisma = require("../config/prisma");
const { verifyToken } = require("../middleware/auth.middleware");

// — helpers ——————————————————————————————————————————————————————————————————
function buildContent(type, game) {
  switch (type) {
    case "WORD_GAME":
      return {
        word:      game.word,
        scrambled: game.word.split("").sort(() => Math.random() - 0.5).join(""),
        hint:      game.hint
      };
    case "NUMBER_SEQUENCE":
      return {
        sequence: Array.from({ length: 5 }, () => Math.floor(Math.random() * 9) + 1)
      };
    case "RECALL_QUIZ":
      // FIX: Return the story and the full array of questions
      return {
        story:    game.story,
        questions: game.questions.map(q => ({
          question: q.question,
          options:  q.options,
          answer:   q.options[q.correct_index]
        }))
      };
    case "VISUAL_PATTERNS":
      return {
        pattern: Array.from({ length: 4 }, () => Math.floor(Math.random() * 9))
          .filter((v, i, a) => a.indexOf(v) === i)
      };
    default:
      return {};
  }
}

// GET /api/v1/exercises/daily
router.get("/daily", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;

    // Fetch all available games
    const allWordGames = await prisma.wordGame.findMany();
    const allQuizzes   = await prisma.recallQuiz.findMany();

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    // Check what the user has already finished today
    const completedToday = await prisma.exerciseSession.findMany({
      where: { userId, completed: true, createdAt: { gte: startOfDay } }
    });
    const completedIds = new Set(completedToday.map(s => s.gameId));

    // PROGRESSION LOGIC: Pick the first game that hasn't been completed yet
    const wordGame = allWordGames.find(g => !completedIds.has(g.id)) || allWordGames[0];
    const recallQuiz = allQuizzes.find(q => !completedIds.has(q.id)) || allQuizzes[0];

    const exercises = [
      { id: wordGame?.id   ?? "wg_001",  type: "WORD_GAME",        isCompleted: completedIds.has(wordGame?.id) },
      { id: "seq_001",                   type: "NUMBER_SEQUENCE",   isCompleted: completedIds.has("seq_001") },
      { id: recallQuiz?.id ?? "rq_001",  type: "RECALL_QUIZ",       isCompleted: completedIds.has(recallQuiz?.id) },
      { id: "vp_001",                    type: "VISUAL_PATTERNS",   isCompleted: completedIds.has("vp_001") },
    ];

    const completedCount = exercises.filter(e => e.isCompleted).length;
    const goalProgress   = exercises.length > 0 ? completedCount / exercises.length : 0;

    return res.status(200).json({ goalProgress, exercises });
  } catch (error) {
    console.error("ERROR [GET /exercises/daily]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// GET /api/v1/exercises/:id
router.get("/:id", verifyToken, async (req, res) => {
  try {
    const userId = req.user.userId;
    const { id } = req.params;

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);

    const completed = await prisma.exerciseSession.findFirst({
      where: { userId, gameId: id, completed: true, createdAt: { gte: startOfDay } }
    });

    let type, content;

    if (id.startsWith("seq_") || id === "seq_001") {
      type    = "NUMBER_SEQUENCE";
      content = buildContent(type, {});
    } else if (id.startsWith("vp_") || id === "vp_001") {
      type    = "VISUAL_PATTERNS";
      content = buildContent(type, {});
    } else {
      const wordGame = await prisma.wordGame.findUnique({ where: { id } });
      if (wordGame) {
        type    = "WORD_GAME";
        content = buildContent(type, wordGame);
      } else {
        const quiz = await prisma.recallQuiz.findUnique({ where: { id } });
        if (quiz) {
          type    = "RECALL_QUIZ";
          content = buildContent(type, quiz);
        } else {
          return res.status(404).json({ status: "error", message: "Exercise not found" });
        }
      }
    }

    return res.status(200).json({
      type,
      id,
      isCompleted: !!completed,
      content
    });
  } catch (error) {
    console.error("ERROR [GET /exercises/:id]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

// POST /api/v1/exercises/submit
router.post("/submit", verifyToken, async (req, res) => {
  try {
    const userId     = req.user.userId;
    const exerciseId = req.body.exerciseId ?? null;
    const score      = req.body.score      ?? 0;

    if (!exerciseId) {
      return res.status(400).json({ status: "error", message: "exerciseId is required" });
    }

    const session = await prisma.exerciseSession.create({
      data: {
        userId,
        gameType:  "EXERCISE",
        gameId:    exerciseId,
        score:     score,
        completed: true
      }
    });

    return res.status(201).json({ status: "success", data: session });
  } catch (error) {
    console.error("ERROR [POST /exercises/submit]:", error);
    return res.status(500).json({ status: "error", message: error.message });
  }
});

module.exports = router;
