import { useEffect, useState, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
    Container,
    Paper,
    Title,
    Text,
    Button,
    Group,
    SimpleGrid,
    Loader,
    Center
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { getRecommendations, getOnboardingRecipes } from '../api/recipes';
import type { RecipeSummary } from '../types/recipe';
import type { UserResponse } from '../types/auth';
import { RecipeCard } from '../components/RecipeCard';


interface OutletContextType {
    user: UserResponse | null;
    isLoggedIn: boolean;
}


export const Dashboard = () => {
    const { user, isLoggedIn } = useOutletContext<OutletContextType>();
    const [recipes, setRecipes] = useState<(RecipeSummary)[]>([]);
    const [loading, setLoading] = useState(false);


    const fetchRecipes = useCallback(async () => {
        setLoading(true);
        try {
            if (isLoggedIn) {
                const data = await getRecommendations(12);
                setRecipes(data);
            } else {
                const data = await getOnboardingRecipes(12);
                setRecipes(data);
            }
        } catch {
            notifications.show({
                title: 'Error',
                message: 'Failed to fetch recipes.',
                color: 'red'
            });
        } finally {
            setLoading(false);
        }
    }, [isLoggedIn]);


    useEffect(() => {
        fetchRecipes();
    }, [fetchRecipes]);


    return (
        <Container size='lg'>
            <Paper shadow='2xl' p={36} radius='xl' bg='white'>
                <Group justify='space-between' align='center' mb='lg'>
                    <div>
                        <Title order={2} fw={800} c='teal.9'>
                            {isLoggedIn ? 'Recommended For You' : 'Trending Recipes'}
                        </Title>
                        <Text c='dimmed' size='sm'>
                            {isLoggedIn
                                ? 'Recipes dynamically personalized using your interactions'
                                : 'Explore the most popular dishes across our community'}
                        </Text>
                    </div>

                    {isLoggedIn && (
                        <Button
                            variant='subtle'
                            color='teal'
                            radius='md'
                            size='xs'
                            loading={loading}
                            onClick={fetchRecipes}
                        >
                            Refresh
                        </Button>
                    )}
                </Group>

                {loading && recipes.length === 0 ? (
                    <Center py='xl'>
                        <Loader color='teal' size='md' />
                    </Center>
                ) : recipes.length === 0 ? (
                    <Center py='xl'>
                        <Text size='sm' c='dimmed'>No recipes found.</Text>
                    </Center>
                ) : (
                    <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing='md'>
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                                isLoggedIn={isLoggedIn}
                            />
                        ))}
                    </SimpleGrid>
                )}
            </Paper>
        </Container>
    );
};