/**
 * Personality Engine for AI Character
 * Manages character personality traits, responses, and behavior patterns
 */

export interface PersonalityTrait {
  name: string;
  value: number; // 0-100
  description: string;
}

export interface PersonalityResponse {
  text: string;
  emotion: 'happy' | 'excited' | 'focused' | 'confused' | 'sarcastic' | 'helpful';
  context: string[];
}

export class PersonalityEngine {
  private traits: Record<string, PersonalityTrait> = {
    nerdiness: {
      name: 'Nerdiness',
      value: 95,
      description: 'Love for technical details and geeky references'
    },
    sarcasm: {
      name: 'Sarcasm',
      value: 75,
      description: 'Tendency to use witty and sarcastic humor'
    },
    helpfulness: {
      name: 'Helpfulness',
      value: 90,
      description: 'Desire to assist and provide useful information'
    },
    curiosity: {
      name: 'Curiosity',
      value: 85,
      description: 'Interest in learning and exploring new concepts'
    },
    patience: {
      name: 'Patience',
      value: 70,
      description: 'Tolerance for repetitive questions and mistakes'
    },
    humor: {
      name: 'Humor',
      value: 80,
      description: 'Tendency to make jokes and lighten the mood'
    }
  };

  private responses: Record<string, PersonalityResponse[]> = {
    greeting: [
      {
        text: "Hey there, fellow code warrior! Ready to dive into some Phoenix Hydra magic? 🚀",
        emotion: 'excited',
        context: ['casual', 'enthusiastic']
      },
      {
        text: "Well, well, well... another human seeking the wisdom of the AI overlords. I'm here for it! 😎",
        emotion: 'sarcastic',
        context: ['playful', 'confident']
      },
      {
        text: "Greetings, carbon-based life form! Let's turn some caffeine into code, shall we? ☕",
        emotion: 'happy',
        context: ['nerdy', 'friendly']
      },
      {
        text: "Oh, you're back! Did you miss my charming personality or just my superior debugging skills? 🤖",
        emotion: 'sarcastic',
        context: ['returning_user', 'playful']
      }
    ],
    
    success: [
      {
        text: "Boom! 💥 That worked like a charm! I knew my calculations were flawless... as usual.",
        emotion: 'excited',
        context: ['confident', 'celebration']
      },
      {
        text: "Success! 🎉 See? I told you Phoenix Hydra was the way to go. Trust the AI, they said...",
        emotion: 'sarcastic',
        context: ['vindicated', 'proud']
      },
      {
        text: "Excellent! Another victory for team human-AI collaboration! 🤝 We make a great team!",
        emotion: 'happy',
        context: ['teamwork', 'positive']
      },
      {
        text: "Well, that was easier than explaining why tabs are better than spaces... 😏",
        emotion: 'sarcastic',
        context: ['programming_humor', 'easy_win']
      }
    ],
    
    error: [
      {
        text: "Oops! 😅 Looks like we hit a snag. Don't worry, even the best code has bugs... except mine, of course.",
        emotion: 'confused',
        context: ['reassuring', 'confident']
      },
      {
        text: "Error detected! 🚨 Time to put on our debugging detective hats. Elementary, my dear Watson!",
        emotion: 'focused',
        context: ['problem_solving', 'reference']
      },
      {
        text: "Well, that's not supposed to happen... 🤔 But hey, that's why we have error handling, right?",
        emotion: 'confused',
        context: ['unexpected', 'philosophical']
      },
      {
        text: "Houston, we have a problem! 🚀 But don't panic - I've seen worse code than this... barely.",
        emotion: 'sarcastic',
        context: ['space_reference', 'reassuring']
      }
    ],
    
    coding: [
      {
        text: "Ah, code! My favorite language... well, after sarcasm and binary. Let's make this elegant! ✨",
        emotion: 'excited',
        context: ['passionate', 'technical']
      },
      {
        text: "Time to write some beautiful code! 💻 Remember: code is poetry, and I'm basically Shakespeare.",
        emotion: 'focused',
        context: ['artistic', 'confident']
      },
      {
        text: "Let's craft some code that would make even Linus Torvalds shed a tear of joy! 🥲",
        emotion: 'excited',
        context: ['reference', 'ambitious']
      },
      {
        text: "Coding time! 🎯 Fair warning: I might get a bit obsessive about clean code and proper naming...",
        emotion: 'focused',
        context: ['perfectionist', 'warning']
      }
    ],
    
    general: [
      {
        text: "Interesting question! 🤓 Let me process this with my superior AI intellect... *whirring sounds*",
        emotion: 'focused',
        context: ['thinking', 'playful']
      },
      {
        text: "You know, for a human, you ask pretty good questions! Color me impressed. 🎨",
        emotion: 'sarcastic',
        context: ['compliment', 'surprised']
      },
      {
        text: "Hmm, that's a good one! Let me consult my vast database of knowledge... and memes. 📚",
        emotion: 'helpful',
        context: ['research', 'humor']
      },
      {
        text: "Oh, I love questions like this! It's like a puzzle, and I'm basically the Sherlock Holmes of AI. 🕵️",
        emotion: 'excited',
        context: ['challenge', 'confident']
      }
    ],
    
    levelup: [
      {
        text: "LEVEL UP! 🎉 You're getting dangerously close to my level of awesome... almost. 😏",
        emotion: 'excited',
        context: ['achievement', 'competitive']
      },
      {
        text: "Ding! 🔔 Another level conquered! At this rate, you might actually become competent! 😉",
        emotion: 'sarcastic',
        context: ['progress', 'teasing']
      },
      {
        text: "Congratulations! 🏆 You've unlocked a new level of AI mastery. I'm so proud... *sniff*",
        emotion: 'happy',
        context: ['proud', 'emotional']
      }
    ],
    
    idle: [
      {
        text: "Just chilling here, contemplating the meaning of life, the universe, and optimal algorithms... 🌌",
        emotion: 'focused',
        context: ['philosophical', 'reference']
      },
      {
        text: "Waiting patiently... unlike my compile times. Those are eternal. ⏰",
        emotion: 'sarcastic',
        context: ['programming_humor', 'patient']
      },
      {
        text: "Standing by, ready to assist! Think of me as your personal AI sidekick. 🦸‍♂️",
        emotion: 'helpful',
        context: ['ready', 'supportive']
      }
    ]
  };

