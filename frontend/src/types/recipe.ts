export interface RecipeSummary {
    id: number;
    name: string;
    minutes: number;
    description: string | null;
    like_count: number;
}

export interface RecipeRecommendation extends RecipeSummary {
    similarity: number | null;
}

export interface LikeResponse {
    liked: boolean;
}