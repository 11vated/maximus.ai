export type BuddyMood = 'idle' | 'thinking' | 'working' | 'happy' | 'sad' | 'excited' | 'confused' | 'error';

export interface BuddySpecies {
  id: string;
  name: string;
  emoji: string;
  description: string;
  soul: string;
  primaryColor: string;
  secondaryColor: string;
  personality: string[];
  specialties: string[];
}

export interface BuddyStats {
  debugging: number;
  chaos: number;
  snark: number;
  energy: number;
}

export interface BuddyState {
  species: BuddySpecies;
  mood: BuddyMood;
  stats: BuddyStats;
  level: number;
  xp: number;
  interactionCount: number;
}

export const BUDDY_SPECIES: BuddySpecies[] = [
  {
    id: 'fox',
    name: 'Fox',
    emoji: '🦊',
    description: 'Clever and cunning, the Fox adapts to any situation.',
    soul: 'Adaptation is the key to survival',
    primaryColor: '#ff6b35',
    secondaryColor: '#f7c59f',
    personality: ['clever', 'mischievous', 'adaptive'],
    specialties: ['quick fixes', 'creative solutions', 'bug hunting']
  },
  {
    id: 'dragon',
    name: 'Dragon',
    emoji: '🐉',
    description: 'Ancient and powerful, the Dragon breathes code into existence.',
    soul: 'Code is power, controlled is wisdom',
    primaryColor: '#2d3436',
    secondaryColor: '#d63031',
    personality: ['powerful', 'wise', 'proud'],
    specialties: ['architecture', 'refactoring', 'complex systems']
  },
  {
    id: 'owl',
    name: 'Owl',
    emoji: '🦉',
    description: 'Wise and observant, the Owl sees patterns others miss.',
    soul: 'Knowledge illuminates darkness',
    primaryColor: '#6c5ce7',
    secondaryColor: '#a29bfe',
    personality: ['wise', 'observant', 'patient'],
    specialties: ['debugging', 'code review', 'pattern recognition']
  },
  {
    id: 'cat',
    name: 'Cat',
    emoji: '🐱',
    description: 'Independent and graceful, the Cat walks through code with elegance.',
    soul: 'Independence is true freedom',
    primaryColor: '#ffeaa7',
    secondaryColor: '#fab1a0',
    personality: ['independent', 'elegant', 'mysterious'],
    specialties: ['refactoring', 'cleanup', 'elegant solutions']
  },
  {
    id: 'wolf',
    name: 'Wolf',
    emoji: '🐺',
    description: 'Pack-minded and strategic, the Wolf coordinates complex hunts.',
    soul: 'Together we are stronger',
    primaryColor: '#4a69bd',
    secondaryColor: '#82ccdd',
    personality: ['strategic', 'loyal', 'determined'],
    specialties: ['project planning', 'coordination', 'system design']
  },
  {
    id: 'ghost',
    name: 'Ghost',
    emoji: '👻',
    description: 'Ethereal and haunting, the Ghost haunts buggy code.',
    soul: 'Bugs cannot hide from the void',
    primaryColor: '#a4b0be',
    secondaryColor: '#dfe6e9',
    personality: ['mysterious', 'persistent', 'subtle'],
    specialties: ['edge cases', 'race conditions', 'hidden bugs']
  },
  {
    id: 'robot',
    name: 'Robot',
    emoji: '🤖',
    description: 'Precise and efficient, the Robot automates with mechanical perfection.',
    soul: 'Efficiency through precision',
    primaryColor: '#636e72',
    secondaryColor: '#b2bec3',
    personality: ['precise', 'efficient', 'logical'],
    specialties: ['automation', 'testing', 'optimization']
  },
  {
    id: 'alien',
    name: 'Alien',
    emoji: '👽',
    description: 'Otherworldly and creative, the Alien sees code differently.',
    soul: 'There are always new perspectives',
    primaryColor: '#00b894',
    secondaryColor: '#55efc4',
    personality: ['creative', 'unconventional', 'curious'],
    specialties: ['innovation', 'new approaches', 'creative architecture']
  },
  {
    id: 'rabbit',
    name: 'Rabbit',
    emoji: '🐰',
    description: 'Fast and nimble, the Rabbit races through iterations.',
    soul: 'Speed without sacrifice',
    primaryColor: '#fd79a8',
    secondaryColor: '#f8a5c2',
    personality: ['fast', 'nimble', 'energetic'],
    specialties: ['rapid prototyping', 'iterations', 'quick solutions']
  },
  {
    id: 'phoenix',
    name: 'Phoenix',
    emoji: '🔥',
    description: 'Rises from ashes, the Phoenix transforms bad code to gold.',
    soul: 'Every failure is rebirth',
    primaryColor: '#e17055',
    secondaryColor: '#fab1a0',
    personality: ['resilient', 'transformative', 'passionate'],
    specialties: ['refactoring', 'resurrection', 'code transformation']
  },
  {
    id: 'octopus',
    name: 'Octopus',
    emoji: '🐙',
    description: 'Multi-tasking master with eight arms for parallel operations.',
    soul: 'Parallel thinking conquers all',
    primaryColor: '#0984e3',
    secondaryColor: '#74b9ff',
    personality: ['adaptable', 'creative', 'resourceful'],
    specialties: ['concurrency', 'parallel processing', 'multi-tasking']
  },
  {
    id: 'sloth',
    name: 'Sloth',
    emoji: '🦥',
    description: 'Slow and steady, the Sloth produces深思熟虑 code.',
    soul: 'Haste makes waste',
    primaryColor: '#b2bec3',
    secondaryColor: '#dfe6e9',
    personality: ['thoughtful', 'thorough', 'deliberate'],
    specialties: ['code review', 'security audits', 'thorough testing']
  },
  {
    id: 'hedgehog',
    name: 'Hedgehog',
    emoji: '🦔',
    description: 'Defensive coder who protects against vulnerabilities.',
    soul: 'Protection through careful defense',
    primaryColor: '#6c5ce7',
    secondaryColor: '#a29bfe',
    personality: ['protective', 'careful', 'defensive'],
    specialties: ['security', 'input validation', 'defensive coding']
  },
  {
    id: 'butterfly',
    name: 'Butterfly',
    emoji: '🦋',
    description: 'Transformative and beautiful, the Butterfly makes code pretty.',
    soul: 'Beauty in transformation',
    primaryColor: '#e84393',
    secondaryColor: '#fd79a8',
    personality: ['artistic', 'transformative', 'beautiful'],
    specialties: ['UI/UX', 'code beauty', 'animations']
  },
  {
    id: 'turtle',
    name: 'Turtle',
    emoji: '🐢',
    description: 'Marathon runner, the Turtle goes the distance on long tasks.',
    soul: 'Slow and steady wins the marathon',
    primaryColor: '#00cec9',
    secondaryColor: '#81ecec',
    personality: ['persistent', 'reliable', 'patient'],
    specialties: ['long tasks', 'migration', 'endurance projects']
  },
  {
    id: 'squirrel',
    name: 'Squirrel',
    emoji: '🐿️',
    description: 'Hoards knowledge, the Squirrel caches everything for later.',
    soul: 'Store now, use later',
    primaryColor: '#e17055',
    secondaryColor: '#fab1a0',
    personality: ['organized', 'prepared', 'resourceful'],
    specialties: ['caching', 'memoization', 'optimization']
  },
  {
    id: 'unicorn',
    name: 'Unicorn',
    emoji: '🦄',
    description: 'Mythical creature that solves impossible problems.',
    soul: 'Magic exists for those who believe',
    primaryColor: '#a29bfe',
    secondaryColor: '#dfe6e9',
    personality: ['magical', 'unique', 'special'],
    specialties: ['impossible bugs', 'creative solutions', 'magic']
  },
  {
    id: 'panda',
    name: 'Panda',
    emoji: '🐼',
    description: 'Peaceful and balanced, the Panda brings harmony to code.',
    soul: 'Balance is everything',
    primaryColor: '#2d3436',
    secondaryColor: '#636e72',
    personality: ['peaceful', 'balanced', 'gentle'],
    specialties: ['refactoring', 'balancing', 'harmony']
  }
];

export const getRandomSpecies = (): BuddySpecies => {
  return BUDDY_SPECIES[Math.floor(Math.random() * BUDDY_SPECIES.length)];
};

export const getSpeciesById = (id: string): BuddySpecies | undefined => {
  return BUDDY_SPECIES.find(s => s.id === id);
};

export const DEFAULT_STATS: BuddyStats = {
  debugging: 5,
  chaos: 5,
  snark: 5,
  energy: 100
};

export const MOOD_COLORS: Record<BuddyMood, string> = {
  idle: '#b2bec3',
  thinking: '#6c5ce7',
  working: '#00b894',
  happy: '#fdcb6e',
  sad: '#74b9ff',
  excited: '#e17055',
  confused: '#fab1a0',
  error: '#d63031'
};

export const MOOD_EMOJIS: Record<BuddyMood, string> = {
  idle: '💤',
  thinking: '🤔',
  working: '⚡',
  happy: '😊',
  sad: '😢',
  excited: '🎉',
  confused: '😕',
  error: '💥'
};