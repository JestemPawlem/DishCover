import { useState } from 'react';
import {
    Card,
    Text,
    Badge,
    Button,
    Group,
    Stack,
    Flex
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import type { RecipeRecommendation } from '../types/recipe';
import { toggleLikeRecipe } from '../api/recipes';


interface Props {
    recipe: RecipeRecommendation;
    onLikeToggled? : () => void;
}


export const RecipeCard = ({ recipe, onLikeToggled }: Props) => {
    const [liked, setLiked] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleLike = async () => {
        if (loading) {
            return;
        }

        const previousState = liked;
        setLiked(!previousState);
        setLoading(true);
        try {
            const result = await toggleLikeRecipe(recipe.id);
            setLiked(result.liked);
            onLikeToggled?.();
        } catch (err) {
            notifications.show({
                title: 'Error',
                message: 'Failed to update favorite status. Please try again.',
                color: 'red'
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card
            withBorder
            shadow='sm'
            radius='lg'
            p='lg'
            bg='teal.1'
            h='100%'
        >
            <Flex direction='column' justify='space-between' h='100%'>
                <Stack gap='xs' mb='md'>
                    <Flex justify='space-between' align='flex-start' gap='xs'>
                        <Text fw={700} size='md' c='teal.9' lineClamp={2} flex={1}>
                            {recipe.name}
                        </Text>
                        {recipe.similarity !== null && (
                            <Badge
                                color='teal'
                                variant='light'
                                size='md'
                                flex='0 0 auto'
                            >
                                {(recipe.similarity * 100).toFixed(1)}% match
                            </Badge>
                        )}
                    </Flex>

                    <Flex align='center' gap='sm'>
                        {recipe.minutes && (
                            <Text size='xs' c='dimmed'>
                                Prep time: {recipe.minutes} mins
                            </Text>
                        )}
                        {recipe.minutes && recipe.like_count !== undefined && (
                            <Text size='xs' c='dimmed'>•</Text>
                        )}
                        {recipe.like_count !== undefined && (
                            <Text size='xs' c='dimmed'>
                                ❤️ {recipe.like_count} {recipe.like_count === 1 ? 'like' : 'likes'}
                            </Text>
                        )}
                    </Flex>

                    <Text size='sm' c='gray.7' lineClamp={4}>
                        {recipe.description || 'No description provided.'}
                    </Text>
                </Stack>

                <Button
                    fullWidth
                    radius='md'
                    loading={loading}
                    onClick={handleLike}
                    variant={liked ? 'filled' : 'light'}
                    color={liked ? 'red' : 'gray'}
                >
                    {liked ? 'Favorited' : 'Add to favorites'}
                </Button>
            </Flex>
        </Card>
    );
}