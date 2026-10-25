import api from './client';
import type {
    Recipe,
    RecipeRecommendation,
    RecipeSummary,
    LikeResponse
} from '../types/recipe';


export const getRecommendations = async (limit: number = 12): Promise<RecipeRecommendation[]> => {
    const response = await api.get<RecipeRecommendation[]>(`/recipes/recommendations?limit=${limit}`);
    return response.data;
};


export const getOnboardingRecipes = async (limit: number = 12): Promise<RecipeSummary[]> => {
    const response = await api.get<RecipeSummary[]>(`/recipes/onboarding?limit=${limit}`);
    return response.data;
};


export const searchRecipes = async (q: string, limit: number = 20, offset: number = 0): Promise<RecipeSummary[]> => {
    const response = await api.get<RecipeSummary[]>('/recipes/search', {
        params: { q, limit, offset }
    });
    return response.data;
};


export const getRecipe = async (id: number): Promise<Recipe> => {
    const response = await api.get<Recipe>(`/recipes/${id}`);
    return response.data;
};


export const getSimilarRecipes = async (id: number, limit: number = 6): Promise<RecipeSummary[]> => {
    const response = await api.get<RecipeSummary[]>(`/recipes/${id}/similar`, {
        params: { limit }
    });
    return response.data;
};


export const toggleLikeRecipe = async (recipeId: number): Promise<LikeResponse> => {
    const response = await api.post<LikeResponse>(`/recipes/${recipeId}/like`, {});
    return response.data;
};


export const getLikedRecipes = async (limit: number = 20, offset: number = 0): Promise<RecipeSummary[]> => {
    const response = await api.get<RecipeSummary[]>('/users/me/liked', {
        params: { limit, offset }
    });
    return response.data;
};