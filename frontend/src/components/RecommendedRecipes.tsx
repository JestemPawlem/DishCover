import { useState, useEffect, useCallback } from 'react';

import { SimpleGrid, Loader, Center, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';

import { getRecommendations } from '../api/recipes';
import type { RecipeSummary } from '../types/recipe';
import { RecipeCard } from './RecipeCard';

interface Props {
  isLoggedIn: boolean;
  refreshKey: number;
}

export const RecommendedRecipes = ({ isLoggedIn, refreshKey }: Props) => {
  const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchRecipes = useCallback(async () => {
    if (!isLoggedIn) return;
    
    setLoading(true);
    try {
      const data = await getRecommendations(12);
      setRecipes(data);
    } catch {
      notifications.show({
        title: 'Error',
        message: 'Failed to fetch recommended recipes.',
        color: 'red'
      });
    } finally {
      setLoading(false);
    }
  }, [isLoggedIn]);

  useEffect(() => {
    fetchRecipes();
  }, [fetchRecipes, refreshKey]);

  if (loading && recipes.length === 0) {
    return (
      <Center py='xl'>
        <Loader color='teal' size='md' />
      </Center>
    );
  }

  if (recipes.length === 0) {
    return (
      <Center py='xl'>
        <Text size='sm' c='dimmed'>No recommended recipes found.</Text>
      </Center>
    );
  }

  return (
    <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing='md' mt='xl'>
      {recipes.map((recipe) => (
        <RecipeCard
          key={recipe.id}
          recipe={recipe}
          isLoggedIn={isLoggedIn}
        />
      ))}
    </SimpleGrid>
  );
};