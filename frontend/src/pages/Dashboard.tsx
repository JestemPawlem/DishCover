import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../api/auth';
import { getRecommendations } from '../api/recipes';
import type { UserResponse } from '../types/user';
import type { RecipeRecommendation } from '../types/recipe';
import { RecipeCard } from '../components/RecipeCard';

import {
  Box,
  Container,
  Paper,
  Title,
  Text,
  Button,
  Stack,
  Group,
  Divider,
  Badge,
  SimpleGrid,
  Loader,
  Center
} from '@mantine/core';
import { notifications } from '@mantine/notifications';


export const Dashboard = () => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [recipes, setRecipes] = useState<RecipeRecommendation[]>([]);
  const [loadingRecipes, setLoadingRecipes] = useState(false);
  const navigate = useNavigate();

  const fetchRecommendations = useCallback(async () => {
    setLoadingRecipes(true);
    try {
      const data = await getRecommendations(8);
      setRecipes(data);
    } catch {
      notifications.show({
        title: 'Error',
        message: 'Failed to fetch recipe recommendations.',
        color: 'red'
      });
    } finally {
      setLoadingRecipes(false);
    }
  }, []);

  useEffect(() => {
    getCurrentUser()
      .then((data) => {
        setUser(data);
        fetchRecommendations();
      })
      .catch(() => {
        localStorage.removeItem('token');
        navigate('/login');
      });
  }, [navigate, fetchRecommendations]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (!user) {
    return (
      <Box bg='teal.7' mih='100vh'>
        <Center h='100vh'>
          <Loader color='white' size='xl' type='dots' />
        </Center>
      </Box>
    );
  }

  return (
    <Box bg='teal.7' mih='100vh' py='xl' px='md'>
      <Container size='xl'>
        <Paper shadow='2xl' p={36} radius='xl' bg='white'>
          <Group justify='space-between' align='center' mb='lg'>
            <div>
              <Title order={2} fw={800} c='teal.9'>
                User Dashboard
              </Title>
            </div>
            <Button
              variant='light'
              color='red'
              radius='md'
              onClick={handleLogout}
            >
              Sign out
            </Button>
          </Group>


          <Divider my='md' />


          <Stack gap='xs' mb='xl'>
            <Group justify='space-between'>
              <Text fw={600} size='sm'>Email:</Text>
              <Text size='sm'>{user.email}</Text>
            </Group>

            <Group justify='space-between'>
              <Text fw={600} size='sm'>User ID:</Text>
              <Badge color='gray' variant='light'>{user.id}</Badge>
            </Group>

            <Group justify='space-between'>
              <Text fw={600} size='sm'>Member since:</Text>
              <Text size='sm'>{new Date(user.created_at).toLocaleDateString()}</Text>
            </Group>
          </Stack>


          <Group justify='space-between' align='center' mb='md'>
            <div>
              <Title order={3} fw={700} c='teal.9'>
                Recommended Recipes
              </Title>
            </div>

            <Button
              variant='subtle'
              color='teal'
              radius='md'
              size='xs'
              loading={loadingRecipes}
              onClick={fetchRecommendations}
            >
              Refresh
            </Button>
          </Group>


          {loadingRecipes && recipes.length === 0 ? (
            <Center py='xl'>
              <Loader color='teal' size='md' />
            </Center>
          ) : recipes.length === 0 ? (
            <Center py='xl'>
              <Text size='sm' c='dimmed'>No recipe recommendations found.</Text>
            </Center>
          ) : (
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing='md'>
              {recipes.map((recipe) => (
                <RecipeCard
                  key={recipe.id}
                  recipe={recipe}
                  onLikeToggled={fetchRecommendations}
                />
              ))}
            </SimpleGrid>
          )}
        </Paper>
      </Container>
    </Box>
  );
};