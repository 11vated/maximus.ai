import { create } from 'zustand';
import type { 
  BuddyState, 
  BuddyMood, 
  BuddyStats,
  BuddySpecies
} from '../components/BuddySystem/BuddySpecies';
import { getRandomSpecies, DEFAULT_STATS } from '../components/BuddySystem/BuddySpecies';

interface BuddyStore {
  buddy: BuddyState;
  setMood: (mood: BuddyMood) => void;
  setSpecies: (species: BuddySpecies) => void;
  randomize: () => void;
  addXP: (amount: number) => void;
  updateStats: (stats: Partial<BuddyStats>) => void;
  interact: (type: 'click' | 'hover' | 'pet') => void;
  levelUp: () => void;
  reset: () => void;
}

const createInitialBuddy = (): BuddyState => {
  const species = getRandomSpecies();
  return {
    species,
    mood: 'idle',
    stats: { ...DEFAULT_STATS },
    level: 1,
    xp: 0,
    interactionCount: 0
  };
};

export const useBuddyStore = create<BuddyStore>((set) => ({
  buddy: createInitialBuddy(),
  
  setMood: (mood) => set((state) => ({
    buddy: { ...state.buddy, mood }
  })),
  
  setSpecies: (species) => set((state) => ({
    buddy: { ...state.buddy, species }
  })),
  
  randomize: () => set({ buddy: createInitialBuddy() }),
  
  addXP: (amount) => set((state) => {
    const newXP = state.buddy.xp + amount;
    const xpForLevel = state.buddy.level * 100;
    let newLevel = state.buddy.level;
    let remainingXP = newXP;
    
    while (remainingXP >= xpForLevel) {
      remainingXP -= xpForLevel;
      newLevel++;
    }
    
    return {
      buddy: {
        ...state.buddy,
        xp: remainingXP,
        level: newLevel,
        stats: {
          ...state.buddy.stats,
          energy: Math.min(100, state.buddy.stats.energy + 5)
        }
      }
    };
  }),
  
  updateStats: (statsUpdate) => set((state) => ({
    buddy: {
      ...state.buddy,
      stats: { ...state.buddy.stats, ...statsUpdate }
    }
  })),
  
  interact: (type) => set((state) => {
    const energyCost = type === 'click' ? 5 : type === 'pet' ? 10 : 0;
    
    // Random mood change on interaction
    const moods: BuddyMood[] = ['idle', 'happy', 'thinking'];
    const newMood = type === 'click' 
      ? moods[Math.floor(Math.random() * moods.length)]
      : 'happy';
    
    return {
      buddy: {
        ...state.buddy,
        interactionCount: state.buddy.interactionCount + 1,
        stats: {
          ...state.buddy.stats,
          energy: Math.max(0, state.buddy.stats.energy - energyCost)
        },
        mood: newMood
      }
    };
  }),
  
  levelUp: () => set((state) => {
    const newLevel = state.buddy.level + 1;
    const newStats = {
      debugging: Math.min(10, state.buddy.stats.debugging + 1),
      chaos: Math.min(10, state.buddy.stats.chaos + 1),
      snark: Math.min(10, state.buddy.stats.snark + 1),
      energy: 100
    };
    
    return {
      buddy: {
        ...state.buddy,
        level: newLevel,
        stats: newStats,
        mood: 'excited'
      }
    };
  }),
  
  reset: () => set({ buddy: createInitialBuddy() })
}));

export const getBuddyFromStore = () => useBuddyStore.getState().buddy;