const { PrismaClient } = require("@prisma/client");
const prisma = new PrismaClient();

const wordsData = require("../src/data/words");
const quizzesData = require("../src/data/quizzes");

async function main() {
    console.log("🌱 Starting seed...");

    // ─── Seed WordGame ─────────────────────────────────────────────────────────
    console.log("Seeding WordGame entries...");
    await prisma.wordGame.deleteMany(); // clear existing to avoid duplicates

    for (const word of wordsData) {
        await prisma.wordGame.create({
            data: {
                id: word.id,
                word: word.word,
                hint: word.hint,
                category: word.category,
                difficulty: word.difficulty,
            },
        });
    }
    console.log(`✅ Seeded ${wordsData.length} WordGame entries.`);

    // ─── Seed RecallQuiz ───────────────────────────────────────────────────────
    console.log("Seeding RecallQuiz entries...");
    await prisma.recallQuiz.deleteMany(); // clear existing to avoid duplicates

    for (const quiz of quizzesData) {
        await prisma.recallQuiz.create({
            data: {
                id: quiz.id,
                story: quiz.story,
                questions: quiz.questions,
            },
        });
    }
    console.log(`✅ Seeded ${quizzesData.length} RecallQuiz entries.`);

    console.log("🎉 Seed complete!");
}

main()
    .catch((e) => {
        console.error("❌ Seed failed:", e);
        process.exit(1);
    })
    .finally(async () => {
        await prisma.$disconnect();
    });