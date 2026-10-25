import { useEffect, useState, useCallback } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import {
    Container,
    Paper,
    Title,
    Text,
    SimpleGrid,
    Loader,
    Center
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { getLikedRecipes } from '../api/recipes';
import type { RecipeSummary } from '../types/recipe';
import type { UserResponse } from '../types/auth';
import { RecipeCard } from '../components/RecipeCard';


interface OutletContextType {
    user: UserResponse | null;
    isLoggedIn: boolean;
}


export const Favorites = () => {
    const { isLoggedIn } = useOutletContext<OutletContextType>();
    const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();


    const fetchFavorites = useCallback(async () => {
        setLoading(true);
        try {
            const data = await getLikedRecipes(50, 0);
            setRecipes(data.map((r) => ({ ...r, is_liked: true })));
        } catch {
            notifications.show({
                title: 'Error',
                message: 'Failed to fetch saved recipes.',
                color: 'red'
            });
        } finally {
            setLoading(false);
        }
    }, []);


    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            navigate('/login');
            return;
        }
        fetchFavorites();
    }, [navigate, fetchFavorites]);


    return (
        <Container size='lg'>
            <Paper shadow='2xl' p={36} radius='xl' bg='white'>
                <Title order={2} fw={800} c='teal.9' mb='xs'>
                    Saved Recipes
                </Title>
                <Text c='dimmed' size='sm' mb='lg'>
                    All your favorited recipes in one place
                </Text>

                {loading ? (
                    <Center py='xl'>
                        <Loader color='teal' size='md' />
                    </Center>
                ) : recipes.length === 0 ? (
                    <Center py='xl'>
                        <Text size='sm' c='dimmed'>You haven't saved any recipes yet.</Text>
                    </Center>
                ) : (
                    <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing='md'>
                        {recipes.map((recipe) => (
                            <RecipeCard
                                key={recipe.id}
                                recipe={recipe}
                                isLoggedIn={isLoggedIn}
                                onLikeToggled={fetchFavorites}
                            />
                        ))}
                    </SimpleGrid>
                )}
            </Paper>
        </Container>
    );
};