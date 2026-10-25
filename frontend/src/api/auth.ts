import api from './client';
import type { UserCreate, UserLogin, UserResponse } from '../types/auth';
import type { Token } from '../types/token';


export const registerUser = async (data: UserCreate): Promise<UserResponse> => {
    const response = await api.post<UserResponse>('/auth/register', data);
    return response.data;
};

export const loginUser = async (data: UserLogin): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', data);
    return response.data;
};

export const getCurrentUser = async (): Promise<UserResponse> => {
    const response = await api.get<UserResponse>('/users/me');
    return response.data;
};