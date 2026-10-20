export interface RecipeSummary {
    id: number;
    name: string;
    minutes: number | null;
    description: number | null;
}

export interface RecipeRecommendation extends RecipeSummary {
    similarity: number | null;
}

export interface LikeResponse {
    liked: boolean;
}