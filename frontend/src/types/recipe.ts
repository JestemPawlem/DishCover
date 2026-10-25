import type { components } from './api';

type Schemas = components['schemas'];

export type RecipeSummary = Schemas['RecipeSummary'];
export type Recipe = Schemas['Recipe'];
export type LikeResponse = Schemas['LikeResponse'];