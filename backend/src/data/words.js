const words = [
    // Body Parts (10)
    { id: "word_001", word: "BRAIN", hint: "The organ used for thinking.", category: "Body Parts", difficulty: "easy" },
    { id: "word_002", word: "HEART", hint: "Pumps blood throughout your body.", category: "Body Parts", difficulty: "easy" },
    { id: "word_003", word: "KIDNEY", hint: "Filters waste from the blood.", category: "Body Parts", difficulty: "medium" },
    { id: "word_004", word: "LIVER", hint: "The largest internal organ.", category: "Body Parts", difficulty: "medium" },
    { id: "word_005", word: "SPINE", hint: "The backbone that supports your body.", category: "Body Parts", difficulty: "easy" },
    { id: "word_006", word: "LUNG", hint: "Used for breathing air.", category: "Body Parts", difficulty: "easy" },
    { id: "word_007", word: "RETINA", hint: "Light-sensitive layer inside the eye.", category: "Body Parts", difficulty: "hard" },
    { id: "word_008", word: "NEURON", hint: "A nerve cell that transmits signals.", category: "Body Parts", difficulty: "hard" },
    { id: "word_009", word: "FEMUR", hint: "The longest bone in the human body.", category: "Body Parts", difficulty: "medium" },
    { id: "word_010", word: "CORTEX", hint: "The outer layer of the brain.", category: "Body Parts", difficulty: "hard" },

    // Nature (10)
    { id: "word_011", word: "RIVER", hint: "A large natural stream of water.", category: "Nature", difficulty: "easy" },
    { id: "word_012", word: "CLOUD", hint: "A visible mass of water vapor in the sky.", category: "Nature", difficulty: "easy" },
    { id: "word_013", word: "FOREST", hint: "A large area covered with trees.", category: "Nature", difficulty: "easy" },
    { id: "word_014", word: "VALLEY", hint: "A low area between hills or mountains.", category: "Nature", difficulty: "medium" },
    { id: "word_015", word: "GLACIER", hint: "A slow-moving mass of ice.", category: "Nature", difficulty: "hard" },
    { id: "word_016", word: "CANYON", hint: "A deep gorge, often with a river.", category: "Nature", difficulty: "medium" },
    { id: "word_017", word: "MARSH", hint: "A wetland area often covered with reeds.", category: "Nature", difficulty: "medium" },
    { id: "word_018", word: "TUNDRA", hint: "A vast, flat, treeless Arctic region.", category: "Nature", difficulty: "hard" },
    { id: "word_019", word: "DUNE", hint: "A mound of sand formed by the wind.", category: "Nature", difficulty: "easy" },
    { id: "word_020", word: "CORAL", hint: "A marine organism that builds reefs.", category: "Nature", difficulty: "medium" },

    // Food (10)
    { id: "word_021", word: "MANGO", hint: "A tropical fruit with a yellow-orange flesh.", category: "Food", difficulty: "easy" },
    { id: "word_022", word: "QUINOA", hint: "A grain-like seed rich in protein.", category: "Food", difficulty: "hard" },
    { id: "word_023", word: "WALNUT", hint: "A wrinkled nut that looks like a brain.", category: "Food", difficulty: "medium" },
    { id: "word_024", word: "LENTIL", hint: "A small legume used in soups.", category: "Food", difficulty: "medium" },
    { id: "word_025", word: "GINGER", hint: "A spicy root used in cooking and medicine.", category: "Food", difficulty: "medium" },
    { id: "word_026", word: "PAPAYA", hint: "A tropical fruit with orange flesh.", category: "Food", difficulty: "medium" },
    { id: "word_027", word: "ALMOND", hint: "A nut often eaten as a healthy snack.", category: "Food", difficulty: "medium" },
    { id: "word_028", word: "BARLEY", hint: "A grain used to make beer and bread.", category: "Food", difficulty: "medium" },
    { id: "word_029", word: "TURNIP", hint: "A round root vegetable, often white.", category: "Food", difficulty: "medium" },
    { id: "word_030", word: "FIG", hint: "A sweet fruit with tiny seeds inside.", category: "Food", difficulty: "easy" },

    // Animals (10)
    { id: "word_031", word: "DOLPHIN", hint: "An intelligent marine mammal.", category: "Animals", difficulty: "easy" },
    { id: "word_032", word: "JAGUAR", hint: "The largest wild cat in the Americas.", category: "Animals", difficulty: "medium" },
    { id: "word_033", word: "PANDA", hint: "A black-and-white bear from China.", category: "Animals", difficulty: "easy" },
    { id: "word_034", word: "FALCON", hint: "A fast bird of prey.", category: "Animals", difficulty: "medium" },
    { id: "word_035", word: "GECKO", hint: "A small lizard known for climbing walls.", category: "Animals", difficulty: "medium" },
    { id: "word_036", word: "BISON", hint: "A large, shaggy North American bovine.", category: "Animals", difficulty: "medium" },
    { id: "word_037", word: "OTTER", hint: "A playful semi-aquatic mammal.", category: "Animals", difficulty: "easy" },
    { id: "word_038", word: "LEMUR", hint: "A primate found only in Madagascar.", category: "Animals", difficulty: "hard" },
    { id: "word_039", word: "MANTA", hint: "A large flat ray that swims in oceans.", category: "Animals", difficulty: "hard" },
    { id: "word_040", word: "HYENA", hint: "A scavenging animal known for its laugh.", category: "Animals", difficulty: "medium" },

    // Technology (12)
    { id: "word_041", word: "SERVER", hint: "A computer that provides data to others.", category: "Technology", difficulty: "medium" },
    { id: "word_042", word: "PIXEL", hint: "The smallest unit of a digital image.", category: "Technology", difficulty: "medium" },
    { id: "word_043", word: "ROUTER", hint: "A device that directs network traffic.", category: "Technology", difficulty: "medium" },
    { id: "word_044", word: "CACHE", hint: "Temporary storage for fast data access.", category: "Technology", difficulty: "hard" },
    { id: "word_045", word: "SENSOR", hint: "A device that detects physical input.", category: "Technology", difficulty: "easy" },
    { id: "word_046", word: "ALGORITHM", hint: "A step-by-step set of instructions.", category: "Technology", difficulty: "hard" },
    { id: "word_047", word: "FIRMWARE", hint: "Software embedded in hardware devices.", category: "Technology", difficulty: "hard" },
    { id: "word_048", word: "BANDWIDTH", hint: "The capacity of a network connection.", category: "Technology", difficulty: "hard" },
    { id: "word_049", word: "LATENCY", hint: "Delay before data transfer begins.", category: "Technology", difficulty: "hard" },
    { id: "word_050", word: "DATABASE", hint: "An organized collection of structured data.", category: "Technology", difficulty: "medium" },
    { id: "word_051", word: "TOKEN", hint: "A unit used in authentication or AI processing.", category: "Technology", difficulty: "medium" },
    { id: "word_052", word: "CLUSTER", hint: "A group of computers working together.", category: "Technology", difficulty: "medium" },
];

module.exports = words;