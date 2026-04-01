const prisma = require("../config/prisma");
const words = require("../data/words");
const quizzes = require("../data/quizzes");

// ─── Helpers ──────────────────────────────────────────────────────────────────

const getTodayRange = () => {
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const end = new Date();
    end.setHours(23, 59, 59, 999);
    return { start, end };
};

const getRandomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];

// ─── Game Generators ──────────────────────────────────────────────────────────

const generateWordGame = () => {
    const word = getRandomItem(words);
    return {
        game_id: word.id,
        word: word.word,
        hint: word.hint,
        category: word.category,
    };
};

const generateQuizGame = () => {
    const quiz = getRandomItem(quizzes);
    return {
        game_id: quiz.id,
        story: quiz.story,
        questions: quiz.questions,
    };
};

const generateSequenceGame = (level) => {
    const clampedLevel = Math.min(Math.max(parseInt(level) || 1, 1), 10);
    // Level 1 → 2 numbers, Level 10 → 10 numbers (level + 1)
    const length = clampedLevel + 1;
    const sequence = Array.from({ length }, () => Math.floor(Math.random() * 9) + 1);
    // Display duration decreases: level 1 → 5000ms, level 10 → 1500ms
    const display_duration_ms = Math.max(5000 - (clampedLevel - 1) * 400, 1500);
    return {
        level: clampedLevel,
        sequence,
        display_duration_ms,
    };
};

const generatePatternGame = (level, currentScore = 0) => {
    const clampedLevel = Math.min(Math.max(parseInt(level) || 1, 1), 10);
    // Pattern grows: level 1 → 2 cells, level 10 → 8 cells
    const patternLength = Math.min(clampedLevel + 1, 8);
    const indices = new Set();
    while (indices.size < patternLength) {
        indices.add(Math.floor(Math.random() * 9));
    }
    return {
        level: clampedLevel,
        grid_size: 3,
        pattern_indices: Array.from(indices),
        current_score: currentScore,
    };
};

// ─── Today's Session Lookup ───────────────────────────────────────────────────

const getTodaySessions = async (userId) => {
    const { start, end } = getTodayRange();
    return prisma.exerciseSession.findMany({
        where: {
            userId,
            createdAt: { gte: start, lte: end },
        },
    });
};

// ─── Service Functions ────────────────────────────────────────────────────────

const getDailyExercises = async (userId) => {
    const sessions = await getTodaySessions(userId);
    const sessionMap = {};
    for (const s of sessions) {
        sessionMap[s.gameType] = s;
    }

    const gameTypes = ["word", "quiz", "sequence", "pattern"];
    const completed = gameTypes.filter((t) => sessionMap[t]?.completed).length;

    const wordGame = { ...generateWordGame(), completed: !!sessionMap["word"]?.completed };
    const quizGame = { ...generateQuizGame(), completed: !!sessionMap["quiz"]?.completed };
    const sequenceGame = { ...generateSequenceGame(1), completed: !!sessionMap["sequence"]?.completed };
    const patternGame = { ...generatePatternGame(1), completed: !!sessionMap["pattern"]?.completed };

    return {
        date: new Date().toISOString().split("T")[0],
        completed,
        total: 4,
        percentage: Math.round((completed / 4) * 100),
        games: {
            word: wordGame,
            quiz: quizGame,
            sequence: sequenceGame,
            pattern: patternGame,
        },
    };
};

const submitExercise = async (userId, { gameType, gameId, score, completed }) => {
    const { start, end } = getTodayRange();

    // Check if a session for this game type already exists today
    const existing = await prisma.exerciseSession.findFirst({
        where: {
            userId,
            gameType,
            createdAt: { gte: start, lte: end },
        },
    });

    if (existing) {
        // Update existing session
        await prisma.exerciseSession.update({
            where: { id: existing.id },
            data: {
                score: score ?? existing.score,
                completed: completed ?? existing.completed,
                gameId: gameId ?? existing.gameId,
            },
        });
    } else {
        // Create new session
        await prisma.exerciseSession.create({
            data: {
                userId,
                gameType,
                gameId: gameId || null,
                score: score ?? 0,
                completed: completed ?? false,
            },
        });
    }

    // Calculate daily progress after update
    const sessions = await getTodaySessions(userId);
    const completedCount = sessions.filter((s) => s.completed).length;
    const dailyProgress = Math.round((completedCount / 4) * 100);

    return {
        success: true,
        score: score ?? 0,
        dailyProgress,
    };
};

const getProgress = async (userId) => {
    const sessions = await getTodaySessions(userId);
    const gameTypes = ["word", "quiz", "sequence", "pattern"];

    const breakdown = gameTypes.map((type) => {
        const session = sessions.find((s) => s.gameType === type);
        return {
            gameType: type,
            score: session?.score ?? 0,
            completed: session?.completed ?? false,
        };
    });

    const completedCount = breakdown.filter((b) => b.completed).length;
    const totalScore = breakdown.reduce((sum, b) => sum + b.score, 0);

    return {
        date: new Date().toISOString().split("T")[0],
        percentage: Math.round((completedCount / 4) * 100),
        totalScore,
        gamesCompleted: completedCount,
        gamesTotal: 4,
        breakdown,
    };
};

module.exports = {
    generateWordGame,
    generateQuizGame,
    generateSequenceGame,
    generatePatternGame,
    getDailyExercises,
    submitExercise,
    getProgress,
};