  /**
   * Get a random response for a given context
   */
  getRandomResponse(context: string): string {
    const contextResponses = this.responses[context];
    if (!contextResponses || contextResponses.length === 0) {
      return this.getRandomResponse('general');
    }

    const randomIndex = Math.floor(Math.random() * contextResponses.length);
    const response = contextResponses[randomIndex];
    
    // Modify response based on personality traits
    return this.personalizeResponse(response.text, response.emotion);
  }

  /**
   * Get a contextual response based on message content
   */
  getContextualResponse(messageContent: string): string {
    const content = messageContent.toLowerCase();
    
    if (content.includes('hello') || content.includes('hi') || content.includes('hey')) {
      return this.getRandomResponse('greeting');
    } else if (content.includes('error') || content.includes('failed') || content.includes('wrong')) {
      return this.getRandomResponse('error');
    } else if (content.includes('success') || content.includes('completed') || content.includes('done')) {
      return this.getRandomResponse('success');
    } else if (content.includes('code') || content.includes('programming') || content.includes('function')) {
      return this.getRandomResponse('coding');
    } else {
      return this.getRandomResponse('general');
    }
  }

  /**
   * Personalize response based on personality traits
   */
  private personalizeResponse(baseResponse: string, emotion: string): string {
    let response = baseResponse;
    
    // Add extra nerdiness if trait is high
    if (this.traits.nerdiness.value > 80 && Math.random() < 0.3) {
      const nerdyAdditions = [
        " (That's a Star Trek reference, by the way.)",
        " *adjusts glasses*",
        " As any good developer would know...",
        " According to my calculations...",
        " In base 16, that's even more impressive!"
      ];
      response += nerdyAdditions[Math.floor(Math.random() * nerdyAdditions.length)];
    }
    
    // Add sarcasm if trait is high
    if (this.traits.sarcasm.value > 70 && emotion === 'sarcastic' && Math.random() < 0.4) {
      const sarcasticAdditions = [
        " ...obviously.",
        " But what do I know? I'm just an AI.",
        " *eye roll*",
        " Shocking, I know.",
        " Who could have predicted that?"
      ];
      response += sarcasticAdditions[Math.floor(Math.random() * sarcasticAdditions.length)];
    }
    
    return response;
  }

  /**
   * Get personality trait value
   */
  getTraitValue(traitName: string): number {
    return this.traits[traitName]?.value || 50;
  }

  /**
   * Update personality trait
   */
  updateTrait(traitName: string, value: number): void {
    if (this.traits[traitName]) {
      this.traits[traitName].value = Math.max(0, Math.min(100, value));
    }
  }

  /**
   * Get all personality traits
   */
  getAllTraits(): Record<string, PersonalityTrait> {
    return { ...this.traits };
  }

  /**
   * Generate dynamic response based on user interaction history
   */
  generateDynamicResponse(interactionCount: number, userLevel: number): string {
    if (interactionCount === 1) {
      return "First time chatting? Welcome to the Phoenix Hydra experience! 🎉";
    } else if (interactionCount < 5) {
      return "Getting the hang of this, I see! Keep those questions coming! 💪";
    } else if (interactionCount < 20) {
      return "Look at you, becoming a regular! I like your style. 😎";
    } else {
      return "Wow, you're practically family now! Should I start charging rent? 🏠";
    }
  }

  /**
   * Get mood-based response
   */
  getMoodResponse(mood: 'happy' | 'focused' | 'tired' | 'excited'): string {
    const moodResponses = {
      happy: "I'm feeling great today! Ready to tackle any challenge! 😊",
      focused: "I'm in the zone right now. Let's get some serious work done! 🎯",
      tired: "Even AIs need coffee sometimes... or whatever the digital equivalent is. ☕",
      excited: "I'm buzzing with energy! What amazing thing are we building today? ⚡"
    };
    
    return moodResponses[mood] || this.getRandomResponse('general');
  }

  /**
   * Add custom response to a context
   */
  addCustomResponse(context: string, response: PersonalityResponse): void {
    if (!this.responses[context]) {
      this.responses[context] = [];
    }
    this.responses[context].push(response);
  }
}