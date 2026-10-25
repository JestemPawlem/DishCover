import type { components } from './api';

type Schemas = components['schemas'];

export type Token = Schemas['Token'];
export type UserCreate = Schemas['UserCreate'];
export type UserLogin = Schemas['UserLogin'];
export type UserResponse = Schemas['UserResponse'];