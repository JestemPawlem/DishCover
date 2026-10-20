import api from './client';
import type { RecipeSummary, RecipeRecommendation, LikeResponse } from '../types/recipe';


export const getRecommendations = async (limit: number = 10): Promise<RecipeRecommendation[]> => {
    const response = await api.get<RecipeRecommendation[]>(`/recipes/recommendations?limit=${limit}`);
    return response.data;
};

export const getOnboardingRecipes = async (limit: number = 12): Promise<RecipeSummary[]> => {
    const response = await api.get<RecipeRecommendation[]>(`/recipes/onboarding?limit=${limit}`);
    return response.data;
};

export const toggleLikeRecipe = async (recipeId: number): Promise<LikeResponse> => {
    const response = await api.post<LikeResponse>(`recipes/${recipeId}/like`);
    return response.data;
}