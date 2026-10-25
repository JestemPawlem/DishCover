import { useEffect, useState } from 'react';
import { useParams, useOutletContext } from 'react-router-dom';
import {
  Container,
  Paper,
  Title,
  Text,
  Badge,
  Button,
  Group,
  Divider,
  List,
  SimpleGrid,
  Loader,
  Center,
  Flex,
  Box
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { getRecipe, getSimilarRecipes, toggleLikeRecipe } from '../api/recipes';
import type { Recipe, RecipeSummary } from '../types/recipe';
import type { UserResponse } from '../types/auth';
import { RecipeCard } from '../components/RecipeCard';

interface OutletContextType {
  user: UserResponse | null;
  isLoggedIn: boolean;
}

export const RecipeDetails = () => {
  const { id } = useParams<{ id: string }>();
  const recipeId = Number(id);
  const { isLoggedIn } = useOutletContext<OutletContextType>();

  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [similar, setSimilar] = useState<RecipeSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [likeLoading, setLikeLoading] = useState(false);

  useEffect(() => {
    if (!recipeId) return;

    setLoading(true);
    Promise.all([
      getRecipe(recipeId),
      getSimilarRecipes(recipeId, 4)
    ])
      .then(([recipeData, similarData]) => {
        setRecipe(recipeData);
        setSimilar(similarData);
      })
      .catch(() => {
        notifications.show({
          title: 'Error',
          message: 'Failed to load recipe details.',
          color: 'red'
        });
      })
      .finally(() => setLoading(false));
  }, [recipeId]);

  const handleLike = async () => {
    if (!recipe || !isLoggedIn) return;

    setLikeLoading(true);
    try {
      const res = await toggleLikeRecipe(recipe.id);
      setRecipe({
        ...recipe,
        is_liked: res.liked,
        like_count: (recipe.like_count ?? 0) + (res.liked ? 1 : -1)
      });
    } catch {
      notifications.show({
        title: 'Error',
        message: 'Failed to update favorite status.',
        color: 'red'
      });
    } finally {
      setLikeLoading(false);
    }
  };

  if (loading) {
    return (
      <Center py={100}>
        <Loader color='white' size='xl' type='dots' />
      </Center>
    );
  }

  if (!recipe) {
    return (
      <Container size='lg'>
        <Paper shadow='2xl' p={36} radius='xl' bg='white'>
          <Text ta='center' c='dimmed'>Recipe not found.</Text>
        </Paper>
      </Container>
    );
  }

  return (
    <Container size='lg'>
      <Paper shadow='2xl' p={36} radius='xl' bg='white' mb='xl'>
        <Group justify='space-between' align='flex-start' mb='md'>
          <div style={{ flex: 1 }}>
            <Title order={1} fw={800} c='teal.9'>
              {recipe.name}
            </Title>
            <Group gap='sm' mt='xs'>
              {recipe.minutes && (
                <Badge color='teal' variant='light' size='lg'>
                  ⏱ {recipe.minutes} mins
                </Badge>
              )}
              <Badge color='gray' variant='light' size='lg'>
                ❤️ {recipe.like_count ?? 0} likes
              </Badge>
            </Group>
          </div>

          {isLoggedIn && (
            <Button
              radius='md'
              loading={likeLoading}
              onClick={handleLike}
              variant={recipe.is_liked ? 'filled' : 'light'}
              color={recipe.is_liked ? 'red' : 'gray'}
            >
              {recipe.is_liked ? 'Favorited' : 'Add to favorites'}
            </Button>
          )}
        </Group>

        <Text c='gray.7' size='md' mb='xl'>
          {recipe.description || 'No description provided.'}
        </Text>

        <Divider my='xl' />

        <Flex direction={{ base: 'column', md: 'row' }} gap='xl'>
          <Box style={{ flex: 5 }}>
            <Title order={3} fw={700} c='teal.8' mb='md'>
              Ingredients
            </Title>
            <List spacing='sm' size='sm' center>
              {recipe.ingredients.map((ing, idx) => (
                <List.Item key={idx}>{ing}</List.Item>
              ))}
            </List>
          </Box>

          <Box style={{ flex: 7 }}>
            <Title order={3} fw={700} c='teal.8' mb='md'>
              Preparation Steps
            </Title>
            <List type='ordered' spacing='md' size='sm'>
              {recipe.steps.map((step, idx) => (
                <List.Item key={idx}>
                  <Text size='sm'>{step}</Text>
                </List.Item>
              ))}
            </List>
          </Box>
        </Flex>
      </Paper>

      {similar.length > 0 && (
        <Paper shadow='2xl' p={36} radius='xl' bg='white'>
          <Title order={3} fw={700} c='teal.9' mb='lg'>
            Similar Recipes
          </Title>
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing='md'>
            {similar.map((simRecipe) => (
              <RecipeCard
                key={simRecipe.id}
                recipe={simRecipe}
                isLoggedIn={isLoggedIn}
              />
            ))}
          </SimpleGrid>
        </Paper>
      )}
    </Container>
  );
};