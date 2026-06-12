import { DatasetProfile, CleaningStrategy, MLPipeline, MLMetrics } from './schemas';

export interface PipelineState {
  currentPhase: 'profiling' | 'strategizing' | 'executing' | 'validating';
  profile?: DatasetProfile;
  strategy?: CleaningStrategy;
  pipeline?: MLPipeline;
  artifacts?: {
    cleanedDataPath: string;
    modelPath: string;
    metrics: MLMetrics;
  };
  errors?: any[];
}

export class StateManager<T extends PipelineState> {
  private state: T;

  constructor(initialState: T) {
    this.state = initialState;
  }

  get(): T {
    return this.state;
  }

  update(updates: Partial<T>): void {
    this.state = { ...this.state, ...updates };
  }

  addError(error: any): void {
    if (!this.state.errors) {
      this.state.errors = [];
    }
    this.state.errors.push(error);
  }
}
