import { useEffect, useState } from 'react';
import { useSearchParams, useOutletContext } from 'react-router-dom';
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
import { searchRecipes } from '../api/recipes';
import type { RecipeSummary } from '../types/recipe';
import type { UserResponse } from '../types/auth';
import { RecipeCard } from '../components/RecipeCard';


interface OutletContextType {
    user: UserResponse | null;
    isLoggedIn: boolean;
}


export const SearchResults = () => {
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const { isLoggedIn } = useOutletContext<OutletContextType>();
    const [recipes, setRecipes] = useState<RecipeSummary[]>([]);
    const [loading, setLoading] = useState(false);


    useEffect(() => {
        if (!query.trim()) {
            setRecipes([]);
            return;
        }

        setLoading(true);
        searchRecipes(query.trim())
            .then(setRecipes)
            .catch(() => {
                notifications.show({
                    title: 'Error',
                    message: 'Failed to execute search.',
                    color: 'red'
                });
            })
            .finally(() => setLoading(false));
    }, [query]);


    return (
        <Container size='lg'>
            <Paper shadow='2xl' p={36} radius='xl' bg='white'>
                <Title order={2} fw={800} c='teal.9' mb='xs'>
                    Search Results
                </Title>
                <Text c='dimmed' size='sm' mb='lg'>
                    Showing matches for "{query}"
                </Text>

                {loading ? (
                    <Center py='xl'>
                        <Loader color='teal' size='md' />
                    </Center>
                ) : recipes.length === 0 ? (
                    <Center py='xl'>
                        <Text size='sm' c='dimmed'>No recipes found matching your query.</Text>
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