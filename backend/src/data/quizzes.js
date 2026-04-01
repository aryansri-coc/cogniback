const quizzes = [
    {
        id: "quiz_001",
        story: "Sarah went to the market at 10 AM on a Tuesday morning. She bought three apples, a loaf of bread, and a carton of orange juice. The total came to $8.50. She paid with a $10 bill and received change. On her way home, she met her neighbor Tom who was walking his dog named Biscuit.",
        questions: [
            { question: "What time did Sarah go to the market?", options: ["9 AM", "10 AM", "11 AM"], correct_index: 1 },
            { question: "What day of the week did Sarah go to the market?", options: ["Monday", "Wednesday", "Tuesday"], correct_index: 2 },
            { question: "How many apples did Sarah buy?", options: ["Two", "Three", "Four"], correct_index: 1 },
            { question: "What was the name of Tom's dog?", options: ["Biscuit", "Cookie", "Muffin"], correct_index: 0 },
        ],
    },
    {
        id: "quiz_002",
        story: "Dr. James opened his clinic every morning at 8 AM. On Wednesday, his first patient was an elderly woman named Mrs. Chen who had a sore throat. He prescribed her some antibiotics and told her to rest for three days. His second patient was a young boy named Leo who had twisted his ankle playing football.",
        questions: [
            { question: "What time does Dr. James open his clinic?", options: ["7 AM", "8 AM", "9 AM"], correct_index: 1 },
            { question: "What was Mrs. Chen's complaint?", options: ["Headache", "Sore throat", "Back pain"], correct_index: 1 },
            { question: "How many days of rest did Dr. James prescribe?", options: ["Two", "Three", "Five"], correct_index: 1 },
            { question: "How did Leo injure himself?", options: ["Fell off a bicycle", "Playing football", "Climbing a tree"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_003",
        story: "The annual science fair took place on a Friday at Riverside School. Emma, a 12-year-old student, won first place with her project about solar energy. She used 5 solar panels and built a small model house. Her teacher, Mr. Rivera, was very proud. The second-place winner was a student named Aiden who studied water filtration.",
        questions: [
            { question: "What day did the science fair take place?", options: ["Thursday", "Saturday", "Friday"], correct_index: 2 },
            { question: "What was Emma's project about?", options: ["Wind energy", "Solar energy", "Hydropower"], correct_index: 1 },
            { question: "How many solar panels did Emma use?", options: ["3", "5", "7"], correct_index: 1 },
            { question: "What did Aiden study for his project?", options: ["Air pollution", "Soil erosion", "Water filtration"], correct_index: 2 },
        ],
    },
    {
        id: "quiz_004",
        story: "Maria left her house at 7:30 AM to catch the 8 o'clock train to the city. She carried a blue backpack and wore a red scarf. The train ride lasted 45 minutes. Once she arrived, she went straight to the library to return two books she had borrowed three weeks ago. She then stopped at a café for a black coffee before heading to work.",
        questions: [
            { question: "What time did Maria leave her house?", options: ["7:00 AM", "7:30 AM", "8:00 AM"], correct_index: 1 },
            { question: "What color was Maria's backpack?", options: ["Red", "Black", "Blue"], correct_index: 2 },
            { question: "How long was the train ride?", options: ["30 minutes", "45 minutes", "60 minutes"], correct_index: 1 },
            { question: "How many books did Maria return?", options: ["One", "Two", "Three"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_005",
        story: "Carlos started his morning run at 6 AM every day. On Thursday, he ran 5 kilometers through the park and spotted a family of ducks near the pond. After the run, he drank a glass of water and ate a banana for breakfast. He then took a shower and got ready for his job as an architect.",
        questions: [
            { question: "What time does Carlos start his run?", options: ["5 AM", "6 AM", "7 AM"], correct_index: 1 },
            { question: "How far did Carlos run on Thursday?", options: ["3 km", "4 km", "5 km"], correct_index: 2 },
            { question: "What did Carlos eat after his run?", options: ["An apple", "A banana", "Toast"], correct_index: 1 },
            { question: "What is Carlos's job?", options: ["Engineer", "Architect", "Teacher"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_006",
        story: "The village of Millbrook held its annual harvest festival every October. This year, Farmer Pete grew the biggest pumpkin, which weighed 42 kilograms. His daughter Amy helped him carry it to the judging table. The festival also featured apple pie contests, and a woman named Grace won with her cinnamon-spiced recipe.",
        questions: [
            { question: "When is the Millbrook harvest festival held?", options: ["September", "October", "November"], correct_index: 1 },
            { question: "How much did Farmer Pete's pumpkin weigh?", options: ["32 kg", "42 kg", "52 kg"], correct_index: 1 },
            { question: "Who helped Farmer Pete carry the pumpkin?", options: ["His son", "His wife", "His daughter Amy"], correct_index: 2 },
            { question: "Who won the apple pie contest?", options: ["Grace", "Amy", "Pete"], correct_index: 0 },
        ],
    },
    {
        id: "quiz_007",
        story: "Ben had a doctor's appointment at 3 PM on Monday. He arrived 10 minutes early and filled out a form with his health history. The doctor told him his blood pressure was slightly elevated and recommended he reduce salt intake and exercise at least 30 minutes a day. Ben was also advised to return in two weeks for a follow-up.",
        questions: [
            { question: "What time was Ben's appointment?", options: ["2 PM", "3 PM", "4 PM"], correct_index: 1 },
            { question: "How early did Ben arrive?", options: ["5 minutes", "10 minutes", "15 minutes"], correct_index: 1 },
            { question: "What health issue did the doctor mention?", options: ["Low blood sugar", "Elevated blood pressure", "High cholesterol"], correct_index: 1 },
            { question: "How soon was Ben asked to return?", options: ["One week", "Two weeks", "One month"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_008",
        story: "Lena visited her grandmother every Sunday. This Sunday, her grandmother was baking a chocolate cake for Lena's birthday. The recipe required 2 cups of flour, 3 eggs, and half a cup of cocoa powder. Lena helped stir the batter. After baking, they sat on the porch and watched the sunset together.",
        questions: [
            { question: "When does Lena visit her grandmother?", options: ["Saturday", "Sunday", "Friday"], correct_index: 1 },
            { question: "What type of cake was being baked?", options: ["Vanilla", "Carrot", "Chocolate"], correct_index: 2 },
            { question: "How many eggs did the recipe need?", options: ["2", "3", "4"], correct_index: 1 },
            { question: "What did Lena and her grandmother do after baking?", options: ["Watched TV", "Watched the sunset", "Played cards"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_009",
        story: "The city library launched a new reading program called 'Pages & Friends' in January. The program allowed members to borrow up to 4 books at a time and attend weekly reading sessions every Saturday at 11 AM. Over 200 people signed up in the first week. The head librarian, Ms. Patel, said the program exceeded all expectations.",
        questions: [
            { question: "What is the name of the library program?", options: ["Read & Grow", "Pages & Friends", "Book Club Plus"], correct_index: 1 },
            { question: "When were the weekly reading sessions held?", options: ["Sunday at 10 AM", "Saturday at 11 AM", "Friday at 12 PM"], correct_index: 1 },
            { question: "How many books could members borrow at once?", options: ["3", "4", "5"], correct_index: 1 },
            { question: "How many people signed up in the first week?", options: ["100", "150", "200"], correct_index: 2 },
        ],
    },
    {
        id: "quiz_010",
        story: "During a camping trip last summer, four friends — Kai, Zoe, Marcus, and Nina — hiked 8 kilometers to reach a lake. They set up their tents at 5 PM and cooked pasta over a campfire. Marcus forgot to bring a sleeping bag so Zoe lent him her spare one. The next morning, they woke up at sunrise and went for a swim.",
        questions: [
            { question: "How far did the friends hike to reach the lake?", options: ["5 km", "8 km", "10 km"], correct_index: 1 },
            { question: "What time did they set up their tents?", options: ["4 PM", "5 PM", "6 PM"], correct_index: 1 },
            { question: "Who forgot their sleeping bag?", options: ["Kai", "Nina", "Marcus"], correct_index: 2 },
            { question: "What did they cook over the campfire?", options: ["Rice", "Pasta", "Soup"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_011",
        story: "The local art museum opened a new exhibit called 'Colors of the Mind' on March 15th. Over 50 paintings from artists across 12 countries were displayed. The opening night attracted more than 300 visitors. One of the most admired works was a large blue painting by a Brazilian artist named Lucia Fonseca, which depicted the ocean at night.",
        questions: [
            { question: "What is the name of the new exhibit?", options: ["Art of the World", "Colors of the Mind", "Minds and Colors"], correct_index: 1 },
            { question: "How many countries were the artists from?", options: ["10", "12", "15"], correct_index: 1 },
            { question: "How many visitors attended opening night?", options: ["200", "250", "300"], correct_index: 2 },
            { question: "What did Lucia Fonseca's painting depict?", options: ["A forest at dawn", "The ocean at night", "A mountain at sunset"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_012",
        story: "Nick works as a chef at a restaurant called The Golden Fork. Every morning he arrives at 9 AM to prepare for lunch service. On Friday, he created a new dish: grilled salmon with lemon butter sauce and roasted vegetables. The dish became an instant hit, and by evening, they had served it to 47 customers.",
        questions: [
            { question: "What is the name of Nick's restaurant?", options: ["The Silver Spoon", "The Golden Fork", "The Blue Plate"], correct_index: 1 },
            { question: "What time does Nick arrive each morning?", options: ["8 AM", "9 AM", "10 AM"], correct_index: 1 },
            { question: "What protein was in Nick's new dish?", options: ["Chicken", "Tuna", "Salmon"], correct_index: 2 },
            { question: "How many customers ordered the new dish by evening?", options: ["37", "47", "57"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_013",
        story: "A 9-year-old girl named Priya found a stray kitten near her school on a rainy Wednesday afternoon. The kitten was grey with white paws. Priya brought it home and her parents agreed to keep it. She named it Cloud. The vet said Cloud was about 8 weeks old and was in good health after being vaccinated.",
        questions: [
            { question: "How old is Priya?", options: ["8", "9", "10"], correct_index: 1 },
            { question: "What day did she find the kitten?", options: ["Monday", "Tuesday", "Wednesday"], correct_index: 2 },
            { question: "What color were the kitten's paws?", options: ["Black", "White", "Orange"], correct_index: 1 },
            { question: "How old was the kitten according to the vet?", options: ["6 weeks", "8 weeks", "10 weeks"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_014",
        story: "The school football team, the Blue Eagles, won the regional championship after a thrilling match that ended 3-2 against the Red Wolves. The winning goal was scored in the final minute by a player named Jordan, who had only joined the team two months ago. Coach Rivera celebrated by treating the whole team to pizza after the game.",
        questions: [
            { question: "What is the school team's name?", options: ["Red Wolves", "Blue Eagles", "Green Hawks"], correct_index: 1 },
            { question: "What was the final score?", options: ["2-1", "3-2", "4-3"], correct_index: 1 },
            { question: "Who scored the winning goal?", options: ["Coach Rivera", "Jordan", "Alex"], correct_index: 1 },
            { question: "What did the coach treat the team to?", options: ["Ice cream", "Pizza", "Burgers"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_015",
        story: "Every year on the first weekend of June, the town of Cedar Falls hosts a kite festival at the park. Last year, over 500 kites were flown. A retired teacher named Mr. Huang won the award for the most creative kite — a giant red dragon that was 6 meters long. Children under 10 flew their kites in a special kids-only zone.",
        questions: [
            { question: "When does the kite festival take place?", options: ["Last weekend of May", "First weekend of June", "Second weekend of July"], correct_index: 1 },
            { question: "How many kites were flown last year?", options: ["300", "400", "500"], correct_index: 2 },
            { question: "Who won the most creative kite award?", options: ["Mr. Huang", "Mr. Rivera", "Mr. Chen"], correct_index: 0 },
            { question: "How long was the winning dragon kite?", options: ["4 meters", "6 meters", "8 meters"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_016",
        story: "Astronaut Helen Parks completed a 6-month mission aboard the International Space Station. During her stay, she conducted 14 experiments on plant growth in zero gravity. She returned to Earth on a Thursday morning and was greeted by her family and a team of scientists. Helen said the most challenging part was sleeping in microgravity.",
        questions: [
            { question: "How long was Helen's mission?", options: ["4 months", "6 months", "8 months"], correct_index: 1 },
            { question: "How many experiments did she conduct?", options: ["10", "12", "14"], correct_index: 2 },
            { question: "What day did she return to Earth?", options: ["Tuesday", "Wednesday", "Thursday"], correct_index: 2 },
            { question: "What did Helen say was most challenging?", options: ["Eating in space", "Sleeping in microgravity", "Communicating with Earth"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_017",
        story: "On a cold January evening, firefighter Sam rescued a family of four from a burning apartment on the 5th floor. Sam entered the building three times to ensure everyone was safe. The fire was caused by an unattended candle in the living room. No one was seriously injured. Sam received a bravery award from the mayor the following week.",
        questions: [
            { question: "What month did the fire occur?", options: ["December", "January", "February"], correct_index: 1 },
            { question: "Which floor was the apartment on?", options: ["3rd", "4th", "5th"], correct_index: 2 },
            { question: "How many times did Sam enter the building?", options: ["Two", "Three", "Four"], correct_index: 1 },
            { question: "What caused the fire?", options: ["A gas leak", "An electrical fault", "An unattended candle"], correct_index: 2 },
        ],
    },
    {
        id: "quiz_018",
        story: "Rosa runs a small flower shop called Bloom & Blossom. On Valentine's Day, she sold 320 bouquets of roses — her biggest sales day of the year. She started preparing at 5 AM and worked until 9 PM with the help of her two assistants, Mia and Jake. By the end of the day, she had run out of red roses but still had plenty of white and yellow ones.",
        questions: [
            { question: "What is the name of Rosa's flower shop?", options: ["Petal Palace", "Bloom & Blossom", "The Flower Hut"], correct_index: 1 },
            { question: "How many bouquets did she sell on Valentine's Day?", options: ["280", "300", "320"], correct_index: 2 },
            { question: "What time did Rosa start preparing?", options: ["4 AM", "5 AM", "6 AM"], correct_index: 1 },
            { question: "Which roses ran out by end of day?", options: ["Yellow", "White", "Red"], correct_index: 2 },
        ],
    },
    {
        id: "quiz_019",
        story: "The town of Birchwood built a new community garden in the spring. Volunteers planted tomatoes, carrots, herbs, and sunflowers. The garden covered 200 square meters and had 15 individual plots. Each plot was adopted by a local family. The youngest volunteer was a 6-year-old boy named Oliver who planted basil seeds with his mother.",
        questions: [
            { question: "What season was the garden built?", options: ["Summer", "Autumn", "Spring"], correct_index: 2 },
            { question: "How large was the community garden?", options: ["150 sq m", "200 sq m", "250 sq m"], correct_index: 1 },
            { question: "How many individual plots did the garden have?", options: ["10", "12", "15"], correct_index: 2 },
            { question: "How old was the youngest volunteer Oliver?", options: ["5", "6", "7"], correct_index: 1 },
        ],
    },
    {
        id: "quiz_020",
        story: "During the annual science symposium, Professor Lin presented her research on memory and aging to an audience of 150 scientists. She explained that regular mental exercises, such as puzzles and reading, can slow cognitive decline by up to 35%. Her study followed 400 participants over 10 years. After the presentation, she answered questions for 30 minutes.",
        questions: [
            { question: "How many scientists were in the audience?", options: ["100", "150", "200"], correct_index: 1 },
            { question: "By how much can mental exercises slow cognitive decline?", options: ["20%", "25%", "35%"], correct_index: 2 },
            { question: "How many participants were in her study?", options: ["200", "300", "400"], correct_index: 2 },
            { question: "How long did the Q&A session last?", options: ["20 minutes", "30 minutes", "45 minutes"], correct_index: 1 },
        ],
    },
];

module.exports = quizzes;