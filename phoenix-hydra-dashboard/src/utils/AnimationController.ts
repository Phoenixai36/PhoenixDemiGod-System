/**
 * Animation Controller for 3D Character
 * Manages character animations and state transitions
 */

export interface AnimationState {
  name: string;
  duration: number;
  loop: boolean;
  priority: number;
}

export class AnimationController {
  private currentAnimation: string = 'idle';
  private animationQueue: AnimationState[] = [];
  private isPlaying: boolean = false;
  private splineObject: any = null;

  // Available animations with their properties
  private animations: Record<string, AnimationState> = {
    idle: {
      name: 'idle',
      duration: 0,
      loop: true,
      priority: 0
    },
    wave: {
      name: 'wave',
      duration: 2000,
      loop: false,
      priority: 2
    },
    thinking: {
      name: 'thinking',
      duration: 3000,
      loop: true,
      priority: 1
    },
    coding: {
      name: 'coding',
      duration: 4000,
      loop: true,
      priority: 1
    },
    celebrate: {
      name: 'celebrate',
      duration: 3000,
      loop: false,
      priority: 3
    },
    confused: {
      name: 'confused',
      duration: 2500,
      loop: false,
      priority: 2
    },
    listening: {
      name: 'listening',
      duration: 0,
      loop: true,
      priority: 1
    },
    levelup: {
      name: 'levelup',
      duration: 5000,
      loop: false,
      priority: 4
    },
    typing: {
      name: 'typing',
      duration: 0,
      loop: true,
      priority: 1
    },
    explaining: {
      name: 'explaining',
      duration: 0,
      loop: true,
      priority: 1
    }
  };

  /**
   * Set the Spline object reference
   */
  setSplineObject(splineObject: any): void {
    this.splineObject = splineObject;
  }

  /**
   * Play an animation with optional priority override
   */
  playAnimation(animationName: string, force: boolean = false): boolean {
    const animation = this.animations[animationName];
    
    if (!animation) {
      console.warn(`Animation "${animationName}" not found`);
      return false;
    }

    // Check if we should interrupt current animation
    const currentAnimationState = this.animations[this.currentAnimation];
    if (!force && currentAnimationState && animation.priority <= currentAnimationState.priority) {
      // Queue the animation if it's lower priority
      this.queueAnimation(animation);
      return false;
    }

    // Play the animation
    this.executeAnimation(animation);
    return true;
  }

  /**
   * Queue an animation to play after current one finishes
   */
  private queueAnimation(animation: AnimationState): void {
    // Remove any existing queued animation with same name
    this.animationQueue = this.animationQueue.filter(a => a.name !== animation.name);
    
    // Add to queue
    this.animationQueue.push(animation);
    
    // Sort by priority
    this.animationQueue.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Execute the animation
   */
  private executeAnimation(animation: AnimationState): void {
    this.currentAnimation = animation.name;
    this.isPlaying = true;

    // Trigger Spline animation if object is available
    if (this.splineObject) {
      try {
        // This would be the actual Spline animation trigger
        // Replace with actual Spline API calls
        this.splineObject.emitEvent('mouseDown', animation.name);
        console.log(`Playing animation: ${animation.name}`);
      } catch (error) {
        console.error('Failed to play Spline animation:', error);
      }
    }

    // Handle animation completion
    if (!animation.loop && animation.duration > 0) {
      setTimeout(() => {
        this.onAnimationComplete();
      }, animation.duration);
    }
  }

  /**
   * Handle animation completion
   */
  private onAnimationComplete(): void {
    this.isPlaying = false;

    // Play next queued animation or return to idle
    if (this.animationQueue.length > 0) {
      const nextAnimation = this.animationQueue.shift()!;
      this.executeAnimation(nextAnimation);
    } else {
      // Return to idle
      this.executeAnimation(this.animations.idle);
    }
  }

  /**
   * Stop current animation and clear queue
   */
  stopAnimation(): void {
    this.animationQueue = [];
    this.isPlaying = false;
    this.executeAnimation(this.animations.idle);
  }

  /**
   * Get current animation name
   */
  getCurrentAnimation(): string {
    return this.currentAnimation;
  }

  /**
   * Check if an animation is currently playing
   */
  isAnimationPlaying(): boolean {
    return this.isPlaying;
  }

  /**
   * Get available animations
   */
  getAvailableAnimations(): string[] {
    return Object.keys(this.animations);
  }

  /**
   * Add custom animation
   */
  addAnimation(name: string, animation: Omit<AnimationState, 'name'>): void {
    this.animations[name] = {
      name,
      ...animation
    };
  }

  /**
   * Trigger contextual animation based on message content
   */
  triggerContextualAnimation(messageContent: string): void {
    const content = messageContent.toLowerCase();

    if (content.includes('error') || content.includes('failed') || content.includes('wrong')) {
      this.playAnimation('confused');
    } else if (content.includes('success') || content.includes('completed') || content.includes('done')) {
      this.playAnimation('celebrate');
    } else if (content.includes('code') || content.includes('programming') || content.includes('function')) {
      this.playAnimation('coding');
    } else if (content.includes('explain') || content.includes('how') || content.includes('what')) {
      this.playAnimation('explaining');
    } else if (content.includes('think') || content.includes('consider') || content.includes('analyze')) {
      this.playAnimation('thinking');
    } else {
      this.playAnimation('listening');
    }
  }

  /**
   * Trigger emotion-based animation
   */
  triggerEmotionAnimation(emotion: 'happy' | 'sad' | 'excited' | 'confused' | 'focused'): void {
    switch (emotion) {
      case 'happy':
        this.playAnimation('celebrate');
        break;
      case 'sad':
        this.playAnimation('confused');
        break;
      case 'excited':
        this.playAnimation('wave');
        break;
      case 'confused':
        this.playAnimation('confused');
        break;
      case 'focused':
        this.playAnimation('coding');
        break;
      default:
        this.playAnimation('idle');
    }
  }
}